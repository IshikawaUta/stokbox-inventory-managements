document.addEventListener('DOMContentLoaded', async () => {
    await loadKategori();
    await loadTable();
    document.getElementById('btnFilter').addEventListener('click', loadTable);
});

async function loadKategori() {
    try {
        const res = await api.get('/api/kategori/');
        const sel = document.getElementById('filterKategori');
        (res.data || []).forEach(k => {
            sel.insertAdjacentHTML('beforeend', `<option value="${k.id}">${escapeHtml(k.nama_kategori)}</option>`);
        });
        initSelect2('#filterKategori');
    } catch {}
}

async function loadTable() {
    const params = new URLSearchParams();
    const k = document.getElementById('filterKategori').value;
    const s = document.getElementById('filterStatus').value;
    if (k) params.set('kategori_id', k);
    if (s) params.set('status', s);
    try {
        const res = await api.get(`/api/laporan/stok?${params}`);
        renderTable(res.data || []);
    } catch (err) { toast('Gagal', err.message, 'danger'); }
}

function renderTable(items) {
    const html = `
        <table class="table table-hover align-middle">
            <thead>
                <tr>
                    <th width="50">#</th>
                    <th>Kode</th>
                    <th>Nama</th>
                    <th>Kategori</th>
                    <th class="text-end">Stok</th>
                    <th class="text-end">Min.</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${items.map((it, i) => {
                    const stok = parseInt(it.stok || 0);
                    const min = parseInt(it.stok_minimum || 0);
                    let badge;
                    if (stok === 0) badge = '<span class="badge badge-status-habis">Habis</span>';
                    else if (stok <= min) badge = '<span class="badge badge-status-hampir">Hampir Habis</span>';
                    else badge = '<span class="badge badge-status-tersedia">Tersedia</span>';
                    return `
                    <tr>
                        <td>${i + 1}</td>
                        <td class="mono">${escapeHtml(it.kode_barang)}</td>
                        <td>${escapeHtml(it.nama_barang)}</td>
                        <td>${it.nama_kategori ? `<i class="bi ${it.icon_kategori || 'bi-tag'}"></i> ${escapeHtml(it.nama_kategori)}` : '-'}</td>
                        <td class="text-end">${formatNumber(stok)} ${escapeHtml(it.satuan || '')}</td>
                        <td class="text-end">${formatNumber(min)}</td>
                        <td>${badge}</td>
                    </tr>`;
                }).join('')}
            </tbody>
        </table>
        ${items.length === 0 ? `<div class="text-center text-secondary py-4">Belum ada data.</div>` : ''}
    `;
    document.getElementById('tableWrapper').innerHTML = html;
}
