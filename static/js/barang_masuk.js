const BarangMasukModule = {
    dataTable: null,

    async init() {
        await this.loadSuplier();
        await this.loadTable();
        this.bindEvents();
    },

    async loadSuplier() {
        try {
            const res = await api.get('/api/suplier/');
            const sel = document.getElementById('filterSuplier');
            (res.data || []).forEach(s => {
                sel.insertAdjacentHTML('beforeend', `<option value="${s.id}">${escapeHtml(s.nama)}</option>`);
            });
            initSelect2('#filterSuplier');
        } catch {}
    },

    bindEvents() {
        document.getElementById('btnFilter').addEventListener('click', () => this.loadTable());
        document.getElementById('btnExportPdf').addEventListener('click', () => this.exportPdf());
    },

    exportPdf() {
        const params = new URLSearchParams();
        const t1 = document.getElementById('filterTglAwal').value;
        const t2 = document.getElementById('filterTglAkhir').value;
        const s = document.getElementById('filterSuplier').value;
        if (t1) params.set('tanggal_awal', t1);
        if (t2) params.set('tanggal_akhir', t2);
        if (s) params.set('suplier_id', s);
        window.open(`/api/laporan/barang-masuk/print?${params}`, '_blank');
    },

    async loadTable() {
        const params = new URLSearchParams();
        const t1 = document.getElementById('filterTglAwal').value;
        const t2 = document.getElementById('filterTglAkhir').value;
        const s = document.getElementById('filterSuplier').value;
        if (t1) params.set('tanggal_awal', t1);
        if (t2) params.set('tanggal_akhir', t2);
        if (s) params.set('suplier_id', s);
        try {
            const res = await api.get(`/api/barang-masuk/?${params}`);
            this.renderTable(res.data || []);
        } catch (err) { toast('Gagal', err.message, 'danger'); }
    },

    renderTable(items) {
        const canEdit = APP.isAdmin || APP.user.role === 'staff';
        const html = `
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th width="50">#</th>
                        <th>Tanggal</th>
                        <th>No. Transaksi</th>
                        <th>Suplier</th>
                        <th class="text-end">Item</th>
                        <th class="text-end">Total Jumlah</th>
                        <th>Dokumen</th>
                        <th width="180" class="text-end">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    ${items.map((it, i) => `
                        <tr>
                            <td>${i + 1}</td>
                            <td>${formatDate(it.tanggal_masuk)}</td>
                            <td class="mono">${escapeHtml(it.no_transaksi || '-')}</td>
                            <td>${escapeHtml(it.nama_suplier || '-')}</td>
                            <td class="text-end">${it.item_count || 0}</td>
                            <td class="text-end">${formatNumber(it.total_jumlah || 0)}</td>
                            <td>${escapeHtml(it.nomor_dokumen || '-')}</td>
                            <td class="text-end">
                                <a href="/barang-masuk/${it.id}" class="btn btn-sm btn-light" title="Detail"><i class="bi bi-eye"></i></a>
                                <a href="/api/transaksi/barang-masuk/${it.id}/print" target="_blank" class="btn btn-sm btn-light" title="Cetak"><i class="bi bi-printer"></i></a>
                                ${canEdit ? `
                                <a href="/barang-masuk/${it.id}/edit" class="btn btn-sm btn-light" title="Edit"><i class="bi bi-pencil"></i></a>
                                <button class="btn btn-sm btn-light text-danger" onclick="BarangMasukModule.destroy('${it.id}')" title="Hapus"><i class="bi bi-trash"></i></button>
                                ` : ''}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            ${items.length === 0 ? `<div class="text-center text-secondary py-4">Belum ada transaksi.</div>` : ''}
        `;
        document.getElementById('tableWrapper').innerHTML = html;
        if (this.dataTable) { this.dataTable.destroy(); this.dataTable = null; }
        const t = document.querySelector('#tableWrapper table');
        if (t) this.dataTable = jQuery(t).DataTable({
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/id.json',
                emptyTable: 'Belum ada transaksi.',
            },
            pageLength: 25, order: [[1, 'desc']],
        });
    },

    async destroy(id) {
        if (!await confirmDialog({ message: 'Hapus transaksi ini? Stok barang akan dikurangi kembali.', confirmText: 'Hapus' })) return;
        try {
            await api.delete(`/api/barang-masuk/${id}`);
            toast('Berhasil', 'Transaksi dihapus', 'success');
            await this.loadTable();
        } catch (err) { toast('Gagal', err.message, 'danger'); }
    },
};

document.addEventListener('DOMContentLoaded', () => BarangMasukModule.init());
