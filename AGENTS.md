# AGENTS.md

## Tentang proyek ini

Aplikasi web manajemen inventaris (InventarisKu) dibangun di atas **Fenrir Framework v4.3.2** (Python 3.12 async) + **MongoDB Atlas** + **Cloudinary**. Satu paket, bukan monorepo.

## Server development

```bash
fenrir run app.py --dev    # localhost:8000
```

## Testing

```bash
# Jalankan semua test
python -m pytest tests/ -v

# Dengan coverage
python -m pytest tests/ --cov=. --cov-report=term-missing
```

- **717 tests**, **94% coverage**
- Menggunakan `mongomock` — tidak perlu MongoDB asli untuk testing
- `conftest.py` menyiapkan mock DB, session, dan fixtures
- `RateLimitMiddleware`, `CSRFMiddleware`, `SecurityHeadersMiddleware`, `ETagMiddleware` dihapus saat testing (lihat `conftest.py`)
- Coverage config di `pyproject.toml` — omit shibokensupport, PySide6, site-packages

## Variabel environment penting

**PENTING: Jangan pernah menghapus/menimpa `.env` yang sudah ada. Selalu backup dulu (`cp .env .env.bak`) sebelum mengubah file ini.** File `.env` berisi credential asli (MongoDB URI, Cloudinary URL) yang tidak bisa dipulihkan dari `.env.example`.

Wajib: `MONGO_URI`, `MONGO_DB_NAME`, `APP_SECRET_KEY`. Opsional: `CLOUDINARY_URL` (fallback ke upload lokal jika tidak ada). Lihat `.env.example` untuk daftar lengkap termasuk flag monitoring.

## Arsitektur sekilas

### Entry Point
- **`app.py`** — Titik masuk. Mendaftarkan 17 blueprints, mengkonfigurasi renderer Jinja2 dengan custom filter (`formatNumber`, `formatRupiah`, `formatDate`, `formatDateTime`), error handler, middleware stack, signals, hooks, monitoring, static file serving, health check, OpenAPI/Swagger.

### Middleware Stack (urutan pendaftaran)
1. `CORSMiddleware` — Cross-origin resource sharing
2. `RequestIDMiddleware` — Unique request ID per request
3. `RateLimitMiddleware` — Rate limiting 500 req/min
4. `GZipMiddleware` — Response gzip compression (min 500 bytes)
5. `CSRFMiddleware` — CSRF protection (**production only**, aktif saat `APP_ENV=production`)
6. `SecurityHeadersMiddleware` — CSP, X-Frame-Options, dll
7. `ETagMiddleware` — ETag generation untuk JSON GET responses (MD5-based)

### Fitur Framework yang Digunakan
- **Blueprint** — 17 blueprints untuk modularisasi route
- **Dependency Injection** — `Depends(PaginationParams)`, `Body(...)`, `Query(...)`, `File(...)`
- **Session** — `fenrir.session` — request-bound session store
- **Signals** — `request_started`, `request_finished` — auto request counting
- **Hooks** — `on_request`, `on_exception` via HookRegistry (pakai `.register()` bukan `.on()`)
- **WebSocket** — Real-time notifikasi stok rendah dengan heartbeat (30s ping, 10s timeout)
- **SSE** — Live streaming aktivitas dan alert stok via EventSourceResponse
- **Background Tasks** — `from fenrir.background import BackgroundTasks` (hanya di routes)
- **Queue/Worker** — `MemoryQueue` + `Worker` untuk background jobs
- **Cache** — `SyncCache` (thread-safe) + `@cached(ttl, key_prefix)` decorator
- **Jinja2 Renderer** — Custom filters + session proxy
- **Error Handlers** — 404, 500, HTTPException, MultipartParseError
- **OpenAPI/Swagger** — `/docs` (Swagger UI), `/redoc` (ReDoc), `/openapi.json`
- **Monitoring** — Dashboard monitoring opsional via env variable
- **Testing** — `FenrirTestClient` untuk testing

