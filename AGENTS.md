# AGENTS.md

## Tentang proyek ini

Aplikasi web manajemen inventaris (InventarisKu) dibangun di atas **Fenrir Framework v4.1.2** (Python 3.12 async) + **MongoDB Atlas** + **Cloudinary**. Satu paket, bukan monorepo.

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

- **508 tests**, **93% coverage**
- Menggunakan `mongomock` — tidak perlu MongoDB asli untuk testing
- `conftest.py` menyiapkan mock DB, session, dan fixtures
- `RateLimitMiddleware` harus dihapus saat testing (lihat `conftest.py`)

## Variabel environment penting

**PENTING: Jangan pernah menghapus/menimpa `.env` yang sudah ada. Selalu backup dulu (`cp .env .env.bak`) sebelum mengubah file ini.** File `.env` berisi credential asli (MongoDB URI, Cloudinary URL) yang tidak bisa dipulihkan dari `.env.example`.

Wajib: `MONGO_URI`, `MONGO_DB_NAME`, `APP_SECRET_KEY`. Opsional: `CLOUDINARY_URL` (fallback ke upload lokal jika tidak ada). Lihat `.env.example` untuk daftar lengkap termasuk flag monitoring.

## Arsitektur sekilas

- **`app.py`** — Titik masuk. Mendaftarkan semua blueprint, mengkonfigurasi renderer Jinja2 dengan custom filter (`formatNumber`, `formatRupiah`, `formatDate`, `formatDateTime`), error handler, middleware.
- **`config/database.py`** — MongoDB singleton via `pymongo`. `get_db()` membuat index saat pertama kali dipanggil. `USE_MONGOMOCK=1` untuk testing tanpa DB asli.
- **`config/cloudinary_client.py`** — Konfigurasi Cloudinary dengan dukungan reload env. Lazy-configured per request.
- **`models/__init__.py`** — Wrapper tipis: setiap fungsi mengembalikan `collection("name")`. Tanpa ORM, tanpa model Pydantic — dokumen adalah dict biasa.
- **`services/`** — Logika bisnis. Semua fungsi sync (bukan async). Gunakan `serialize_doc`/`serialize_docs` dari `utils/helpers.py` untuk mengkonversi ObjectId/datetime sebelum mengembalikan hasil.
- **`routes/`** — Fenrir Blueprints. Route JSON API di bawah `/api/`. Route halaman mengembalikan template Jinja2.
- **`utils/decorators.py`** — `@login_required` (redirect), `@api_login_required` (HTTP 401), `@role_required("admin")` (HTTP 403).
- **`templates/`** — Jinja2. `base.html` adalah shell utama; partial di `partials/`.

## Konvensi yang harus diikuti

- **Bahasa**: Komentar kode, pesan error, teks UI, dan nama variabel dalam **Bahasa Indonesia**. Ikuti ini.
- **Autentikasi**: Berbasis session via `fenrir.session`. Key: `isLoggedIn`, `userId`, `userName`, `userRole`, `userPhoto`.
- **Audit trail**: Setiap operasi CRUD memanggil `aktivitas_service.log(...)`. Sertakan ini saat menambahkan mutasi baru.
- **Riwayat stok**: `barang_service.catat_riwayat_stok(...)` harus dipanggil pada setiap perubahan stok.
- **Tidak async di service**: Layer service menggunakan fungsi sync biasa. Route async tetapi mendelegasikan ke service sync.
- **Penanganan ObjectId**: Selalu gunakan `parse_object_id()` dari `utils/helpers.py` sebelum query MongoDB. Kembalikan `serialize_doc()` untuk response JSON.
- **Nomor transaksi**: `generate_no_transaksi(prefix)` dari `utils/security.py` — format `PREFIX-YYYYMMDD-XXXXXXXX`.
- **Hashing password**: PBKDF2-HMAC-SHA256 via `utils/security.py`. Bukan bcrypt meskipun ada di requirements.
- **Foto Cloudinary**: `services/cloudinary_service.py` membungkus `config/cloudinary_client.py`. Upload foto user/logo fallback ke lokal `static/uploads/` jika Cloudinary gagal.

## Yang perlu diperhatikan

- **Blueprint route literal sebelum route parameter**: Fenrir mencocokkan route secara literal terlebih dahulu. Taruh path literal (misalnya `/upload-foto`) sebelum route `/<id>` dalam blueprint yang sama. Lihat `routes/api_barang.py:198`.
- **`FENRIR_DEV_MODE=1`**: Mengaktifkan halaman debug gaya Laravel. Jangan pernah diaktifkan di production.
- **Procfile menggunakan `asteri`**: `web: asteri app:app -k asgui -w 4 -b 0.0.0.0:8000` — ini adalah server ASGI Fenrir/asteri, bukan uvicorn.
- **Runtime**: `python-3.12` (dari `runtime.txt`).
- **Filesystem sementara**: Foto user/logo di `static/uploads/` hilang saat deploy Railway. Foto barang tetap aman via Cloudinary.
- **`_SessionProxy`**: Template `session` adalah proxy yang membaca `fenrir.session` per-request. Jangan import session di level modul dalam template context.
- **Penyimpanan tanggal**: Tanggal transaksi disimpan sebagai string ISO (misalnya `"2025-01-15"`), bukan objek MongoDB Date.
- **Filter stok**: Filtering client-side untuk status stok (`hampir-habis`, `habis`, `tersedia`) terjadi di `barang_service.list_barang()` setelah mengambil semua dokumen yang cocok — bukan di query MongoDB.

## Interaksi
- pakai bahasa indonesia
- utamakan untuk pengeditan file saja
- selalu tanya untuk commit dan push ke github