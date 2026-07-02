/* Modul Kategori */
const ICON_LIST = [
    'bi-box','bi-box-seam','bi-archive','bi-bag','bi-basket','bi-cart','bi-tag','bi-tags',
    'bi-laptop','bi-phone','bi-tablet','bi-smartwatch','bi-tv','bi-camera','bi-headphones',
    'bi-printer','bi-keyboard','bi-mouse','bi-cpu','bi-memory','bi-hdd','bi-usb-symbol',
    'bi-tools','bi-wrench','bi-hammer','bi-screwdriver','bi-nut','bi-gear','bi-gear-fill',
    'bi-house','bi-door-open','bi-lightbulb','bi-lamp','bi-bulb','bi-fan','bi-thermometer',
    'bi-droplet','bi-cup-straw','bi-cup-hot','bi-egg-fried','bi-cup','bi-mug',
    'bi-book','bi-journal','bi-pencil','bi-pen','bi-marker','bi-eraser','bi-file-earmark',
    'bi-folder','bi-folder2','bi-archive-fill','bi-clipboard','bi-clipboard-data',
    'bi-truck','bi-car-front','bi-bus-front','bi-bicycle','bi-airplane','bi-train-front',
    'bi-heart-pulse','bi-bandaid','bi-capsule','bi-prescription2','bi-clipboard2-pulse',
    'bi-tree','bi-flower1','bi-flower2','bi-flower3','bi-leaf','bi-grid','bi-grid-3x3',
    'bi-gem','bi-diamond','bi-stars','bi-trophy','bi-award','bi-gift','bi-balloon',
    'bi-music-note','bi-controller','bi-dice-5','bi-puzzle','bi-palette','bi-brush',
    'bi-camera2','bi-image','bi-images','bi-film','bi-camera-reels','bi-vr',
    'bi-shield','bi-shield-lock','bi-shield-check','bi-lock','bi-unlock','bi-key',
    'bi-person','bi-people','bi-person-badge','bi-person-circle','bi-people-fill',
    'bi-globe','bi-geo-alt','bi-map','bi-compass','bi-binoculars','bi-search',
];

const KategoriModule = {
    icons: ICON_LIST,
    current: null,

    async init() {
        if (!APP.isAdmin) {
            document.getElementById('btnTambah')?.remove();
        }
        this.buildIconPicker();
        await this.loadTable();
        document.getElementById('btnTambah')?.addEventListener('click', () => this.openForm());
        document.getElementById('formKategori').addEventListener('submit', (e) => this.submit(e));
    },

    buildIconPicker() {
        const wrap = document.getElementById('iconPicker');
        wrap.innerHTML = this.icons.map(i =>
            `<div class="icon-picker-item" data-icon="${i}"><i class="bi ${i}"></i></div>`
        ).join('');
        wrap.addEventListener('click', (e) => {
            const item = e.target.closest('.icon-picker-item');
            if (!item) return;
            wrap.querySelectorAll('.icon-picker-item').forEach(x => x.classList.remove('active'));
            item.classList.add('active');
            document.getElementById('fieldIcon').value = item.dataset.icon;
        });
    },

    selectIcon(name) {
        const wrap = document.getElementById('iconPicker');
        wrap.querySelectorAll('.icon-picker-item').forEach(x => {
            x.classList.toggle('active', x.dataset.icon === name);
        });
        if (name) document.getElementById('fieldIcon').value = name;
    },

    async loadTable() {
        try {
            const data = await api.get('/api/kategori/');
            this.renderTable(data.data || []);
        } catch (err) {
            toast('Gagal memuat data', err.message, 'danger');
        }
    },

    renderTable(items) {
        const canEdit = APP.isAdmin;
        const html = `
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th width="50">#</th>
                        <th width="60">Icon</th>
                        <th>Nama Kategori</th>
                        ${canEdit ? '<th width="140" class="text-end">Aksi</th>' : ''}
                    </tr>
                </thead>
                <tbody>
                    ${items.map((it, i) => `
                        <tr>
                            <td>${i + 1}</td>
                            <td><span class="icon-cell"><i class="bi ${it.icon_kategori || 'bi-box'}"></i></span></td>
                            <td><strong>${escapeHtml(it.nama_kategori)}</strong></td>
                            ${canEdit ? `
                            <td class="text-end">
                                <button class="btn btn-sm btn-light" onclick="KategoriModule.edit('${it.id}')" title="Edit"><i class="bi bi-pencil"></i></button>
                                <button class="btn btn-sm btn-light text-danger" onclick="KategoriModule.destroy('${it.id}','${escapeHtml(it.nama_kategori)}')" title="Hapus"><i class="bi bi-trash"></i></button>
                            </td>` : ''}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            ${items.length === 0 ? `<div class="text-center text-secondary py-4">Belum ada data.</div>` : ''}
        `;
        document.getElementById('kategoriTable_wrapper').innerHTML = html;
    },

    openForm() {
        this.current = null;
        document.getElementById('formTitle').textContent = 'Tambah Kategori';
        document.getElementById('fieldId').value = '';
        document.getElementById('fieldNama').value = '';
        document.getElementById('fieldIcon').value = 'bi-box';
        this.selectIcon('bi-box');
        new bootstrap.Modal(document.getElementById('formModal')).show();
    },

    async edit(id) {
        try {
            const data = await api.get(`/api/kategori/${id}`);
            this.current = data;
            document.getElementById('formTitle').textContent = 'Edit Kategori';
            document.getElementById('fieldId').value = data.id;
            document.getElementById('fieldNama').value = data.nama_kategori;
            document.getElementById('fieldIcon').value = data.icon_kategori || 'bi-box';
            this.selectIcon(data.icon_kategori || 'bi-box');
            new bootstrap.Modal(document.getElementById('formModal')).show();
        } catch (err) {
            toast('Gagal memuat data', err.message, 'danger');
        }
    },

    async submit(e) {
        e.preventDefault();
        const id = document.getElementById('fieldId').value;
        const body = {
            nama_kategori: document.getElementById('fieldNama').value.trim(),
            icon_kategori: document.getElementById('fieldIcon').value || 'bi-box',
        };
        if (!body.nama_kategori) { toast('Validasi', 'Nama kategori wajib diisi', 'warning'); return; }
        try {
            if (id) {
                await api.put(`/api/kategori/${id}`, body);
                toast('Berhasil', 'Kategori diperbarui', 'success');
            } else {
                await api.post('/api/kategori/', body);
                toast('Berhasil', 'Kategori ditambahkan', 'success');
            }
            bootstrap.Modal.getInstance(document.getElementById('formModal')).hide();
            await this.loadTable();
        } catch (err) {
            toast('Gagal menyimpan', err.message, 'danger');
        }
    },

    async destroy(id, nama) {
        if (!await confirmDialog({ message: `Hapus kategori "${nama}"?`, confirmText: 'Hapus' })) return;
        try {
            await api.delete(`/api/kategori/${id}`);
            toast('Berhasil', 'Kategori dihapus', 'success');
            await this.loadTable();
        } catch (err) {
            toast('Gagal menghapus', err.message, 'danger');
        }
    },
};

document.addEventListener('DOMContentLoaded', () => KategoriModule.init());