### Layer Aplikasi
- **`config/database.py`** — MongoDB singleton via `pymongo`. `get_db()` membuat 12 indexes saat pertama kali dipanggil. `USE_MONGOMOCK=1` untuk testing tanpa DB asli.
- **`config/cloudinary_client.py`** — Konfigurasi Cloudinary dengan dukungan reload env. Lazy-configured per request.
- **`config/cache.py`** — `SyncCache` thread-safe dengan TTL dan prefix-based invalidation. `@cached` decorator untuk caching service layer.
- **`config/queue.py`** — Fenrir `MemoryQueue` + `Worker` singleton untuk background jobs. `enqueue_job()` helper.
- **`config/schemas.py`** — 34 Pydantic v2 models untuk request/response validation + `PaginationParams`.
- **`models/__init__.py`** — Wrapper tipis: 10 collection functions. Tanpa ORM, dokumen adalah dict biasa.
- **`services/`** — Logika bisnis. Semua fungsi sync (bukan async). Gunakan `serialize_doc`/`serialize_docs` dari `utils/helpers.py`.
- **`routes/`** — Fenrir Blueprints. Route JSON API di bawah `/api/`. Route halaman mengembalikan template Jinja2. Semua handler async, mendelegasikan ke service sync via `asyncio.to_thread()`.
- **`utils/decorators.py`** — `@login_required` (redirect), `@api_login_required` (HTTP 401), `@role_required(*roles)` (HTTP 403).
- **`utils/helpers.py`** — `parse_object_id()`, `serialize_doc()`, `serialize_docs()`, `utcnow()`, `parse_date()`.
- **`utils/security.py`** — `hash_password()` (PBKDF2-HMAC-SHA256, 120k iterations), `verify_password()`, `generate_no_transaksi(prefix)`.
- **`templates/`** — Jinja2. `base.html` adalah shell utama; partial di `partials/`.
- **`static/sw.js`** — Service worker untuk offline caching (cache-first static, network-first HTML).

## Konvensi yang harus diikuti

### Bahasa & Penamaan
- **Bahasa**: Komentar kode, pesan error, teks UI, dan nama variabel dalam **Bahasa Indonesia**. Ikuti ini.

### Autentikasi & Sesi
- **Autentikasi**: Berbasis session via `fenrir.session`. Key: `isLoggedIn`, `userId`, `userName`, `userRole`, `userPhoto`.
- **Session proxy**: Template `session` adalah `_SessionProxy` yang membaca `fenrir.session` per-request. Jangan import session di level modul dalam template context.

### Keamanan
- **CSRF**: Aktif hanya di production (`APP_ENV=production`). Client-side: `api.js` baca cookie `_csrf_token`, kirim sebagai header `X-CSRF-Token` pada POST/PUT/DELETE/PATCH.
- **Password hashing**: PBKDF2-HMAC-SHA256 via `utils/security.py`. Bukan bcrypt meskipun ada di requirements.
- **Role-based access**: Admin-only untuk CRUD master data dan setting. Admin/staff untuk transaksi. Auth untuk semua data read.

### Database & Data
- **Penanganan ObjectId**: Selalu gunakan `parse_object_id()` dari `utils/helpers.py` sebelum query MongoDB. Kembalikan `serialize_doc()` untuk response JSON.
- **Nomor transaksi**: `generate_no_transaksi(prefix)` dari `utils/security.py` — format `PREFIX-YYYYMMDD-XXXXXXXX`.
- **Penyimpanan tanggal**: Tanggal transaksi disimpan sebagai string ISO (misalnya `"2025-01-15"`), bukan objek MongoDB Date.
- **Filter stok**: Filtering client-side untuk status stok (`hampir-habis`, `habis`, `tersedia`) terjadi di `barang_service.list_barang()` setelah mengambil semua dokumen — bukan di query MongoDB.
- **MongoDB indexes**: 12 indexes otomatis dibuat saat pertama kali `get_db()` dipanggil (unique constraints + query optimization).

