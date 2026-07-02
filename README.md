# InventarisKu

[![Fenrir Framework](https://img.shields.io/badge/Fenrir-4.1.2-purple.svg)](https://pypi.org/project/fenrir-framework/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-508%20Passed-brightgreen.svg)](https://github.com/IshikawaUta/stokbox-inventory-managements/actions)
[![CI](https://github.com/IshikawaUta/stokbox-inventory-managements/actions/workflows/test.yml/badge.svg)](https://github.com/IshikawaUta/stokbox-inventory-managements/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/Coverage-93%25-brightgreen.svg)]()
[![MongoDB](https://img.shields.io/badge/DB-MongoDB%20Atlas-green.svg)](https://www.mongodb.com/atlas)
[![Cloudinary](https://img.shields.io/badge/Storage-Cloudinary-orange.svg)](https://cloudinary.com)

Sistem manajemen inventaris barang modern berbasis **Fenrir Framework v4.1.2** + **MongoDB Atlas**.

- **Backend**: [Fenrir Web Framework](https://pypi.org/project/fenrir-framework/) v4.1.2 (Python 3.12, async)
- **Database**: MongoDB Atlas (NoSQL)
- **Media Storage**: Cloudinary (foto barang) + local untuk profil user & logo
- **Frontend**: Jinja2 templates + Vanilla JS (no build step)
- **Tests**: 508 tests, 93% coverage (pytest + mongomock)

## Fitur

- **Autentikasi** — Login multi-role (admin & staff), session-based
- **Dashboard** — Statistik real-time: 8 kartu ringkasan, 3 grafik (baris masuk/keluar, donat kategori, batang top 5), 4 tabel
- **Manajemen Barang** — CRUD + upload foto ke Cloudinary + QR/barcode + riwayat stok dengan search & filter
- **Manajemen Kategori** — CRUD, filter barang per kategori
- **Manajemen Suplier** — CRUD
- **Transaksi Barang Masuk** — Multi-item, validasi stok, cetak stok minimum, cetak transaksi
- **Transaksi Barang Keluar** — Multi-item, validasi stok mencukupi, cetak transaksi
- **Penyesuaian Stok** — Stock opname + pembatalan dengan audit trail
- **Manajemen Pengguna** — CRUD, upload foto profil, toggle aktif/nonaktif
- **Profil & Ganti Password** — User bisa update profil sendiri
- **Pengaturan Aplikasi** — Nama, tagline, logo, favicon
- **Catatan Aktivitas** — Audit trail untuk semua operasi CRUD + import
- **Riwayat Stok** — Riwayat perubahan stok per barang (masuk, keluar, penyesuaian)
- **Laporan** — Stok, barang masuk, barang keluar, penyesuaian stok (dengan cetak)
- **Backup & Restore** — Ekspor/impor database JSON + download otomatis
- **Import/Export Excel** — Template dinamis, import barang via XLSX
- **QR Code & Barcode** — Generate, tampilkan, dan cetak QR/barcode per barang

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

Test menggunakan `mongomock` — tidak perlu MongoDB asli untuk testing.

## Akun Default

| Role  | Email                    | Password   |
| ----- | ------------------------ | ---------- |
| admin | `admin@inventaris.local` | `admin123` |

Akun admin otomatis dibuat saat pertama kali aplikasi dijalankan dan tidak ada user di database.

## Struktur Direktori

```
inventaris/
├── app.py                        # Entry point aplikasi
├── requirements.txt
├── .env.example
├── .gitignore
├── Procfile                      # Railway deployment
├── runtime.txt                   # Python 3.12
├── AGENTS.md                     # Arsitektur & konvensi proyek
├── config/                       # Konfigurasi DB & Cloudinary
│   ├── database.py
│   └── cloudinary_client.py
├── models/                       # Koleksi MongoDB
├── services/                     # Business logic
│   ├── auth_service.py
│   ├── barang_service.py
│   ├── kategori_service.py
│   ├── suplier_service.py
│   ├── barang_masuk_service.py
│   ├── barang_keluar_service.py
│   ├── stok_penyesuaian_service.py
│   ├── setting_service.py
│   ├── cloudinary_service.py
│   ├── aktivitas_service.py
│   └── laporan_backup_service.py
├── routes/                       # Fenrir Blueprints
│   ├── page.py
│   ├── auth.py
│   ├── api_kategori.py
│   ├── api_barang.py
│   ├── api_suplier.py
│   ├── api_barang_masuk.py
│   ├── api_barang_keluar.py
│   ├── api_stok_penyesuaian.py
│   ├── api_user.py
│   ├── api_setting.py
│   ├── api_aktivitas.py
│   └── api_laporan_backup.py
├── utils/                        # Utilitas
│   ├── security.py
│   ├── helpers.py
│   └── decorators.py
├── templates/                    # Jinja2 templates
│   ├── base.html
│   ├── partials/
│   ├── auth/
│   ├── barang/
│   ├── kategori/
│   ├── suplier/
│   ├── barang_masuk/
│   ├── barang_keluar/
│   ├── stok_penyesuaian/
│   ├── user/
│   ├── setting/
│   ├── dashboard/
│   ├── aktivitas/
│   ├── laporan/
│   └── backup/
├── static/
│   ├── css/
│   ├── js/
│   ├── vendor/
│   └── uploads/
├── tests/                        # 508 tests, 93% coverage
│   ├── conftest.py
│   ├── test_services_*.py
│   ├── test_routes_*.py
│   └── test_utils_*.py
└── .github/
    └── workflows/
        └── test.yml              # CI: auto-run tests on push/PR
```

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

Dokumentasi otomatis tersedia di `/docs` (Swagger UI) dan `/redoc`.

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
   | `DEBUG` | `false` |

4. **Deploy** — Railway auto-detect `Procfile` → jalankan `fenrir run app:app`.

5. **Catatan**: Filesystem Railway bersifat ephemeral. Foto barang aman di Cloudinary, tapi foto profil user & logo tersimpan lokal akan hilang saat deploy ulang.

## Lisensi

MIT
