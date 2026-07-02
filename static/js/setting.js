document.addEventListener('DOMContentLoaded', async () => {
    await loadSettings();
    document.getElementById('formSetting').addEventListener('submit', saveSettings);
    document.getElementById('btnUploadLogo').addEventListener('click', uploadAsset.bind(null, 'logo', 'fieldLogo', 'logoPreview'));
    document.getElementById('btnUploadFavicon').addEventListener('click', uploadAsset.bind(null, 'favicon', 'fieldFavicon', 'faviconPreview'));
});

async function loadSettings() {
    try {
        const res = await api.get('/api/setting/');
        const s = res.data || {};
        document.getElementById('fieldNama').value = s.nama_aplikasi || '';
        document.getElementById('fieldJudul').value = s.judul_aplikasi || '';
        document.getElementById('fieldTagline').value = s.tagline || '';
        document.getElementById('fieldPerusahaan').value = s.nama_perusahaan || '';
        if (s.logo) document.getElementById('logoPreview').innerHTML = `<img src="${s.logo}" class="preview-photo rounded" alt="">`;
        if (s.favicon) document.getElementById('faviconPreview').innerHTML = `<img src="${s.favicon}" class="rounded" style="width:64px;height:64px;object-fit:cover" alt="">`;
    } catch (err) { toast('Gagal', err.message, 'danger'); }
}

async function saveSettings(e) {
    e.preventDefault();
    const body = {
        nama_aplikasi: document.getElementById('fieldNama').value.trim(),
        judul_aplikasi: document.getElementById('fieldJudul').value.trim(),
        tagline: document.getElementById('fieldTagline').value.trim(),
        nama_perusahaan: document.getElementById('fieldPerusahaan').value.trim(),
    };
    if (!body.nama_aplikasi) { toast('Validasi', 'Nama aplikasi wajib diisi', 'warning'); return; }
    try {
        await api.put('/api/setting/', body);
        toast('Berhasil', 'Pengaturan disimpan', 'success');
        await loadSettings();
    } catch (err) { toast('Gagal', err.message, 'danger'); }
}

async function uploadAsset(kind, fieldId, previewId) {
    const file = document.getElementById(fieldId).files[0];
    if (!file) { toast('Pilih file', 'Belum ada file', 'warning'); return; }
    const fd = new FormData();
    fd.append('file', file);
    try {
        await api.upload(`/api/setting/upload-asset?kind=${kind}`, fd);
        toast('Berhasil', `${kind} diperbarui`, 'success');
        await loadSettings();
    } catch (err) { toast('Gagal', err.message, 'danger'); }
}
