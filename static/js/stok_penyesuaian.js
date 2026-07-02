const StokPenyesuaianModule = {
    dataTable: null,

    async init() {
        await this.loadTable();
    },

    async loadTable() {
        try {
            const res = await api.get('/api/stok-penyesuaian/');
            this.renderTable(res.data || []);
        } catch (err) { toast('Gagal', err.message, 'danger'); }
    },

    renderTable(items) {
        const html = `
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th width="50">#</th>
                        <th>Tanggal</th>
                        <th>No. Penyesuaian</th>
                        <th>Barang</th>
                        <th class="text-end">Stok Sistem</th>
                        <th class="text-end">Stok Fisik</th>
                        <th class="text-end">Selisih</th>
                        <th>Alasan</th>
                        <th>Status</th>
                        <th width="160" class="text-end">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    ${items.map((it, i) => {
                        const selisih = parseInt(it.selisih || 0);
                        const selisihBadge = selisih > 0 ? `<span class="text-success">+${formatNumber(selisih)}</span>`
                            : selisih < 0 ? `<span class="text-danger">${formatNumber(selisih)}</span>`
                            : '<span class="text-secondary">0</span>';
                        const statusBadge = it.status === 'dibatalkan'
                            ? '<span class="badge badge-status-batal">Dibatalkan</span>'
                            : '<span class="badge badge-status-aktif">Aktif</span>';
                        return `
                        <tr>
                            <td>${i + 1}</td>
                            <td>${formatDate(it.tanggal_penyesuaian)}</td>
                            <td class="mono">${escapeHtml(it.no_penyesuaian || '-')}</td>
                            <td><strong>${escapeHtml(it.nama_barang || '-')}</strong><br><small class="text-secondary mono">${escapeHtml(it.kode_barang || '')}</small></td>
                            <td class="text-end">${formatNumber(it.stok_sistem)}</td>
                            <td class="text-end">${formatNumber(it.stok_fisik)}</td>
                            <td class="text-end">${selisihBadge}</td>
                            <td>${escapeHtml(it.alasan || '-')}</td>
                            <td>${statusBadge}</td>
                            <td class="text-end">
                                <a href="/stok-penyesuaian/${it.id}" class="btn btn-sm btn-light" title="Detail"><i class="bi bi-eye"></i></a>
                                ${(APP.isAdmin || APP.user.role === 'staff') && it.status === 'aktif' ? `
                                <button class="btn btn-sm btn-light text-danger" onclick="StokPenyesuaianModule.batal('${it.id}')" title="Batalkan"><i class="bi bi-x-circle"></i></button>
                                ` : ''}
                            </td>
                        </tr>`;
                    }).join('')}
                </tbody>
            </table>
            ${items.length === 0 ? `<div class="text-center text-secondary py-4">Belum ada data.</div>` : ''}
        `;
        document.getElementById('tableWrapper').innerHTML = html;
        if (this.dataTable) { this.dataTable.destroy(); this.dataTable = null; }
        const t = document.querySelector('#tableWrapper table');
        if (t) this.dataTable = jQuery(t).DataTable({
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/id.json',
                emptyTable: 'Belum ada data.',
            },
            pageLength: 25, order: [[1, 'desc']],
        });
    },

    async batal(id) {
        const { value: catatan } = await new Promise((resolve) => {
            showModal({
                title: 'Batalkan Penyesuaian',
                body: `<p>Stok barang akan dikembalikan ke posisi semula.</p>
                       <div class="mb-2"><label class="form-label">Catatan pembatalan</label>
                       <textarea class="form-control" id="batalCatatan" rows="2" placeholder="Alasan pembatalan..."></textarea></div>`,
                footer: `<button type="button" class="btn btn-light" data-bs-dismiss="modal">Batal</button>
                         <button type="button" class="btn btn-danger" id="btnKonfirmBatal">Batalkan Penyesuaian</button>`,
                onShown: () => {
                    document.getElementById('btnKonfirmBatal').addEventListener('click', () => {
                        const v = document.getElementById('batalCatatan').value;
                        bootstrap.Modal.getInstance(document.getElementById('modalContainer').lastChild).hide();
                        resolve({ value: v });
                    });
                },
            });
        });
        try {
            await api.post(`/api/stok-penyesuaian/${id}/batal`, { catatan_pembatalan: catatan });
            toast('Berhasil', 'Penyesuaian dibatalkan', 'success');
            await this.loadTable();
        } catch (err) { toast('Gagal', err.message, 'danger'); }
    },
};

document.addEventListener('DOMContentLoaded', () => StokPenyesuaianModule.init());
