"""Dokumen MongoDB yang digunakan aplikasi."""
from pymongo.collection import Collection
from config.database import collection


def users() -> Collection:
    return collection("users")


def kategori() -> Collection:
    return collection("kategori")


def barang() -> Collection:
    return collection("barang")


def suplier() -> Collection:
    return collection("suplier")


def barang_masuk() -> Collection:
    return collection("barang_masuk")


def barang_keluar() -> Collection:
    return collection("barang_keluar")


def stok_penyesuaian() -> Collection:
    return collection("stok_penyesuaian")


def setting() -> Collection:
    return collection("setting")


def aktivitas() -> Collection:
    return collection("aktivitas")


def riwayat_stok() -> Collection:
    return collection("riwayat_stok")
