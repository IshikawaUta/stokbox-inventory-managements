"""Pydantic v2 schemas untuk validasi data request/response."""
from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ──────────────────────────────────────────────
# Model dasar dengan konfigurasi yang sama
# ──────────────────────────────────────────────


class _Base(BaseModel):
    """Base model dengan konfigurasi untuk field alias & arbitrary types."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# ──────────────────────────────────────────────
# Pagination
# ──────────────────────────────────────────────


class PaginationParams(BaseModel):
    """Parameter pagination untuk request."""

    page: int = Field(default=1, ge=1, description="Nomor halaman (mulai dari 1)")
    per_page: int = Field(default=25, ge=1, le=100, description="Jumlah item per halaman")


# ──────────────────────────────────────────────
# Auth / User
# ──────────────────────────────────────────────


class LoginRequest(BaseModel):
    """Request body untuk login."""

    email: str = Field(..., description="Email pengguna")
    password: str = Field(..., description="Password pengguna")


class LoginResponse(BaseModel):
    """Response setelah login berhasil."""

    message: str = Field(description="Pesan status")
    user: dict = Field(description="Data pengguna")


class UserCreate(BaseModel):
    """Request body untuk membuat user baru."""

    name: str = Field(..., min_length=1, description="Nama lengkap pengguna")
    email: str = Field(..., description="Email pengguna (unik)")
    password: str = Field(..., min_length=6, description="Password minimal 6 karakter")
    role: str = Field(default="staff", description="Peran: admin atau staff")
    photo: Optional[str] = Field(default=None, description="URL foto profil")
    is_active: bool = Field(default=True, description="Status aktif user")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in {"admin", "staff"}:
            raise ValueError("Role harus admin atau staff")
        return v.lower()


class UserUpdate(BaseModel):
    """Request body untuk memperbarui user."""

    name: Optional[str] = Field(default=None, min_length=1, description="Nama lengkap pengguna")
    email: Optional[str] = Field(default=None, description="Email pengguna")
    password: Optional[str] = Field(default=None, min_length=6, description="Password baru (minimal 6 karakter)")
    role: Optional[str] = Field(default=None, description="Peran: admin atau staff")
    photo: Optional[str] = Field(default=None, description="URL foto profil")
    is_active: Optional[bool] = Field(default=None, description="Status aktif user")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"admin", "staff"}:
            raise ValueError("Role harus admin atau staff")
        return v.lower() if v else v


class UserResponse(BaseModel):
    """Response data satu user."""

    id: str = Field(description="ID user (ObjectId)")
    name: str = Field(description="Nama lengkap")
    email: str = Field(description="Email")
    role: str = Field(description="Peran (admin/staff)")
    photo: Optional[str] = Field(default=None, description="URL foto profil")
    is_active: bool = Field(description="Status aktif")
    created_at: Optional[str] = Field(default=None, description="Waktu pembuatan")
    updated_at: Optional[str] = Field(default=None, description="Waktu pembaruan terakhir")


class UserList(BaseModel):
    """Response daftar user."""

    data: list[dict] = Field(description="Daftar user")
    total: int = Field(description="Total jumlah user")


# ──────────────────────────────────────────────
# Kategori
# ──────────────────────────────────────────────


class KategoriCreate(BaseModel):
    """Request body untuk membuat kategori baru."""

    nama_kategori: str = Field(..., min_length=1, description="Nama kategori barang")
    icon_kategori: str = Field(default="bi-box", description="Nama icon Bootstrap (bi-*)")


class KategoriUpdate(BaseModel):
    """Request body untuk memperbarui kategori."""

    nama_kategori: Optional[str] = Field(default=None, min_length=1, description="Nama kategori barang")
    icon_kategori: Optional[str] = Field(default=None, description="Nama icon Bootstrap (bi-*)")


class KategoriResponse(BaseModel):
    """Response data kategori."""

    id: str = Field(description="ID kategori")
    nama_kategori: str = Field(description="Nama kategori")
    icon_kategori: str = Field(description="Icon kategori")
    created_at: Optional[str] = Field(default=None, description="Waktu pembuatan")
    updated_at: Optional[str] = Field(default=None, description="Waktu pembaruan")


# ──────────────────────────────────────────────
# Suplier
# ──────────────────────────────────────────────


class SuplierCreate(BaseModel):
    """Request body untuk membuat suplier baru."""

    nama: str = Field(..., min_length=1, description="Nama suplier")
    no_hp: str = Field(default="", description="Nomor HP suplier")
    email: str = Field(default="", description="Email suplier")
    alamat: str = Field(default="", description="Alamat suplier")
    perusahaan: str = Field(default="", description="Nama perusahaan suplier")


class SuplierUpdate(BaseModel):
    """Request body untuk memperbarui suplier."""

    nama: Optional[str] = Field(default=None, min_length=1, description="Nama suplier")
    no_hp: Optional[str] = Field(default=None, description="Nomor HP suplier")
    email: Optional[str] = Field(default=None, description="Email suplier")
    alamat: Optional[str] = Field(default=None, description="Alamat suplier")
    perusahaan: Optional[str] = Field(default=None, description="Nama perusahaan suplier")


class SuplierResponse(BaseModel):
    """Response data suplier."""

    id: str = Field(description="ID suplier")
    nama: str = Field(description="Nama suplier")
    no_hp: Optional[str] = Field(default=None, description="Nomor HP")
    email: Optional[str] = Field(default=None, description="Email")
    alamat: Optional[str] = Field(default=None, description="Alamat")
    perusahaan: Optional[str] = Field(default=None, description="Nama perusahaan")
    created_at: Optional[str] = Field(default=None, description="Waktu pembuatan")
    updated_at: Optional[str] = Field(default=None, description="Waktu pembaruan")


# ──────────────────────────────────────────────
# Barang
# ──────────────────────────────────────────────


class BarangCreate(BaseModel):
    """Request body untuk membuat barang baru."""

    kode_barang: str = Field(..., min_length=1, description="Kode barang (unik)")
    nama_barang: str = Field(..., min_length=1, description="Nama barang")
    deskripsi_barang: Optional[str] = Field(default=None, description="Deskripsi barang")
    kategori_id: str = Field(..., description="ID kategori barang")
    satuan: str = Field(..., min_length=1, description="Satuan barang (pcs, kg, dll)")
    lokasi_barang: Optional[str] = Field(default=None, description="Lokasi penyimpanan barang")
    stok_awal: int = Field(default=0, ge=0, description="Stok awal barang")
    stok_minimum: int = Field(default=0, ge=0, description="Batas minimum stok")
    foto: Optional[str] = Field(default=None, description="URL foto barang")


class BarangUpdate(BaseModel):
    """Request body untuk memperbarui barang."""

    kode_barang: Optional[str] = Field(default=None, min_length=1, description="Kode barang (unik)")
    nama_barang: Optional[str] = Field(default=None, min_length=1, description="Nama barang")
    deskripsi_barang: Optional[str] = Field(default=None, description="Deskripsi barang")
    kategori_id: Optional[str] = Field(default=None, description="ID kategori barang")
    satuan: Optional[str] = Field(default=None, min_length=1, description="Satuan barang")
    lokasi_barang: Optional[str] = Field(default=None, description="Lokasi penyimpanan barang")
    stok_awal: Optional[int] = Field(default=None, ge=0, description="Stok awal barang")
    stok_minimum: Optional[int] = Field(default=None, ge=0, description="Batas minimum stok")
    foto: Optional[str] = Field(default=None, description="URL foto barang")


class BarangResponse(BaseModel):
    """Response data satu barang."""

    id: str = Field(description="ID barang")
    kode_barang: str = Field(description="Kode barang")
    nama_barang: str = Field(description="Nama barang")
    deskripsi_barang: Optional[str] = Field(default=None, description="Deskripsi barang")
    kategori_id: Optional[str] = Field(default=None, description="ID kategori")
    nama_kategori: Optional[str] = Field(default=None, description="Nama kategori (join)")
    icon_kategori: Optional[str] = Field(default=None, description="Icon kategori (join)")
    satuan: str = Field(description="Satuan barang")
    lokasi_barang: Optional[str] = Field(default=None, description="Lokasi barang")
    stok: int = Field(description="Stok saat ini")
    stok_awal: int = Field(description="Stok awal")
    stok_minimum: int = Field(description="Batas minimum stok")
    harga_satuan: Optional[int] = Field(default=None, description="Harga satuan")
    qrcode: Optional[str] = Field(default=None, description="QR Code")
    barcode: Optional[str] = Field(default=None, description="Barcode")
    foto: Optional[Any] = Field(default=None, description="Data foto barang")
    created_at: Optional[str] = Field(default=None, description="Waktu pembuatan")
    updated_at: Optional[str] = Field(default=None, description="Waktu pembaruan")


class BarangList(BaseModel):
    """Response daftar barang."""

    data: list[dict] = Field(description="Daftar barang")
    total: int = Field(description="Total jumlah barang")


# ──────────────────────────────────────────────
# Detail Item (barang masuk / barang keluar)
# ──────────────────────────────────────────────


class DetailItem(BaseModel):
    """Detail item dalam transaksi masuk/keluar."""

    barang_id: str = Field(..., description="ID barang")
    jumlah: int = Field(..., gt=0, description="Jumlah barang")


class DetailItemResponse(BaseModel):
    """Detail item yang sudah dilengkapi data barang."""

    barang_id: str = Field(description="ID barang")
    kode_barang: str = Field(description="Kode barang")
    nama_barang: str = Field(description="Nama barang")
    satuan: str = Field(description="Satuan barang")
    jumlah: int = Field(description="Jumlah barang")


# ──────────────────────────────────────────────
# Barang Masuk
# ──────────────────────────────────────────────


class BarangMasukCreate(BaseModel):
    """Request body untuk membuat transaksi barang masuk."""

    suplier_id: str = Field(..., description="ID suplier")
    tanggal_masuk: str = Field(..., description="Tanggal masuk (YYYY-MM-DD)")
    nomor_dokumen: str = Field(default="", description="Nomor dokumen referensi")
    no_transaksi: Optional[str] = Field(default=None, description="Nomor transaksi (auto jika kosong)")
    catatan: str = Field(default="", description="Catatan transaksi")
    items: list[DetailItem] = Field(..., min_length=1, description="Daftar item barang masuk")
    user_id: Optional[str] = Field(default=None, description="ID user yang melakukan transaksi")


class BarangMasukUpdate(BaseModel):
    """Request body untuk memperbarui transaksi barang masuk."""

    suplier_id: Optional[str] = Field(default=None, description="ID suplier")
    tanggal_masuk: Optional[str] = Field(default=None, description="Tanggal masuk (YYYY-MM-DD)")
    nomor_dokumen: Optional[str] = Field(default=None, description="Nomor dokumen referensi")
    catatan: Optional[str] = Field(default=None, description="Catatan transaksi")
    items: Optional[list[DetailItem]] = Field(default=None, min_length=1, description="Daftar item barang masuk")
    user_id: Optional[str] = Field(default=None, description="ID user")


class BarangMasukResponse(BaseModel):
    """Response data transaksi barang masuk."""

    id: str = Field(description="ID transaksi")
    no_transaksi: str = Field(description="Nomor transaksi")
    tanggal_masuk: str = Field(description="Tanggal masuk")
    suplier_id: Optional[str] = Field(default=None, description="ID suplier")
    nama_suplier: Optional[str] = Field(default=None, description="Nama suplier (join)")
    perusahaan_suplier: Optional[str] = Field(default=None, description="Perusahaan suplier (join)")
    nomor_dokumen: Optional[str] = Field(default=None, description="Nomor dokumen referensi")
    catatan: Optional[str] = Field(default=None, description="Catatan transaksi")
    user_id: Optional[str] = Field(default=None, description="ID user")
    nama_user: Optional[str] = Field(default=None, description="Nama user (join)")
    detail: list[dict] = Field(description="Daftar item detail")
    item_count: Optional[int] = Field(default=None, description="Jumlah jenis item")
    total_jumlah: Optional[int] = Field(default=None, description="Total jumlah item")
    created_at: Optional[str] = Field(default=None, description="Waktu pembuatan")
    updated_at: Optional[str] = Field(default=None, description="Waktu pembaruan")


# ──────────────────────────────────────────────
# Barang Keluar
# ──────────────────────────────────────────────


class BarangKeluarCreate(BaseModel):
    """Request body untuk membuat transaksi barang keluar."""

    tanggal_keluar: str = Field(..., description="Tanggal keluar (YYYY-MM-DD)")
    tujuan_penerima: str = Field(..., min_length=1, description="Tujuan / nama penerima")
    keperluan: str = Field(default="", description="Keperluan pengambilan barang")
    nomor_dokumen: str = Field(default="", description="Nomor dokumen referensi")
    no_transaksi: Optional[str] = Field(default=None, description="Nomor transaksi (auto jika kosong)")
    catatan: str = Field(default="", description="Catatan transaksi")
    items: list[DetailItem] = Field(..., min_length=1, description="Daftar item barang keluar")
    user_id: Optional[str] = Field(default=None, description="ID user yang melakukan transaksi")


class BarangKeluarUpdate(BaseModel):
    """Request body untuk memperbarui transaksi barang keluar."""

    tanggal_keluar: Optional[str] = Field(default=None, description="Tanggal keluar (YYYY-MM-DD)")
    tujuan_penerima: Optional[str] = Field(default=None, min_length=1, description="Tujuan / nama penerima")
    keperluan: Optional[str] = Field(default=None, description="Keperluan pengambilan barang")
    nomor_dokumen: Optional[str] = Field(default=None, description="Nomor dokumen referensi")
    catatan: Optional[str] = Field(default=None, description="Catatan transaksi")
    items: Optional[list[DetailItem]] = Field(default=None, min_length=1, description="Daftar item barang keluar")
    user_id: Optional[str] = Field(default=None, description="ID user")


class BarangKeluarResponse(BaseModel):
    """Response data transaksi barang keluar."""

    id: str = Field(description="ID transaksi")
    no_transaksi: str = Field(description="Nomor transaksi")
    tanggal_keluar: str = Field(description="Tanggal keluar")
    tujuan_penerima: str = Field(description="Tujuan / penerima")
    keperluan: Optional[str] = Field(default=None, description="Keperluan")
    nomor_dokumen: Optional[str] = Field(default=None, description="Nomor dokumen referensi")
    catatan: Optional[str] = Field(default=None, description="Catatan transaksi")
    user_id: Optional[str] = Field(default=None, description="ID user")
    nama_user: Optional[str] = Field(default=None, description="Nama user (join)")
    detail: list[dict] = Field(description="Daftar item detail")
    item_count: Optional[int] = Field(default=None, description="Jumlah jenis item")
    total_jumlah: Optional[int] = Field(default=None, description="Total jumlah item")
    created_at: Optional[str] = Field(default=None, description="Waktu pembuatan")
    updated_at: Optional[str] = Field(default=None, description="Waktu pembaruan")


# ──────────────────────────────────────────────
# Stok Penyesuaian
# ──────────────────────────────────────────────


class StokPenyesuaianCreate(BaseModel):
    """Request body untuk membuat penyesuaian stok."""

    barang_id: str = Field(..., description="ID barang yang disesuaikan")
    tanggal_penyesuaian: str = Field(..., description="Tanggal penyesuaian (YYYY-MM-DD)")
    stok_fisik: int = Field(..., ge=0, description="Stok fisik hasil penghitungan")
    alasan: str = Field(default="", description="Alasan penyesuaian stok")
    catatan: str = Field(default="", description="Catatan tambahan")
    user_id: Optional[str] = Field(default=None, description="ID user yang melakukan penyesuaian")


class StokPenyesuaianResponse(BaseModel):
    """Response data penyesuaian stok."""

    id: str = Field(description="ID penyesuaian")
    no_penyesuaian: str = Field(description="Nomor penyesuaian")
    tanggal_penyesuaian: str = Field(description="Tanggal penyesuaian")
    barang_id: Optional[str] = Field(default=None, description="ID barang")
    kode_barang: str = Field(description="Kode barang")
    nama_barang: str = Field(description="Nama barang")
    satuan: Optional[str] = Field(default=None, description="Satuan barang")
    stok_sistem: int = Field(description="Stok sistem sebelum penyesuaian")
    stok_fisik: int = Field(description="Stok fisik hasil penghitungan")
    selisih: int = Field(description="Selisih stok (fisik - sistem)")
    jenis: str = Field(description="Jenis penyesuaian: tambah / kurang")
    alasan: Optional[str] = Field(default=None, description="Alasan penyesuaian")
    catatan: Optional[str] = Field(default=None, description="Catatan")
    status: str = Field(description="Status: selesai / dibatalkan")
    user_id: Optional[str] = Field(default=None, description="ID user")
    nama_user: Optional[str] = Field(default=None, description="Nama user (join)")
    dibatalkan_oleh: Optional[str] = Field(default=None, description="ID user yang membatalkan")
    dibatalkan_pada: Optional[str] = Field(default=None, description="Waktu pembatalan")
    catatan_pembatalan: Optional[str] = Field(default=None, description="Catatan pembatalan")
    created_at: Optional[str] = Field(default=None, description="Waktu pembuatan")
    updated_at: Optional[str] = Field(default=None, description="Waktu pembaruan")


# ──────────────────────────────────────────────
# Pengaturan (Setting)
# ──────────────────────────────────────────────


class SettingUpdate(BaseModel):
    """Request body untuk memperbarui pengaturan aplikasi."""

    nama_aplikasi: Optional[str] = Field(default=None, description="Nama aplikasi")
    judul_aplikasi: Optional[str] = Field(default=None, description="Judul aplikasi")
    tagline: Optional[str] = Field(default=None, description="Tagline aplikasi")
    nama_perusahaan: Optional[str] = Field(default=None, description="Nama perusahaan")
    logo: Optional[str] = Field(default=None, description="URL logo")
    favicon: Optional[str] = Field(default=None, description="URL favicon")


class SettingResponse(BaseModel):
    """Response data pengaturan aplikasi."""

    nama_aplikasi: str = Field(description="Nama aplikasi")
    judul_aplikasi: str = Field(description="Judul aplikasi")
    tagline: Optional[str] = Field(default=None, description="Tagline")
    nama_perusahaan: Optional[str] = Field(default=None, description="Nama perusahaan")
    logo: Optional[str] = Field(default=None, description="URL logo")
    favicon: Optional[str] = Field(default=None, description="URL favicon")


# ──────────────────────────────────────────────
# Backup & Restore
# ──────────────────────────────────────────────


class BackupRestoreRequest(BaseModel):
    """Request body untuk restore backup data."""

    data: dict = Field(..., description="Data backup yang akan di-restore (key = nama koleksi, value = list dokumen)")


# ──────────────────────────────────────────────
# Aktivitas (Audit Trail)
# ──────────────────────────────────────────────


class ActivityResponse(BaseModel):
    """Response data satu aktivitas."""

    id: str = Field(description="ID aktivitas")
    user_id: Optional[str] = Field(default=None, description="ID user yang melakukan")
    user_name: Optional[str] = Field(default=None, description="Nama user")
    user_role: Optional[str] = Field(default=None, description="Peran user")
    aksi: str = Field(description="Jenis aksi (create/update/delete)")
    entitas: str = Field(description="Jenis entitas yang diproses")
    entitas_id: Optional[str] = Field(default=None, description="ID entitas")
    deskripsi: str = Field(description="Deskripsi aktivitas")
    detail: Optional[dict] = Field(default=None, description="Detail tambahan")
    ip_address: Optional[str] = Field(default=None, description="Alamat IP")
    created_at: Optional[str] = Field(default=None, description="Waktu aktivitas")


class ActivityList(BaseModel):
    """Response daftar aktivitas dengan pagination."""

    data: list[dict] = Field(description="Daftar aktivitas")
    total: int = Field(description="Total jumlah aktivitas")
    page: int = Field(description="Halaman saat ini")
    per_page: int = Field(description="Item per halaman")
    total_pages: int = Field(description="Total halaman")


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────


class DashboardStats(BaseModel):
    """Statistik ringkasan untuk halaman dashboard."""

    total_barang: int = Field(description="Total jumlah barang")
    total_stok: int = Field(description="Total stok semua barang")
    total_kategori: int = Field(description="Total kategori")
    total_suplier: int = Field(description="Total suplier")
    total_user: int = Field(description="Total user")
    total_staff: int = Field(description="Total user dengan role staff")
    total_masuk: int = Field(description="Total transaksi barang masuk")
    total_keluar: int = Field(description="Total transaksi barang keluar")
    hampir_habis: int = Field(description="Jumlah barang yang stoknya hampir habis")
    stok_kosong: int = Field(description="Jumlah barang yang stoknya kosong")
    barang_masuk_bulan_ini: int = Field(description="Transaksi barang masuk bulan ini")
    qty_barang_masuk_bulan_ini: int = Field(description="Total qty barang masuk bulan ini")
    barang_keluar_bulan_ini: int = Field(description="Transaksi barang keluar bulan ini")
    qty_barang_keluar_bulan_ini: int = Field(description="Total qty barang keluar bulan ini")
    penyesuaian_bulan_ini: int = Field(description="Jumlah penyesuaian stok bulan ini")
    qty_penyesuaian_bulan_ini: int = Field(description="Total selisih penyesuaian bulan ini")
    total_nilai: int = Field(description="Total nilai seluruh stok (harga_satuan x stok)")


# ──────────────────────────────────────────────
# Generic Paginated Response
# ──────────────────────────────────────────────

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Response paginated standar untuk semua list endpoint."""

    data: list[T] = Field(description="Daftar data")
    total: int = Field(description="Total jumlah data")
    page: int = Field(description="Halaman saat ini")
    per_page: int = Field(description="Item per halaman")
    total_pages: int = Field(description="Total halaman")
