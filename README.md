# InventarisKu

[![Fenrir Framework](https://img.shields.io/badge/Fenrir-4.3.2-purple.svg)](https://pypi.org/project/fenrir-framework/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-717%20Passed-brightgreen.svg)](https://github.com/IshikawaUta/stokbox-inventory-managements/actions)
[![CI](https://github.com/IshikawaUta/stokbox-inventory-managements/actions/workflows/test.yml/badge.svg)](https://github.com/IshikawaUta/stokbox-inventory-managements/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/IshikawaUta/stokbox-inventory-managements/branch/main/graph/badge.svg)](https://codecov.io/gh/IshikawaUta/stokbox-inventory-managements)
[![MongoDB](https://img.shields.io/badge/DB-MongoDB%20Atlas-green.svg)](https://www.mongodb.com/atlas)
[![Cloudinary](https://img.shields.io/badge/Storage-Cloudinary-orange.svg)](https://cloudinary.com)

Sistem manajemen inventaris barang modern berbasis **Fenrir Framework v4.3.2** + **MongoDB Atlas**.

- **Backend**: [Fenrir Web Framework](https://pypi.org/project/fenrir-framework/) v4.3.2 (Python 3.12, async)
- **Database**: MongoDB Atlas (NoSQL) via pymongo + mongomock (testing)
- **Media Storage**: Cloudinary (foto barang) + local untuk profil user & logo
- **Frontend**: Jinja2 templates + Vanilla JS (no build step)
- **Real-time**: WebSocket (stok alerts) + Server-Sent Events (activity stream)
- **Background Jobs**: Fenrir Queue/MemoryQueue + Worker
- **Testing**: 717 tests, 94% coverage (pytest + mongomock)

## Fitur

### Fitur Utama
- **Autentikasi** — Login multi-role (admin & staff), session-based, profil & ganti password
- **Dashboard** — Statistik real-time: 8 kartu ringkasan, 3 grafik (baris masuk/keluar, donat kategori, batang top 5), 4 tabel
- **Manajemen Barang** — CRUD + upload foto ke Cloudinary + QR/barcode + riwayat stok dengan search & filter
- **Manajemen Kategori** — CRUD, filter barang per kategori
- **Manajemen Suplier** — CRUD
- **Transaksi Barang Masuk** — Multi-item, validasi stok, cetak stok minimum, cetak transaksi
- **Transaksi Barang Keluar** — Multi-item, validasi stok mencukupi, cetak transaksi
- **Penyesuaian Stok** — Stock opname + pembatalan dengan audit trail
- **Manajemen Pengguna** — CRUD, upload foto profil, toggle aktif/nonaktif
- **Pengaturan Aplikasi** — Nama, tagline, logo, favicon

### Fitur Tambahan
- **Catatan Aktivitas** — Audit trail untuk semua operasi CRUD + import
- **Riwayat Stok** — Riwayat perubahan stok per barang (masuk, keluar, penyesuaian)
- **Laporan** — Stok, barang masuk, barang keluar, penyesuaian stok (dengan cetak)
- **Backup & Restore** — Ekspor/impor database JSON + download otomatis
- **Import/Export Excel** — Template dinamis, import barang via XLSX
- **QR Code & Barcode** — Generate, tampilkan, dan cetak QR/barcode per barang

### Fitur Framework & Real-time
- **WebSocket** — Real-time notifikasi stok rendah via `/ws/notifications` dengan heartbeat ping/pong
- **Server-Sent Events** — Live streaming aktivitas dan alert stok via `/api/sse/`
- **Background Queue** — Job queue untuk proses async (priority, delay, retry, timeout)
- **Cache** — In-memory TTL cache (`SyncCache`) + `@cached` decorator untuk service layer
- **Security** — CSRF (production-only), CSP headers, Rate Limiting (500 req/min), CORS, ETag
- **Performance** — GZip compression, static file cache headers, Service Worker offline caching
- **OpenAPI/Swagger** — Dokumentasi otomatis di `/docs` (Swagger UI) dan `/redoc`
- **Monitoring** — Dashboard monitoring opsional via env variable

## Persyaratan

- Python 3.12+
- Akun MongoDB Atlas (cluster gratis cukup)
- Akun Cloudinary (free tier cukup, opsional — fallback ke local storage)

## Instalasi

1. **Clone repo**

   ```bash
   git clone https://github.com/IshikawaUta/stokbox-inventory-managements.git
   cd stokbox-inventory-managements
   ```

2. **Buat virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate    # Linux/Mac
   venv\Scripts\activate       # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurasi environment**

   Copy `.env.example` dan isi credential asli:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` — wajib diisi:

   ```env
   MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/inventaris?retryWrites=true&w=majority
   MONGO_DB_NAME=inventaris
   CLOUDINARY_URL=cloudinary://your_api_key:your_api_secret@your_cloud_name
   APP_SECRET_KEY=ganti-dengan-string-random-yang-panjang
   ```

   **PENTING**: Jangan pernah menghapus/menimpa `.env` yang sudah ada. Selalu backup dulu (`cp .env .env.bak`).

5. **Jalankan aplikasi**

   ```bash
   fenrir run app.py --dev
   ```

   Buka <http://localhost:8000>.

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

## Akun Default

| Role  | Email                    | Password   |
| ----- | ------------------------ | ---------- |
| admin | `admin@inventaris.local` | `admin123` |

Akun admin otomatis dibuat saat pertama kali aplikasi dijalankan dan tidak ada user di database.

## Struktur Direktori

```
inventaris/
├── app.py                          # Entry point: middleware, blueprints, signals, hooks
├── requirements.txt
├── pyproject.toml                  # Pytest + coverage config
├── .env.example
├── .gitignore
├── Procfile                        # Railway deployment
├── runtime.txt                     # Python 3.12
├── AGENTS.md                       # Arsitektur & konvensi proyek
├── README.md                       # Dokumentasi proyek
├── LICENSE                         # MIT License
├── favicon.ico                     # App favicon
├── logo.png                        # App logo
│
├── config/                         # Konfigurasi
│   ├── __init__.py
│   ├── database.py                 # MongoDB singleton (pymongo), 12 indexes
│   ├── cloudinary_client.py        # Cloudinary SDK config
│   ├── cache.py                    # SyncCache + @cached decorator
│   ├── queue.py                    # Fenrir MemoryQueue + Worker
│   └── schemas.py                  # Pydantic v2 request/response models (510 lines)
│
├── models/                         # Koleksi MongoDB (wrapper tipis)
│   └── __init__.py                 # 10 collection functions
│
├── services/                       # Business logic (semua sync)
│   ├── __init__.py
│   ├── auth_service.py             # Auth + user CRUD + profile + password
│   ├── barang_service.py           # Barang CRUD + dashboard stats + import
│   ├── kategori_service.py         # Kategori CRUD + cache
│   ├── suplier_service.py          # Suplier CRUD + cache
│   ├── barang_masuk_service.py     # Transaksi masuk + stock update + riwayat
│   ├── barang_keluar_service.py    # Transaksi keluar + stock update + riwayat
│   ├── stok_penyesuaian_service.py # Stok adjustment + cancel
│   ├── setting_service.py          # App settings (key-value)
│   ├── aktivitas_service.py        # Audit trail logging
│   └── cloudinary_service.py       # Cloudinary upload + local fallback
│
├── routes/                         # Fenrir Blueprints (async handlers)
│   ├── __init__.py
│   ├── auth.py                     # auth_bp: /auth (login, logout, me)
│   ├── page.py                     # page_bp: 30+ HTML page routes
│   ├── api_kategori.py             # kategori_bp: /api/kategori CRUD
│   ├── api_barang.py               # barang_bp: /api/barang CRUD + upload + import
│   ├── api_suplier.py              # suplier_bp: /api/suplier CRUD
│   ├── api_barang_masuk.py         # bm_bp: /api/barang-masuk CRUD
│   ├── api_barang_keluar.py        # bk_bp: /api/barang-keluar CRUD
│   ├── api_stok_penyesuaian.py     # sp_bp: /api/stok-penyesuaian CRUD + batal
│   ├── api_user.py                 # user_bp: /api/user CRUD + profile + password
│   ├── api_setting.py              # setting_bp: /api/setting get/update + upload
│   ├── api_laporan_backup.py       # laporan_bp + backup_bp + barcode_bp + transaksi_bp
│   ├── api_aktivitas.py            # aktivitas_bp: /api/aktivitas list
│   ├── websocket.py                # ws_bp: /ws/notifications (WebSocket + heartbeat)
│   └── sse.py                      # sse_bp: /api/sse/stock-alerts + activity (SSE)
│
├── utils/                          # Utilitas
│   ├── __init__.py
│   ├── decorators.py               # @login_required, @api_login_required, @role_required
│   ├── helpers.py                  # parse_object_id, serialize_doc, utcnow, parse_date
│   └── security.py                 # hash_password (PBKDF2), generate_no_transaksi
│
├── templates/                      # Jinja2 templates (31 files)
│   ├── base.html                   # Shell utama + service worker registration
│   ├── login.html                  # Login page
│   ├── dashboard.html              # Dashboard dengan stats & charts
│   ├── 404.html                    # Not found error
│   ├── 500.html                    # Server error
│   ├── partials/
│   │   ├── sidebar.html            # Sidebar navigasi (lazy load photo)
│   │   ├── topbar.html             # Top navigation bar
│   │   └── footer.html             # Page footer
│   ├── barang/                     # 6 templates (index, form, detail, import, print QR/barcode)
│   ├── kategori/index.html
│   ├── suplier/index.html
│   ├── barang_masuk/               # 3 templates (index, create, detail)
│   ├── barang_keluar/              # 3 templates (index, create, detail)
│   ├── stok_penyesuaian/           # 3 templates (index, create, detail)
│   ├── user/                       # 3 templates (index, profile, change_password)
│   ├── setting/index.html
│   ├── aktivitas/index.html
│   ├── laporan/                    # 4 templates (stok, barang_masuk, barang_keluar, penyesuaian)
│   └── backup/index.html
│
├── static/                         # Static assets
│   ├── css/
│   │   ├── style.css               # Main stylesheet
│   │   ├── bootstrap-icons.css     # Bootstrap Icons
│   │   └── fonts/                  # Icon fonts (woff, woff2)
│   ├── js/
│   │   ├── api.js                  # API client + CSRF header support
│   │   ├── ui.js                   # UI utilities
│   │   ├── barang.js               # Barang page JS
│   │   ├── barang_masuk.js         # Barang masuk page JS
│   │   ├── barang_keluar.js        # Barang keluar page JS
│   │   ├── stok_penyesuaian.js     # Stok penyesuaian page JS
│   │   ├── kategori.js             # Kategori page JS
│   │   ├── suplier.js              # Suplier page JS
│   │   ├── user.js                 # User page JS
│   │   ├── setting.js              # Setting page JS
│   │   └── laporan_stok.js         # Laporan stok page JS
│   ├── vendor/
│   │   ├── jquery/jquery-3.7.1.min.js
│   │   └── datatables/             # DataTables core + Bootstrap 5 integration
│   ├── img/bg-login.jpg
│   ├── sw.js                       # Service worker (offline caching)
│   └── uploads/                    # User-generated content (ephemeral on Railway)
│
├── tests/                          # 717 tests, 94% coverage
│   ├── conftest.py                 # Fixtures: mock DB, session, middleware disable
│   ├── test_app_config.py
│   ├── test_config_cache.py        # SyncCache + @cached
│   ├── test_config_queue.py        # Background queue
│   ├── test_middleware.py          # ETagMiddleware
│   ├── test_routes_auth.py
│   ├── test_routes_crud.py
│   ├── test_routes_crud_v3.py
│   ├── test_routes_v2.py
│   ├── test_routes_laporan_backup_v2.py
│   ├── test_routes_setting_v2.py
│   ├── test_routes_transaksi.py
│   ├── test_routes_websocket.py
│   ├── test_routes_websocket_v2.py
│   ├── test_routes_sse.py
│   ├── test_services_auth.py
│   ├── test_services_barang.py
│   ├── test_services_barang_v2.py
│   ├── test_services_kategori.py
│   ├── test_services_suplier.py
│   ├── test_services_transaksi.py
│   ├── test_services_v2.py
│   ├── test_services_aktivitas_setting.py
│   ├── test_services_cloudinary_v2.py
│   ├── test_utils_helpers.py
│   └── test_utils_security.py
│
└── .github/workflows/test.yml      # CI: auto-run tests on push/PR
```

## Arsitektur & Fitur Framework

### Middleware Stack (urutan pendaftaran)

| # | Middleware | Keterangan |
| --- | --- | --- |
| 1 | `CORSMiddleware` | Cross-origin resource sharing |
| 2 | `RequestIDMiddleware` | Unique request ID per request |
| 3 | `RateLimitMiddleware` | Rate limiting 500 req/min |
| 4 | `GZipMiddleware` | Response gzip compression |
| 5 | `CSRFMiddleware` | CSRF protection (**production only**) |
| 6 | `SecurityHeadersMiddleware` | CSP, X-Frame-Options, dll |
| 7 | `ETagMiddleware` | ETag generation untuk JSON GET responses |

### Fitur Framework yang Digunakan

| Fitur | Keterangan |
| --- | --- |
| **Blueprint** | 17 blueprints untuk modularisasi route |
| **Dependency Injection** | `Depends(PaginationParams)`, `Body(...)`, `Query(...)`, `File(...)` |
| **Session** | `fenrir.session` — request-bound session store |
| **Signals** | `request_started`, `request_finished` — auto request counting |
| **Hooks** | `on_request`, `on_exception` via HookRegistry |
| **WebSocket** | Real-time notifikasi stok rendah dengan heartbeat (30s ping, 10s timeout) |
| **SSE** | Live streaming aktivitas dan alert stok via EventSourceResponse |
| **Background Tasks** | `from fenrir.background import BackgroundTasks` |
| **Queue/Worker** | `MemoryQueue` + `Worker` untuk background jobs |
| **Cache** | `SyncCache` + `@cached(ttl, key_prefix)` decorator |
| **Jinja2 Renderer** | Custom filters: `formatNumber`, `formatRupiah`, `formatDate`, `formatDateTime` |
| **Error Handlers** | 404, 500, HTTPException, MultipartParseError |
| **OpenAPI/Swagger** | `/docs` (Swagger UI), `/redoc` (ReDoc), `/openapi.json` |
| **Monitoring** | Dashboard monitoring opsional |
| **Testing** | `FenrirTestClient` untuk testing |

## API Endpoints

Semua endpoint JSON di prefix `/api/`. Halaman HTML di root (`/`, `/dashboard`, `/barang`, dst).

### Autentikasi
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| POST | `/auth/login` | Login | public |
| POST | `/auth/logout` | Logout | auth |
| GET | `/auth/logout` | Logout (redirect) | auth |
| GET | `/auth/me` | Info user aktif | auth |

### Barang
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/barang/` | List barang | auth |
| POST | `/api/barang/` | Tambah barang | admin |
| GET | `/api/barang/<id>` | Detail barang | auth |
| PUT | `/api/barang/<id>` | Update barang | admin |
| DELETE | `/api/barang/<id>` | Hapus barang | admin |
| GET | `/api/barang/check-kode` | Cek kode duplikat | auth |
| GET | `/api/barang/low-stock` | List barang stok rendah | auth |
| GET | `/api/barang/lookup` | Lookup barang | auth |
| POST | `/api/barang/upload-foto` | Upload foto barang | admin |
| POST | `/api/barang/upload-foto-base64` | Upload foto (base64) | admin |
| POST | `/api/barang/upload-foto-raw` | Upload foto (raw) | admin |
| GET | `/api/barang/import-template` | Download template Excel | auth |
| POST | `/api/barang/import` | Import dari Excel | admin |
| GET | `/api/barang/<id>/riwayat-stok` | Riwayat stok | auth |

### Kategori
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/kategori/` | List kategori | auth |
| POST | `/api/kategori/` | Tambah kategori | admin |
| GET | `/api/kategori/<id>` | Detail kategori | auth |
| PUT | `/api/kategori/<id>` | Update kategori | admin |
| DELETE | `/api/kategori/<id>` | Hapus kategori | admin |

### Suplier
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/suplier/` | List suplier | auth |
| POST | `/api/suplier/` | Tambah suplier | admin |
| GET | `/api/suplier/<id>` | Detail suplier | auth |
| PUT | `/api/suplier/<id>` | Update suplier | admin |
| DELETE | `/api/suplier/<id>` | Hapus suplier | admin |

### Barang Masuk
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/barang-masuk/` | List barang masuk | auth |
| POST | `/api/barang-masuk/` | Catat barang masuk | admin/staff |
| GET | `/api/barang-masuk/generate-number` | Generate no transaksi | auth |
| GET | `/api/barang-masuk/<id>` | Detail barang masuk | auth |
| PUT | `/api/barang-masuk/<id>` | Edit barang masuk | admin/staff |
| DELETE | `/api/barang-masuk/<id>` | Hapus barang masuk | admin |

### Barang Keluar
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/barang-keluar/` | List barang keluar | auth |
| POST | `/api/barang-keluar/` | Catat barang keluar | admin/staff |
| GET | `/api/barang-keluar/generate-number` | Generate no transaksi | auth |
| GET | `/api/barang-keluar/<id>` | Detail barang keluar | auth |
| PUT | `/api/barang-keluar/<id>` | Edit barang keluar | admin/staff |
| DELETE | `/api/barang-keluar/<id>` | Hapus barang keluar | admin |

### Stok Penyesuaian
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/stok-penyesuaian/` | List penyesuaian | auth |
| POST | `/api/stok-penyesuaian/` | Buat penyesuaian | admin/staff |
| GET | `/api/stok-penyesuaian/generate-number` | Generate no penyesuaian | auth |
| POST | `/api/stok-penyesuaian/<id>/batal` | Batalkan penyesuaian | admin/staff |
| DELETE | `/api/stok-penyesuaian/<id>` | Hapus penyesuaian | admin |

### Pengguna
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/user/` | List pengguna | admin |
| POST | `/api/user/` | Tambah pengguna | admin |
| GET | `/api/user/<id>` | Detail pengguna | admin |
| PUT | `/api/user/<id>` | Update pengguna | admin |
| DELETE | `/api/user/<id>` | Hapus pengguna | admin |
| POST | `/api/user/<id>/toggle-active` | Aktifkan/nonaktifkan | admin |
| PUT | `/api/user/profile` | Update profil sendiri | auth |
| PUT | `/api/user/change-password` | Ganti password | auth |
| POST | `/api/user/profile/photo` | Upload foto profil | auth |

### Pengaturan
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/setting/` | Ambil pengaturan | auth |
| PUT | `/api/setting/` | Update pengaturan | admin |
| POST | `/api/setting/upload-asset` | Upload logo/favicon | admin |

### Laporan
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/laporan/stok` | Laporan stok | auth |
| GET | `/api/laporan/barang-masuk` | Laporan barang masuk | auth |
| GET | `/api/laporan/barang-keluar` | Laporan barang keluar | auth |
| GET | `/api/laporan/penyesuaian-stok` | Laporan penyesuaian | auth |
| GET | `/api/laporan/stok/print` | Cetak laporan stok | auth |
| GET | `/api/laporan/barang-masuk/print` | Cetak laporan masuk | auth |
| GET | `/api/laporan/barang-keluar/print` | Cetak laporan keluar | auth |
| GET | `/api/laporan/penyesuaian-stok/print` | Cetak laporan penyesuaian | auth |

### Barcode & QR Code
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/barcode/barang/<id>/qrcode` | QR Code barang | auth |
| GET | `/api/barcode/barang/<id>/barcode` | Barcode barang | auth |
| GET | `/api/barcode/barang/print-qrcode` | Cetak QR Code | auth |
| GET | `/api/barcode/barang/print-barcode` | Cetak Barcode | auth |

### Cetak Transaksi
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/transaksi/barang-masuk/<id>/print` | Cetak transaksi masuk | auth |
| GET | `/api/transaksi/barang-keluar/<id>/print` | Cetak transaksi keluar | auth |

### Aktivitas & Lainnya
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/api/aktivitas/` | List catatan aktivitas | auth |
| GET | `/api/backup/stats` | Statistik backup | admin |
| GET | `/api/backup/download` | Download backup JSON | admin |
| POST | `/api/backup/restore` | Restore dari file backup | admin |
| GET | `/health` | Health check (MongoDB) | public |

### Real-time Endpoints
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| WebSocket | `/ws/notifications` | Real-time notifikasi stok rendah | auth |
| GET | `/api/sse/stock-alerts` | SSE alert stok rendah (15s polling) | auth |
| GET | `/api/sse/activity` | SSE streaming aktivitas (10s polling) | auth |

### Halaman HTML
| Method | Path | Deskripsi | Role |
| ------ | ---- | --------- | ---- |
| GET | `/` | Home/redirect | public |
| GET | `/login` | Login page | public |
| GET | `/dashboard` | Dashboard | auth |
| GET | `/barang` | List barang | auth |
| GET | `/barang/create` | Form tambah barang | admin |
| GET | `/barang/import` | Form import barang | admin |
| GET | `/barang/print-qrcode` | Cetak QR Code | auth |
| GET | `/barang/print-barcode` | Cetak Barcode | auth |
| GET | `/barang/<id>` | Detail barang | auth |
| GET | `/barang/<id>/edit` | Form edit barang | admin |
| GET | `/kategori` | List kategori | auth |
| GET | `/suplier` | List suplier | auth |
| GET | `/barang-masuk` | List barang masuk | auth |
| GET | `/barang-masuk/create` | Form tambah barang masuk | admin/staff |
| GET | `/barang-masuk/<id>` | Detail barang masuk | auth |
| GET | `/barang-masuk/<id>/edit` | Form edit barang masuk | admin/staff |
| GET | `/barang-keluar` | List barang keluar | auth |
| GET | `/barang-keluar/create` | Form tambah barang keluar | admin/staff |
| GET | `/barang-keluar/<id>` | Detail barang keluar | auth |
| GET | `/barang-keluar/<id>/edit` | Form edit barang keluar | admin/staff |
| GET | `/stok-penyesuaian` | List penyesuaian | auth |
| GET | `/stok-penyesuaian/create` | Form buat penyesuaian | admin/staff |
| GET | `/stok-penyesuaian/<id>` | Detail penyesuaian | auth |
| GET | `/user` | List pengguna | admin |
| GET | `/profile` | Profil user | auth |
| GET | `/change-password` | Ganti password | auth |
| GET | `/setting` | Pengaturan aplikasi | admin |
| GET | `/laporan/stok` | Laporan stok | auth |
| GET | `/laporan/barang-masuk` | Laporan barang masuk | auth |
| GET | `/laporan/barang-keluar` | Laporan barang keluar | auth |
| GET | `/laporan/penyesuaian-stok` | Laporan penyesuaian | auth |
| GET | `/aktivitas` | Catatan aktivitas | auth |
| GET | `/backup` | Backup & restore | admin |

Dokumentasi API otomatis tersedia di `/docs` (Swagger UI) dan `/redoc` (ReDoc).

## Variabel Environment

| Variable | Wajib | Default | Deskripsi |
| -------- | ----- |---------|-----------|
| `MONGO_URI` | Ya | - | MongoDB Atlas connection string |
| `MONGO_DB_NAME` | Ya | - | Nama database |
| `APP_SECRET_KEY` | Ya | - | Secret key untuk session signing |
| `APP_NAME` | Tidak | `InventarisKu` | Nama aplikasi |
| `APP_ENV` | Tidak | `development` | Environment (`development`/`production`) |
| `CLOUDINARY_URL` | Tidak | - | Cloudinary API URL (fallback ke local storage) |
| `CLOUDINARY_FOLDER` | Tidak | `inventaris` | Folder Cloudinary |
| `CORS_ORIGINS` | Tidak | `*` | CORS origins (comma-separated) |
| `SESSION_COOKIE_SECURE` | Tidak | `0` | Set ke `1` jika server pakai HTTPS |
| `FENRIR_DEV_MODE` | Tidak | `0` | Set ke `1` untuk debug page (jangan di production!) |
| `MONITORING_ENABLED` | Tidak | `false` | Aktifkan dashboard monitoring |
| `MONITORING_USER` | Tidak | `admin` | Username monitoring |
| `MONITORING_PASSWORD` | Tidak | `changeme` | Password monitoring |
| `MONITORING_SECRET_KEY` | Tidak | - | Secret key monitoring |

## Deployment ke Railway

1. **Push ke GitHub**

   ```bash
   git push origin main
   ```

2. **Buat project di Railway** — hubungkan repo GitHub.

3. **Set Environment Variables** di Railway Dashboard:

   | Variable | Value |
   | -------- | ----- |
   | `MONGO_URI` | MongoDB Atlas connection string |
   | `MONGO_DB_NAME` | `inventaris` |
   | `CLOUDINARY_URL` | Cloudinary API URL |
   | `CLOUDINARY_FOLDER` | `inventaris` |
   | `APP_SECRET_KEY` | Random string panjang |
   | `APP_ENV` | `production` |
   | `SESSION_COOKIE_SECURE` | `1` (karena Railway pakai HTTPS) |
   | `MONITORING_ENABLED` | `true` (opsional) |

4. **Deploy** — Railway auto-detect `Procfile` → jalankan `fenrir run app:app`.

5. **Catatan**: Filesystem Railway bersifat ephemeral. Foto barang aman di Cloudinary, tapi foto profil user & logo tersimpan lokal akan hilang saat deploy ulang.

## Kontribusi

1. Fork repository
2. Buat branch baru (`git checkout -b feature/nama-fitur`)
3. Commit perubahan (`git commit -m 'Tambah fitur X'`)
4. Push ke branch (`git push origin feature/nama-fitur`)
5. Buka Pull Request

## Lisensi

MIT License - Copyright (c) 2026 IshikawaUta
