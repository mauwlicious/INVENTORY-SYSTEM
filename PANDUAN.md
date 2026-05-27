# PANDUAN APLIKASI PT ABC INVENTORY SYSTEM
## Tugas Besar Struktur Data — Institut Teknologi Bacharuddin Jusuf Habibie

---

## DAFTAR ISI
1. [Struktur File Proyek](#1-struktur-file-proyek)
2. [Cara Menjalankan Aplikasi](#2-cara-menjalankan-aplikasi)
3. [Fitur-Fitur Aplikasi](#3-fitur-fitur-aplikasi)
4. [Struktur Data yang Digunakan](#4-struktur-data-yang-digunakan)
5. [Panduan Kustomisasi](#5-panduan-kustomisasi)
6. [Panduan Penggunaan per Halaman](#6-panduan-penggunaan-per-halaman)
7. [Antisipasi Pertanyaan Presentasi](#7-antisipasi-pertanyaan-presentasi)

---

## 1. Struktur File Proyek

```
part4/
├── main.py                  # Entry point — jalankan file ini
├── inventory_manager.py     # Controller utama: mengelola semua struktur data
├── sales_manager.py         # Controller penjualan
├── data_structures.py       # Implementasi HashMap, PriorityQueue, Sorter
├── inventory_data.py        # Generator & loader data CSV
├── inventory.csv            # Data barang (auto-generate jika tidak ada)
├── sales.csv                # Riwayat penjualan (auto-create)
├── _env.txt                 # Daftar user (email & password)
├── .remember.json           # Data Remember Me (auto-create)
└── screens/
    ├── __init__.py
    ├── login_screen.py      # Halaman login
    ├── index_screen.py      # Navigasi sidebar
    ├── dashboard_screen.py  # Halaman dashboard
    ├── items_screen.py      # Halaman kelola barang
    ├── sales_screen.py      # Halaman penjualan
    ├── priority_screen.py   # Halaman priority queue
    └── search_screen.py     # Halaman pencarian
```

---

## 2. Cara Menjalankan Aplikasi

### Prasyarat
```bash
pip install customtkinter
```

### Menjalankan
```bash
cd part4
python main.py
```

### Format _env.txt (Multi-User)
```
# Tambah user baru dengan menambahkan pasangan USER_EMAIL + USER_PASSWORD
USER_EMAIL=admin@mail.com
USER_PASSWORD=rahasia123
USER_EMAIL=manajer@mail.com
USER_PASSWORD=manajer456
USER_EMAIL=staff@mail.com
USER_PASSWORD=staff789
```

---

## 3. Fitur-Fitur Aplikasi

### A. Login Multi-User dengan Remember Me
- Mendukung lebih dari 1 akun pengguna dari file `_env.txt`
- Fitur "Remember Me": jika dicentang, email & password tersimpan ke `.remember.json`
- Saat aplikasi dibuka kembali, form otomatis terisi — tinggal klik Login
- Jika tidak dicentang, form kosong setiap kali buka aplikasi

### B. Dashboard
- Menampilkan 4 KPI card: Total Items, Total Stock, Inventory Value, Near Expiry
- Tabel Top 5 Barang Termahal (dari Priority Queue Max-Price)
- Tabel 5 Barang Mendekati Kadaluarsa (dari Priority Queue Expiry)
- Chart distribusi barang per kategori

### C. Items (Kelola Barang)
- Tampilkan semua barang dalam tabel dengan pagination (10 baris/halaman)
- Filter: search by code, search by name, sort, filter kategori
- Action per baris: **✏ Edit**, **📋 Details**, **🗑 Delete**
- **Add Item**: form dengan validasi lengkap, kategori dropdown
- Perubahan otomatis tersimpan ke `inventory.csv` (autosave)

### D. Sales (Penjualan)
- **Catat Penjualan**: cari barang → tambah ke keranjang → atur qty → proses
- Saat diproses: stok inventory otomatis berkurang, transaksi tersimpan ke `sales.csv`
- **Riwayat & Statistik**: total transaksi, total revenue, item terlaris, riwayat transaksi

### E. Priority Queue
- 3 mode: Cheapest (min-price), Costliest (max-price), Soonest Expiry
- Pagination 10 baris/halaman
- Action: **✏ Edit**, **📋 Details**, **Pop** (hapus dari antrian)
- **Pop Top**: ambil item prioritas tertinggi dari antrian

### F. Search
- Ketik kode item → pencarian O(1) via Hash Map (langsung ketemu jika kode tepat)
- Partial search O(N): ketik sebagian kode, tampilkan semua yang cocok
- Pada hasil exact match: tersedia tombol **Edit** dan **Details**

---

## 4. Struktur Data yang Digunakan

### 4.1 Hash Map (InventoryHashMap)
**Lokasi**: `data_structures.py`

**Apa itu?**
Hash Map adalah struktur data yang menyimpan pasangan key-value. Pencarian data dilakukan dengan menghitung `hash(key) % capacity` untuk langsung menuju slot penyimpanan.

**Kompleksitas**:
- `put(key, value)` → O(1) rata-rata
- `get(key)` → O(1) rata-rata
- `delete(key)` → O(1) rata-rata

**Digunakan untuk**: Menyimpan seluruh data barang inventory dengan kode barang sebagai key.

**Cara menjelaskan ke dosen**:
> "HashMap kami implementasikan dengan teknik chaining untuk menangani collision. Ketika kita mencari barang dengan kode ELC-0001, HashMap langsung menghitung posisi slot tanpa perlu loop seluruh data. Ini yang menyebabkan fitur Search kami bekerja dalam waktu konstan O(1)."

**Contoh di kode**:
```python
# Simpan barang
self.hash_map.put("ELC-0001", item_dict)

# Ambil barang — O(1)
item = self.hash_map.get("ELC-0001")
```

---

### 4.2 Priority Queue (InventoryPriorityQueue)
**Lokasi**: `data_structures.py`

**Apa itu?**
Priority Queue adalah antrian di mana setiap elemen punya prioritas. Elemen dengan prioritas tertinggi selalu berada di posisi terdepan (top). Implementasi kami menggunakan Binary Heap.

**Kompleksitas**:
- `push(item)` → O(log n)
- `pop()` → O(log n) — ambil item prioritas tertinggi
- `peek()` → O(1) — lihat item teratas tanpa mengambil

**Tiga instance digunakan**:
1. `pq_price_min` → Min-Heap berdasarkan harga (barang termurah di atas)
2. `pq_price_max` → Max-Heap berdasarkan harga (barang termahal di atas)
3. `pq_expiry` → Min-Heap berdasarkan tanggal kadaluarsa (paling dekat di atas)

**Cara menjelaskan ke dosen**:
> "Priority Queue kami gunakan untuk secara efisien mengetahui barang mana yang paling murah, paling mahal, atau paling mendekati kadaluarsa. Tanpa Priority Queue, kita harus sort seluruh data setiap kali ingin tahu informasi ini — O(n log n). Dengan Priority Queue, kita langsung tahu O(1) untuk peek, dan O(log n) untuk pop."

---

### 4.3 Merge Sort (InventorySorter)
**Lokasi**: `data_structures.py`

**Apa itu?**
Merge Sort adalah algoritma pengurutan berbasis divide and conquer. Array dibagi dua secara rekursif hingga ukuran 1, kemudian digabungkan dengan urutan yang benar.

**Kompleksitas**: O(n log n) untuk semua kasus (best, average, worst)

**Digunakan untuk**: Fitur sort di halaman Items (sort by name, price)

**Cara menjelaskan ke dosen**:
> "Kami memilih Merge Sort karena kompleksitasnya O(n log n) yang stabil di semua kondisi, berbeda dengan Quick Sort yang bisa O(n²) di worst case. Dengan 155 item, perbedaannya tidak terasa, tapi secara konsep ini pilihan yang lebih tepat untuk data inventory yang terus bertambah."

---

### 4.4 Struktur Data Python Bawaan yang Digunakan

| Struktur Data | Digunakan di | Kegunaan |
|---|---|---|
| **List** | `sales_manager.py`, `inventory_data.py` | Menyimpan list transaksi, list item |
| **Dict** | Semua file | Menyimpan data per item (key-value) |
| **Tuple** | `items_screen.py` | Konstanta COL_HEADERS & COL_WIDTHS |
| **Set** | `data_structures.py` | Menghindari duplikasi di chaining |
| **CSV (text file)** | `inventory.csv`, `sales.csv` | Penyimpanan persisten data |

---

## 5. Panduan Kustomisasi

### A. Menambah/Mengubah User
Edit file `_env.txt`:
```
# Ganti password admin
USER_EMAIL=admin@mail.com
USER_PASSWORD=password_baru

# Tambah user baru
USER_EMAIL=direktur@mail.com
USER_PASSWORD=direktur2024
```

### B. Mengubah Warna Tema Aplikasi
Buka file yang ingin diubah, cari konstanta warna di bagian atas:
```python
# Contoh di items_screen.py
PRIMARY  = "#1E61B8"   # ← Ubah ini untuk warna utama (tombol, header, dll)
TEXT_SEC = "#7A8A9A"   # ← Warna teks sekunder (label, subtitle)
RED      = "#D92626"   # ← Warna untuk aksi berbahaya (hapus, error)
GREEN    = "#1A9A4A"   # ← Warna sukses
```

### C. Mengubah Jumlah Baris per Halaman
```python
# Di items_screen.py dan priority_screen.py
ROWS_PER_PAGE = 10    # ← Ubah angka ini (contoh: 20 untuk 20 baris)
```

### D. Menambah Kategori Barang
```python
# Di items_screen.py, cari variabel CATEGORIES
CATEGORIES = ["Electronics", "Furniture", "Clothing", "Food & Beverage",
              "Tools", "Stationary", "Cleaning", "Medical",
              "Kategori Baru"]   # ← Tambahkan di sini
```

### E. Mengubah Nama Perusahaan
```python
# Di main.py
self.title("PT ABC — Inventory System")   # ← Judul window

# Di login_screen.py
ctk.CTkLabel(left, text="PT ABC Inventory", ...)   # ← Nama di halaman login
```

### F. Mengubah Lebar Kolom Tabel
```python
# Di items_screen.py
COL_W = {"CODE":105, "NAME":0, "CATEGORY":155, "QTY":60,
         "PRICE":125, "EXPIRY":105, "ACTIONS":165}
# Nilai 0 pada NAME berarti kolom ini mengisi sisa ruang
# Ubah angka untuk memperlebar/mempersempit kolom
```

### G. Menambah Field Barang Baru
Perlu edit 3 tempat:
1. `inventory_data.py` — tambah key di `save_to_csv()` dan `fieldnames`
2. `items_screen.py` — tambah field di form Add/Edit dan kolom tabel
3. `inventory_manager.py` — tambah mapping key di `autosave()`

---

## 6. Panduan Penggunaan per Halaman

### Login
1. Masukkan email dan password sesuai `_env.txt`
2. Centang "Remember Me" agar tidak perlu isi ulang saat buka aplikasi
3. Tekan Enter atau klik tombol Login

### Dashboard
- Buka otomatis setelah login
- Data diperbarui setiap kali halaman dibuka
- Klik menu lain di sidebar untuk navigasi

### Items — Tambah Barang
1. Klik tombol **+ Add Item** (kanan atas)
2. Isi semua field yang bertanda `*`
3. Pilih kategori dari dropdown
4. Klik **Simpan** → barang otomatis tersimpan ke `inventory.csv`

### Items — Edit Barang
1. Cari barang di tabel
2. Klik tombol **✏** (biru) di kolom Actions
3. Ubah field yang diperlukan
4. Klik **Simpan Perubahan**

### Sales — Catat Penjualan
1. Buka halaman **Sales** dari sidebar
2. Cari barang di kolom kiri, klik **+** untuk tambah ke keranjang
3. Atur qty di keranjang menggunakan tombol **+/-**
4. Klik **✅ Proses** → konfirmasi → stok otomatis berkurang

### Priority Queue — Pop Item
1. Pilih mode (Cheapest / Costliest / Soonest Expiry)
2. Klik **⬆ Pop Top** untuk mengambil item prioritas tertinggi dari antrian
3. Atau klik tombol **Pop** di baris tertentu untuk pop item spesifik

### Search
1. Ketik kode lengkap untuk pencarian O(1) exact match
2. Ketik sebagian kode (misal "ELC") untuk partial search O(N)
3. Pada hasil exact match, klik **✏ Edit** atau **📋 Details**

---

## 7. Antisipasi Pertanyaan Presentasi

### Q: "Mengapa menggunakan HashMap bukan List biasa untuk menyimpan inventory?"
**A**: "Dengan List, pencarian barang berdasarkan kode membutuhkan O(n) karena harus loop semua elemen. Dengan HashMap, pencarian langsung ke slot memori yang dihitung dari hash kode, sehingga O(1). Untuk inventory dengan 155+ item yang terus bertambah, ini sangat signifikan — jika ada 10.000 item, List butuh 10.000 operasi, HashMap tetap ~1 operasi."

### Q: "Bagaimana cara kerja Priority Queue di aplikasi ini?"
**A**: "Kami menggunakan Binary Min/Max Heap. Saat barang baru ditambahkan (push), barang ditempatkan di akhir heap lalu di-heapify-up — membandingkan dengan parent dan menukar jika prioritasnya lebih tinggi. Kompleksitas O(log n). Saat pop, item teratas diambil, posisi terakhir dipindah ke atas, lalu di-heapify-down. Ini memastikan item prioritas tertinggi selalu di posisi paling atas."

### Q: "Apa bedanya 3 Priority Queue yang digunakan?"
**A**: "Kami punya 3 instance: (1) `pq_price_min` menggunakan Min-Heap berdasarkan harga — cocok untuk mengetahui barang termurah; (2) `pq_price_max` menggunakan Max-Heap berdasarkan harga — untuk barang termahal; (3) `pq_expiry` menggunakan Min-Heap berdasarkan tanggal kadaluarsa — untuk mendeteksi barang yang segera kadaluarsa. Ketiganya di-update bersamaan setiap ada perubahan inventory."

### Q: "Mengapa data disimpan ke CSV bukan database?"
**A**: "Untuk keperluan proyek ini, CSV sudah memenuhi kebutuhan dan lebih mudah diportabilitas — tidak perlu install database server. Jika ingin upgrade ke production, kita bisa ganti bagian `autosave()` di `inventory_manager.py` dan `_save_sales()` di `sales_manager.py` untuk terhubung ke SQLite atau PostgreSQL tanpa mengubah logika aplikasi lainnya."

### Q: "Bagaimana cara menambah fitur baru, misalnya laporan bulanan?"
**A**: "Kami memisahkan logika (manager) dari tampilan (screen). Untuk laporan bulanan, cukup: (1) tambah method `get_monthly_report(month, year)` di `sales_manager.py` yang filter data berdasarkan kolom 'date'; (2) buat file `report_screen.py` yang memanggil method tersebut; (3) daftarkan di `index_screen.py` sebagai nav baru. Tidak perlu mengubah file lain."

### Q: "Apakah ada penanganan error jika file CSV tidak ditemukan?"
**A**: "Ya, di `inventory_data.py` fungsi `load_from_csv()` sudah ada try-except. Jika file tidak ditemukan, program otomatis generate 155+ data dummy menggunakan `generate_data()`. Di `sales_manager.py`, jika `sales.csv` tidak ada, `_load_sales()` langsung return list kosong. Jadi program tetap bisa berjalan meski file tidak ada."

### Q: "Apa yang terjadi jika dua user login bersamaan dengan Remember Me?"
**A**: "Saat ini aplikasi didesain untuk single-session (dijalankan satu instance). File `.remember.json` hanya menyimpan 1 sesi terakhir, jadi jika user A login dengan remember, lalu user B login dengan remember, file akan berisi data user B. Untuk multi-session, perlu modifikasi agar `.remember.json` menyimpan array sesi."

### Q: "Bagaimana kompleksitas waktu keseluruhan saat load awal aplikasi?"
**A**: "Saat startup, `_load_initial_data()` di `inventory_manager.py` melakukan: (1) baca CSV O(n); (2) untuk setiap item, `hash_map.put()` O(1) amortized; (3) `pq.push()` untuk 3 priority queue masing-masing O(log n). Total: O(n log n). Untuk 155 item ini sangat cepat, tapi konsepnya scalable."

### Q: "Mengapa menggunakan Merge Sort bukan built-in sort Python?"
**A**: "Built-in sort Python (Timsort) sebenarnya sangat baik — O(n log n) juga. Kami menggunakan Merge Sort karena tujuan akademis: untuk mendemonstrasikan implementasi algoritma sorting secara eksplisit. Dalam konteks tugas Struktur Data, lebih baik menunjukkan bahwa kita memahami cara kerja algoritma sorting."

---

## STRUKTUR DATA — RINGKASAN UNTUK PRESENTASI

| Struktur Data | Diimplementasikan di | Kompleksitas Utama | Fungsi dalam Aplikasi |
|---|---|---|---|
| **Hash Map** | `data_structures.py` | O(1) get/put | Penyimpanan & pencarian inventory |
| **Min-Heap PQ** | `data_structures.py` | O(log n) push/pop | Barang termurah, terdekat kadaluarsa |
| **Max-Heap PQ** | `data_structures.py` | O(log n) push/pop | Barang termahal |
| **Merge Sort** | `data_structures.py` | O(n log n) | Sort tampilan tabel |
| **List** | `sales_manager.py` | O(1) append, O(n) search | Riwayat penjualan |
| **Dictionary** | Semua file | O(1) akses | Data per item/transaksi |
| **CSV (Text File)** | `inventory.csv`, `sales.csv` | O(n) read/write | Persistensi data |

---

*Dokumen ini dibuat untuk mendukung presentasi Tugas Besar Struktur Data*  
*Institut Teknologi Bacharuddin Jusuf Habibie — Program Studi Ilmu Komputer*