const BarangModule = {
    kategoriMap: {},
    dataTable: null,
    filters: { keyword: '', kategori_id: '', stok: '' },

    async init() {
        await this.loadKategori();
        this.bindEvents();
        await this.loadTable();

        // initial filter from URL
        const params = new URLSearchParams(window.location.search);
        if (params.get('stok')) {
            this.filters.stok = params.get('stok');
            document.getElementById('filterStok').value = this.filters.stok;
        }
        if (this.filters.stok) await this.loadTable();
    },

    async loadKategori() {
        try {
            const res = await api.get('/api/kategori/');
            const sel = document.getElementById('filterKategori');
            (res.data || []).forEach(k => {
                this.kategoriMap[k.id] = k;
                sel.insertAdjacentHTML('beforeend', `<option value="${k.id}">${escapeHtml(k.nama_kategori)}</option>`);
            });
            initSelect2('#filterKategori');
        } catch {}
    },

    bindEvents() {
        const apply = debounce(() => this.loadTable(), 300);
        document.getElementById('filterKeyword').addEventListener('input', (e) => { this.filters.keyword = e.target.value; apply(); });
        jQuery('#filterKategori').on('change', (e) => { this.filters.kategori_id = e.target.value; this.loadTable(); });
        document.getElementById('filterStok').addEventListener('change', (e) => { this.filters.stok = e.target.value; this.loadTable(); });
        document.getElementById('btnReset').addEventListener('click', () => {
            this.filters = { keyword: '', kategori_id: '', stok: '' };
            document.getElementById('filterKeyword').value = '';
            jQuery('#filterKategori').val('').trigger('change');
            document.getElementById('filterStok').value = '';
            this.loadTable();
        });
    },

    async loadTable() {
        try {
            const params = new URLSearchParams();
            if (this.filters.keyword) params.set('keyword', this.filters.keyword);
            if (this.filters.kategori_id) params.set('kategori_id', this.filters.kategori_id);
            if (this.filters.stok) params.set('stok', this.filters.stok);
            const res = await api.get(`/api/barang/?${params}`);
            this.renderTable(res.data || []);
        } catch (err) {
            toast('Gagal memuat data', err.message, 'danger');
        }
    },

    renderTable(items) {
        const canEdit = APP.isAdmin;
        const html = `
            <table class="table table-hover align-middle" id="tblBarang">
                <thead>
                    <tr>
                        <th width="50">Foto</th>
                        <th>Kode</th>
                        <th>Nama</th>
                        <th>Kategori</th>
                        <th class="text-end">Stok</th>
                        <th class="text-end">Min.</th>
                        <th>Lokasi</th>
                        <th>Status</th>
                        ${canEdit ? '<th width="200" class="text-end">Aksi</th>' : '<th width="120" class="text-end">Aksi</th>'}
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        `;
        document.getElementById('barangTable_wrapper').innerHTML = html;
        if (this.dataTable) { this.dataTable.destroy(); this.dataTable = null; }
        const table = document.getElementById('tblBarang');
        if (!table) return;
        this.dataTable = jQuery(table).DataTable({
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/id.json',
                emptyTable: 'Belum ada data barang.',
                zeroRecords: 'Tidak ada data yang cocok dengan pencarian.',
            },
            pageLength: 25,
            lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "Semua"]],
            order: [[1, 'asc']],
            columnDefs: [{ orderable: false, targets: [0, -1] }],
            data: items,
            columns: [
                {
                    data: 'foto',
                    render: (d) => d && d.url
                        ? `<img src="${escapeHtml(d.url)}" class="thumb-sm" alt="">`
                        : `<span class="icon-cell"><i class="bi bi-box"></i></span>`,
                },
                {
                    data: 'kode_barang',
                    render: (d) => `<span class="mono">${escapeHtml(d || '')}</span>`,
                },
                {
                    data: 'nama_barang',
                    render: (d) => `<strong>${escapeHtml(d || '')}</strong>`,
                },
                {
                    data: 'nama_kategori',
                    render: (d, t, row) => d
                        ? `<i class="bi ${row.icon_kategori || 'bi-tag'}"></i> ${escapeHtml(d)}`
                        : '-',
                },
                {
                    data: 'stok',
                    className: 'text-end',
                    render: (d, t, row) => `${formatNumber(d || 0)} ${escapeHtml(row.satuan || '')}`,
                },
                {
                    data: 'stok_minimum',
                    className: 'text-end',
                    render: (d) => formatNumber(d || 0),
                },
                {
                    data: 'lokasi_barang',
                    render: (d) => escapeHtml(d || '-'),
                },
                {
                    data: null,
                    render: (d) => {
                        const stok = parseInt(d.stok || 0);
                        const min = parseInt(d.stok_minimum || 0);
                        if (stok === 0) return '<span class="badge badge-status-habis">Habis</span>';
                        if (stok <= min) return '<span class="badge badge-status-hampir">Hampir Habis</span>';
                        return '<span class="badge badge-status-tersedia">Tersedia</span>';
                    },
                },
                {
                    data: null,
                    className: 'text-end',
                    render: (d) => {
                        const aksi = `
                            <a href="/barang/${d.id}" class="btn btn-sm btn-light" title="Detail"><i class="bi bi-eye"></i></a>
                            <a href="/api/barcode/barang/${d.id}/qrcode" target="_blank" class="btn btn-sm btn-light" title="QR Code"><i class="bi bi-qr-code"></i></a>
                            <a href="/api/barcode/barang/${d.id}/barcode" target="_blank" class="btn btn-sm btn-light" title="Barcode"><i class="bi bi-upc"></i></a>
                        `;
                        return aksi + (canEdit ? `
                            <a href="/barang/${d.id}/edit" class="btn btn-sm btn-light" title="Edit"><i class="bi bi-pencil"></i></a>
                            <button class="btn btn-sm btn-light text-danger" onclick="BarangModule.destroy('${d.id}','${escapeHtml(d.nama_barang || '')}')" title="Hapus"><i class="bi bi-trash"></i></button>
                        ` : '');
                    },
                },
            ],
        });
    },

    async destroy(id, nama) {
        if (!await confirmDialog({ message: `Hapus barang "${nama}"?`, confirmText: 'Hapus' })) return;
        try {
            await api.delete(`/api/barang/${id}`);
            toast('Berhasil', 'Barang dihapus', 'success');
            await this.loadTable();
        } catch (err) {
            toast('Gagal menghapus', err.message, 'danger');
        }
    },
};

document.addEventListener('DOMContentLoaded', () => BarangModule.init());