### Audit & Riwayat
- **Audit trail**: Setiap operasi CRUD memanggil `aktivitas_service.log(...)`. Sertakan ini saat menambahkan mutasi baru.
- **Riwayat stok**: `barang_service.catat_riwayat_stok(...)` harus dipanggil pada setiap perubahan stok (masuk, keluar, penyesuaian).

### Arsitektur Layer
- **Tidak async di service**: Layer service menggunakan fungsi sync biasa. Route async tetapi mendelegasikan ke service sync via `asyncio.to_thread()`.
- **Cache invalidation**: Service layer pakai `@cached` decorator. Invalidate cache menggunakan `_get_cache()` pattern.
- **Foto Cloudinary**: `services/cloudinary_service.py` membungkus `config/cloudinary_client.py`. Upload foto user/logo fallback ke lokal `static/uploads/` jika Cloudinary gagal. Ghost upload verify via HEAD request.
- **Background jobs**: `config/queue.py` register handler via `q.register(name, func)`. `enqueue_job()` kirim ke `MemoryQueue` backend.
- **WebSocket heartbeat**: 30s ping interval, 10s timeout. Client harus respond pong agar tidak disconnect.

## Yang perlu diperhatikan

### Route & Blueprint
- **Blueprint route literal sebelum route parameter**: Fenrir mencocokkan route secara literal terlebih dahulu. Taruh path literal (misalnya `/upload-foto`) sebelum route `/<id>` dalam blueprint yang sama. Lihat `routes/api_barang.py`.
- **4 blueprints dalam 1 file**: `routes/api_laporan_backup.py` berisi `laporan_bp`, `backup_bp`, `barcode_bp`, dan `transaksi_bp`.

### Environment & Deployment
- **`APP_ENV=production`**: Aktifkan CSRF, SecurityHeaders. Development: nonaktif.
- **`FENRIR_DEV_MODE=1`**: Mengaktifkan halaman debug gaya Laravel. Jangan pernah diaktifkan di production.
- **`SESSION_COOKIE_SECURE`**: Set ke `1` hanya jika server pakai HTTPS. Railway harus `1`.
- **Procfile**: `web: fenrir run app:app --host 0.0.0.0 --port 8000 --workers 4 --disable-dashboard`.
- **Runtime**: `python-3.12` (dari `runtime.txt`).
- **Filesystem sementara**: Foto user/logo di `static/uploads/` hilang saat deploy Railway. Foto barang tetap aman via Cloudinary.

### Performance & Optimasi
- **Static file cache headers**: JS/CSS 1 tahun, fonts 1 tahun, images 1 hari.
- **Service worker**: `static/sw.js` cache-first untuk static assets, network-first untuk HTML.
- **Preconnect CDN**: `cdn.jsdelivr.net` untuk scripts/styles/fonts/connect.
- **Lazy load images**: `loading="lazy"` pada foto user, logo, dan gambar non-kritis.
- **fetchpriority hints**: `fetchpriority="high"` pada logo login, `fetchpriority="low"` pada sidebar/topbar.
- **Script on-demand**: Chart.js, Select2, DataTables hanya dimuat saat diperlukan.

### Testing
- **conftest.py**: Disable RateLimit, CSRF, SecurityHeaders, ETag middlewares. Set `APP_ENV=development`.
- **mongomock**: Semua test pakai mock MongoDB, tidak perlu MongoDB asli.
- **FenrirTestClient**: `from fenrir.testing import FenrirTestClient` — sync wrapper untuk testing.

### BackgroundTasks DI
- **Jangan pakai `from __future__ import annotations`** di file yang pakai `BackgroundTasks` sebagai parameter. Ini membreak Fenrir's DI type check karena annotations jadi string.

## Interaksi
- pakai bahasa indonesia
- utamakan untuk pengeditan file saja
- selalu tanya untuk commit dan push ke github
