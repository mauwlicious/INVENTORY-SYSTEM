# inventory_data.py
# Generator data dummy 150+ item untuk PT ABC Inventory System

import csv
import json
import random
from datetime import datetime, timedelta

CATEGORIES = ["Electronics", "Furniture", "Clothing", "Food & Beverage", "Tools", "Stationary", "Cleaning", "Medical"]

PRODUCT_NAMES = {
    "Electronics": ["Laptop ASUS", "Laptop Lenovo", "Monitor LG", "Monitor Samsung", "Keyboard Mechanical",
                    "Mouse Wireless", "Headset Gaming", "Speaker Bluetooth", "Webcam HD", "Printer Canon",
                    "Printer Epson", "SSD Samsung 1TB", "RAM DDR4 16GB", "USB Hub 7-Port", "HDMI Cable"],
    "Furniture":   ["Kursi Kantor", "Meja Kerja", "Lemari Arsip", "Rak Buku", "Sofa Tunggu",
                    "Meja Meeting", "Kursi Gaming", "Filing Cabinet", "Loker Karyawan", "Whiteboard"],
    "Clothing":    ["Seragam Staff", "Seragam Security", "Rompi Safety", "Helm Safety", "Sepatu Safety",
                    "Sarung Tangan", "Masker N95", "Jas Lab", "Topi Proyek", "Kacamata Safety"],
    "Food & Beverage": ["Kopi Arabika 1kg", "Teh Celup 100pcs", "Gula Pasir 5kg", "Air Mineral 24pcs",
                        "Susu UHT 1L", "Mie Instan 40pcs", "Biskuit Kaleng", "Sirup Marjan", "Kopi Sachet 50pcs", "Teh Botol 24pcs"],
    "Tools":       ["Obeng Set", "Tang Kombinasi", "Kunci Inggris", "Bor Listrik", "Gergaji Besi",
                    "Meteran 5m", "Waterpass", "Palu Besi", "Cutter Besar", "Selotip Double Tape"],
    "Stationary":  ["Kertas HVS A4", "Pulpen Ballpoint", "Spidol Whiteboard", "Stapler Besar", "Penggaris 30cm",
                    "Amplop Coklat", "Map Plastik", "Tinta Printer", "Penghapus", "Binder Clip 50pcs"],
    "Cleaning":    ["Sabun Lantai 5L", "Cairan Pembersih", "Kain Lap Microfiber", "Sapu Lidi", "Kemoceng",
                    "Ember Plastik", "Sikat WC", "Pewangi Ruangan", "Tempat Sampah", "Lap Pel Set"],
    "Medical":     ["Obat P3K Set", "Perban Gulung", "Plester Luka", "Alkohol 70%", "Betadine 30ml",
                    "Sarung Tangan Latex", "Masker Bedah 50pcs", "Termometer Digital", "Tensimeter Digital", "Kapas Gulung"],
}

def generate_item_code(index, category):
    prefix = {
        "Electronics": "ELC", "Furniture": "FRN", "Clothing": "CLT",
        "Food & Beverage": "FNB", "Tools": "TLS", "Stationary": "STN",
        "Cleaning": "CLN", "Medical": "MED"
    }
    return f"{prefix[category]}-{str(index).zfill(4)}"

def random_expiry(category):
    """Hanya kategori tertentu yang punya tanggal kadaluarsa"""
    if category in ["Food & Beverage", "Medical", "Cleaning"]:
        base = datetime.today()
        days = random.randint(-30, 730)  # bisa sudah expired atau belum
        return (base + timedelta(days=days)).strftime("%Y-%m-%d")
    return ""

def generate_data():
    items = []
    index = 1
    for category, names in PRODUCT_NAMES.items():
        for name in names:
            # Buat 1-2 variasi per nama produk
            for variant in range(random.randint(1, 2)):
                suffix = ["", " Pro", " Lite", " XL", " Mini", " Plus"][variant % 6]
                item = {
                    "kode_item": generate_item_code(index, category),
                    "nama_item": name + suffix,
                    "kategori": category,
                    "jumlah": random.randint(1, 200),
                    "harga": round(random.uniform(5000, 15000000) / 500) * 500,
                    "satuan": random.choice(["pcs", "unit", "box", "lusin", "kg", "liter"]),
                    "tanggal_kadaluarsa": random_expiry(category),
                    "lokasi": random.choice(["Gudang A", "Gudang B", "Toko Utama", "Rak C1", "Rak D2"]),
                }
                items.append(item)
                index += 1

    # Pastikan minimal 150 item
    while len(items) < 155:
        cat = random.choice(CATEGORIES)
        names_list = PRODUCT_NAMES[cat]
        name = random.choice(names_list)
        item = {
            "kode_item": generate_item_code(index, cat),
            "nama_item": name + f" Seri-{index}",
            "kategori": cat,
            "jumlah": random.randint(1, 200),
            "harga": round(random.uniform(5000, 15000000) / 500) * 500,
            "satuan": random.choice(["pcs", "unit", "box", "lusin"]),
            "tanggal_kadaluarsa": random_expiry(cat),
            "lokasi": random.choice(["Gudang A", "Gudang B", "Toko Utama"]),
        }
        items.append(item)
        index += 1

    return items

def save_to_csv(items, filepath="inventory.csv"):
    fieldnames = ["kode_item", "nama_item", "kategori", "jumlah", "harga", "satuan", "tanggal_kadaluarsa", "lokasi"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)
    print(f"[OK] Saved {len(items)} items to {filepath}")

def save_to_json(items, filepath="inventory.json"):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved {len(items)} items to {filepath}")

def load_from_csv(filepath="inventory.csv"):
    items = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["jumlah"] = int(row["jumlah"])
                row["harga"] = float(row["harga"])
                items.append(row)
    except FileNotFoundError:
        print(f"[WARN] {filepath} not found, generating fresh data...")
        items = generate_data()
        save_to_csv(items, filepath)
    return items

if __name__ == "__main__":
    data = generate_data()
    save_to_csv(data)
    save_to_json(data)
    print(f"Total items generated: {len(data)}")