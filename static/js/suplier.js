const SuplierModule = {
    async init() {
        await this.loadTable();
        document.getElementById('btnTambah')?.addEventListener('click', () => this.openForm());
        document.getElementById('formSuplier').addEventListener('submit', (e) => this.submit(e));
    },

    async loadTable() {
        try {
            const data = await api.get('/api/suplier/');
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
                        <th>Nama</th>
                        <th>Kontak</th>
                        <th>Perusahaan</th>
                        <th>Alamat</th>
                        ${canEdit ? '<th width="140" class="text-end">Aksi</th>' : ''}
                    </tr>
                </thead>
                <tbody>
                    ${items.map((it, i) => `
                        <tr>
                            <td>${i + 1}</td>
                            <td><strong>${escapeHtml(it.nama)}</strong></td>
                            <td>
                                ${it.no_hp ? `<div><i class="bi bi-telephone"></i> ${escapeHtml(it.no_hp)}</div>` : ''}
                                ${it.email ? `<div class="small text-secondary"><i class="bi bi-envelope"></i> ${escapeHtml(it.email)}</div>` : ''}
                            </td>
                            <td>${escapeHtml(it.perusahaan || '-')}</td>
                            <td>${escapeHtml(it.alamat || '-')}</td>
                            ${canEdit ? `
                            <td class="text-end">
                                <button class="btn btn-sm btn-light" onclick="SuplierModule.edit('${it.id}')" title="Edit"><i class="bi bi-pencil"></i></button>
                                <button class="btn btn-sm btn-light text-danger" onclick="SuplierModule.destroy('${it.id}','${escapeHtml(it.nama)}')" title="Hapus"><i class="bi bi-trash"></i></button>
                            </td>` : ''}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            ${items.length === 0 ? `<div class="text-center text-secondary py-4">Belum ada data.</div>` : ''}
        `;
        document.getElementById('suplierTable_wrapper').innerHTML = html;
    },

    openForm() {
        document.getElementById('formTitle').textContent = 'Tambah Suplier';
        document.getElementById('fieldId').value = '';
        ['Nama', 'Perusahaan', 'NoHp', 'Email', 'Alamat'].forEach(f => {
            document.getElementById('field' + f).value = '';
        });
        new bootstrap.Modal(document.getElementById('formModal')).show();
    },

    async edit(id) {
        try {
            const data = await api.get(`/api/suplier/${id}`);
            document.getElementById('formTitle').textContent = 'Edit Suplier';
            document.getElementById('fieldId').value = data.id;
            document.getElementById('fieldNama').value = data.nama || '';
            document.getElementById('fieldPerusahaan').value = data.perusahaan || '';
            document.getElementById('fieldNoHp').value = data.no_hp || '';
            document.getElementById('fieldEmail').value = data.email || '';
            document.getElementById('fieldAlamat').value = data.alamat || '';
            new bootstrap.Modal(document.getElementById('formModal')).show();
        } catch (err) {
            toast('Gagal memuat data', err.message, 'danger');
        }
    },

    async submit(e) {
        e.preventDefault();
        const id = document.getElementById('fieldId').value;
        const body = {
            nama: document.getElementById('fieldNama').value.trim(),
            perusahaan: document.getElementById('fieldPerusahaan').value.trim(),
            no_hp: document.getElementById('fieldNoHp').value.trim(),
            email: document.getElementById('fieldEmail').value.trim(),
            alamat: document.getElementById('fieldAlamat').value.trim(),
        };
        if (!body.nama) { toast('Validasi', 'Nama wajib diisi', 'warning'); return; }
        try {
            if (id) await api.put(`/api/suplier/${id}`, body);
                else await api.post('/api/suplier/', body);
            toast('Berhasil', 'Data suplier disimpan', 'success');
            bootstrap.Modal.getInstance(document.getElementById('formModal')).hide();
            await this.loadTable();
        } catch (err) {
            toast('Gagal menyimpan', err.message, 'danger');
        }
    },

    async destroy(id, nama) {
        if (!await confirmDialog({ message: `Hapus suplier "${nama}"?`, confirmText: 'Hapus' })) return;
        try {
            await api.delete(`/api/suplier/${id}`);
            toast('Berhasil', 'Suplier dihapus', 'success');
            await this.loadTable();
        } catch (err) {
            toast('Gagal menghapus', err.message, 'danger');
        }
    },
};

document.addEventListener('DOMContentLoaded', () => SuplierModule.init());
