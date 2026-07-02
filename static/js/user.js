const UserModule = {
    async init() {
        await this.loadTable();
        document.getElementById('btnTambah')?.addEventListener('click', () => this.openForm());
        document.getElementById('formUser').addEventListener('submit', (e) => this.submit(e));
    },

    async loadTable() {
        try {
            const res = await api.get('/api/user/');
            this.renderTable(res.data || []);
        } catch (err) { toast('Gagal', err.message, 'danger'); }
    },

    renderTable(items) {
        const html = `
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th width="50">#</th>
                        <th width="60">Foto</th>
                        <th>Nama</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th width="200" class="text-end">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    ${items.map((u, i) => {
                        const initial = (u.name || u.email || '?')[0].toUpperCase();
                        const foto = u.photo && u.photo.url
                            ? `<img src="${u.photo.url}" class="avatar" style="object-fit:cover" alt="">`
                            : `<div class="avatar">${initial}</div>`;
                        const roleBadge = u.role === 'admin'
                            ? '<span class="badge badge-role-admin">Administrator</span>'
                            : '<span class="badge badge-role-staff">Staff</span>';
                        const statusBadge = u.is_active
                            ? '<span class="badge badge-status-tersedia">Aktif</span>'
                            : '<span class="badge badge-status-batal">Non-aktif</span>';
                        return `
                        <tr>
                            <td>${i + 1}</td>
                            <td>${foto}</td>
                            <td><strong>${escapeHtml(u.name)}</strong></td>
                            <td>${escapeHtml(u.email)}</td>
                            <td>${roleBadge}</td>
                            <td>${statusBadge}</td>
                            <td class="text-end">
                                <button class="btn btn-sm btn-light" onclick="UserModule.edit('${u.id}')" title="Edit"><i class="bi bi-pencil"></i></button>
                                <button class="btn btn-sm btn-light text-danger" onclick="UserModule.toggleActive('${u.id}', ${!u.is_active})" title="${u.is_active ? 'Nonaktifkan' : 'Aktifkan'}"><i class="bi bi-${u.is_active ? 'pause' : 'play'}-fill"></i></button>
                                <button class="btn btn-sm btn-light text-danger" onclick="UserModule.destroy('${u.id}','${escapeHtml(u.name)}')" title="Hapus"><i class="bi bi-trash"></i></button>
                            </td>
                        </tr>`;
                    }).join('')}
                </tbody>
            </table>
            ${items.length === 0 ? `<div class="text-center text-secondary py-4">Belum ada data.</div>` : ''}
        `;
        document.getElementById('tableWrapper').innerHTML = html;
    },

    openForm() {
        document.getElementById('formTitle').textContent = 'Tambah User';
        document.getElementById('fieldId').value = '';
        document.getElementById('fieldNama').value = '';
        document.getElementById('fieldEmail').value = '';
        document.getElementById('fieldPassword').value = '';
        document.getElementById('fieldRole').value = 'staff';
        document.getElementById('fieldActive').checked = true;
        document.getElementById('pwdHint').textContent = '(wajib)';
        new bootstrap.Modal(document.getElementById('formModal')).show();
    },

    async edit(id) {
        try {
            const u = await api.get(`/api/user/${id}`);
            document.getElementById('formTitle').textContent = 'Edit User';
            document.getElementById('fieldId').value = u.id;
            document.getElementById('fieldNama').value = u.name || '';
            document.getElementById('fieldEmail').value = u.email || '';
            document.getElementById('fieldPassword').value = '';
            document.getElementById('fieldRole').value = u.role || 'staff';
            document.getElementById('fieldActive').checked = !!u.is_active;
            document.getElementById('pwdHint').textContent = '(kosongkan jika tidak diubah)';
            new bootstrap.Modal(document.getElementById('formModal')).show();
        } catch (err) { toast('Gagal', err.message, 'danger'); }
    },

    async submit(e) {
        e.preventDefault();
        const id = document.getElementById('fieldId').value;
        const body = {
            name: document.getElementById('fieldNama').value.trim(),
            email: document.getElementById('fieldEmail').value.trim(),
            role: document.getElementById('fieldRole').value,
            is_active: document.getElementById('fieldActive').checked,
        };
        const pwd = document.getElementById('fieldPassword').value;
        if (pwd) body.password = pwd;
        else if (!id) { toast('Validasi', 'Password wajib untuk user baru', 'warning'); return; }
        try {
            if (id) await api.put(`/api/user/${id}`, body);
                else await api.post('/api/user/', body);
            toast('Berhasil', 'User disimpan', 'success');
            bootstrap.Modal.getInstance(document.getElementById('formModal')).hide();
            await this.loadTable();
        } catch (err) { toast('Gagal', err.message, 'danger'); }
    },

    async toggleActive(id, aktif) {
        try {
            await api.put(`/api/user/${id}/toggle-active`, { is_active: aktif });
            toast('Berhasil', `User ${aktif ? 'diaktifkan' : 'dinonaktifkan'}`, 'success');
            await this.loadTable();
        } catch (err) { toast('Gagal', err.message, 'danger'); }
    },

    async destroy(id, nama) {
        if (!await confirmDialog({ message: `Hapus user "${nama}"?`, confirmText: 'Hapus' })) return;
        try {
            await api.delete(`/api/user/${id}`);
            toast('Berhasil', 'User dihapus', 'success');
            await this.loadTable();
        } catch (err) { toast('Gagal', err.message, 'danger'); }
    },
};

document.addEventListener('DOMContentLoaded', () => UserModule.init());
