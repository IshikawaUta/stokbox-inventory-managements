/* API Client + UI helpers */
function _getCookie(name) {
    const val = document.cookie.split(';').find(c => c.trim().startsWith(name + '='));
    return val ? decodeURIComponent(val.split('=')[1]) : '';
}

const api = {
    async request(method, url, body, isForm) {
        const opts = { method, headers: { 'Accept': 'application/json' }, credentials: 'same-origin' };
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
            const csrf = _getCookie('_csrf_token');
            if (csrf) opts.headers['X-CSRF-Token'] = csrf;
        }
        if (body !== undefined && body !== null) {
            if (isForm === 'formdata' || (isForm && body instanceof FormData)) {
                opts.body = body;
            } else if (isForm) {
                const fd = new URLSearchParams();
                Object.entries(body).forEach(([k, v]) => { if (v !== undefined && v !== null) fd.append(k, v); });
                opts.headers['Content-Type'] = 'application/x-www-form-urlencoded';
                opts.body = fd;
            } else {
                opts.headers['Content-Type'] = 'application/json';
                opts.body = JSON.stringify(body);
            }
        }
        const res = await fetch(url, opts);
        const text = await res.text();
        let data;
        try { data = text ? JSON.parse(text) : null; } catch { data = text; }
        if (!res.ok) {
            const msg = (data && (data.error || data.message || data.detail)) || `HTTP ${res.status}`;
            const err = new Error(msg);
            err.status = res.status;
            err.data = data;
            throw err;
        }
        return data;
    },
    get(url) { return this.request('GET', url); },
    post(url, body) { return this.request('POST', url, body, false); },
    postForm(url, body) { return this.request('POST', url, body, true); },
    put(url, body) { return this.request('PUT', url, body, false); },
    delete(url) { return this.request('DELETE', url); },
    upload(url, formData) { return _uploadXHR(url, formData); },
};

function _uploadXHR(url, formData) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', url);
        xhr.withCredentials = true;
        xhr.setRequestHeader('Accept', 'application/json');
        const csrf = _getCookie('_csrf_token');
        if (csrf) xhr.setRequestHeader('X-CSRF-Token', csrf);
        xhr.responseType = 'text';
        xhr.onload = () => {
            const text = xhr.responseText;
            let data;
            try { data = text ? JSON.parse(text) : null; } catch { data = text; }
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(data);
            } else {
                const msg = (data && (data.error || data.message || data.detail)) || `HTTP ${xhr.status}`;
                const err = new Error(msg);
                err.status = xhr.status;
                err.data = data;
                reject(err);
            }
        };
        xhr.onerror = () => reject(new Error('Kesalahan jaringan saat upload.'));
        xhr.send(formData);
    });
}

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function formatDate(value) {
    if (!value) return '-';
    try {
        const d = new Date(value);
        if (isNaN(d.getTime())) return value;
        return d.toLocaleDateString('id-ID', { year: 'numeric', month: 'short', day: '2-digit' });
    } catch { return value; }
}

function formatDateTime(value) {
    if (!value) return '-';
    try {
        const d = new Date(value);
        if (isNaN(d.getTime())) return value;
        return d.toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' });
    } catch { return value; }
}

function formatNumber(value, dec = 0) {
    if (value === null || value === undefined) return '0';
    return new Intl.NumberFormat('id-ID', { minimumFractionDigits: dec, maximumFractionDigits: dec }).format(value);
}

function formatRupiah(value) {
    if (value === null || value === undefined) return 'Rp 0';
    return 'Rp ' + new Intl.NumberFormat('id-ID').format(value);
}

function debounce(fn, delay = 300) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}

function downloadFile(url, filename) {
    fetch(url, { credentials: 'same-origin' })
        .then(r => { if (!r.ok) throw new Error('Gagal unduh'); return r.blob(); })
        .then(blob => {
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = filename || url.split('/').pop();
            a.click();
            URL.revokeObjectURL(a.href);
        })
        .catch(err => toast('Gagal mengunduh file', err.message, 'danger'));
}
