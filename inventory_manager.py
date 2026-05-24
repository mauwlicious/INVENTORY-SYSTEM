# inventory_manager.py
# Controller pusat yang mengelola semua struktur data inventory

from data_structures import InventoryHashMap, InventoryPriorityQueue
from inventory_data import load_from_csv

class InventoryManager:
    """
    Manajer Inventory PT ABC — menggabungkan:
    - HashMap   : penyimpanan utama + pencarian O(1) by kode
    - PriorityQueue (3x): min-price, max-price, soonest-expiry
    """

    def __init__(self):
        # --- Struktur Data Utama ---
        # Parameter diubah dari capacity -> initial_capacity
        self.hash_map = InventoryHashMap(initial_capacity=512)

        # --- Priority Queues ---
        # Mode disesuaikan dengan yang ada di data_structures.py
        self.pq_price_min  = InventoryPriorityQueue(mode='harga')
        self.pq_price_max  = InventoryPriorityQueue(mode='harga_max')
        self.pq_expiry     = InventoryPriorityQueue(mode='expired')

        # Patch (Alias) metode agar kompatibel dengan pemanggilan UI index.py
        self.pq_expiry.get_all_sorted = self.pq_expiry.to_sorted_list

        # Muat data awal
        self._load_initial_data()

    def _load_initial_data(self):
        # Memanggil fungsi yang benar dari inventory_data.py
        items = load_from_csv()
        for item in items:
            # SUNTIK KEY BAHASA INGGRIS
            # UI (index.py) butuh 'code' dan 'price', sedangkan
            # Struktur Data butuh 'kode_item' dan 'harga'. Kita simpan keduanya.
            item['code'] = item.get('kode_item', '')
            item['name'] = item.get('nama_item', '')
            item['category'] = item.get('kategori', '')
            item['qty'] = item.get('jumlah', 0)
            item['price'] = item.get('harga', 0.0)
            item['expiry_date'] = item.get('tanggal_kadaluarsa', '')
            
            # Insert ke Data Structures
            self.hash_map.put(item['code'], item)
            self.pq_price_min.push(item)
            self.pq_price_max.push(item)
            self.pq_expiry.push(item)

    # ---------------------------------------------------------------
    # CRUD Operations
    # ---------------------------------------------------------------

    def add_item(self, item: dict):
        """Tambah item baru ke semua struktur data"""
        code = item.get('code') or item.get('kode_item')
        self.hash_map.put(code, item)
        self.pq_price_min.push(item)
        self.pq_price_max.push(item)
        self.pq_expiry.push(item)

    def remove_item(self, code: str) -> bool:
        """Hapus item dari semua struktur data"""
        success = self.hash_map.delete(code)
        if success:
            self.pq_price_min.remove_by_code(code)
            self.pq_price_max.remove_by_code(code)
            self.pq_expiry.remove_by_code(code)
        return success

    def get_item(self, code: str) -> dict:
        """Cari item by kode — O(1)"""
        return self.hash_map.get(code)

    def update_item(self, code: str, updated_data: dict):
        """Update item — remove lama, insert baru"""
        self.remove_item(code)
        updated_data['code'] = code
        self.add_item(updated_data)

    # ---------------------------------------------------------------
    # Stats untuk Dashboard
    # ---------------------------------------------------------------

    def get_stats(self) -> dict:
        from datetime import date, datetime
        
        # Method di hashmap adalah all_values(), bukan all_items()
        all_items = self.hash_map.all_values()
        total = len(all_items)
        total_value = sum(i.get('price', 0) * i.get('qty', 0) for i in all_items)
        total_qty = sum(i.get('qty', 0) for i in all_items)

        today = date.today()
        near_expiry = 0
        expired = 0
        for item in all_items:
            try:
                exp_str = item.get('expiry_date', '')
                if not exp_str:
                    continue
                exp = datetime.strptime(exp_str, "%Y-%m-%d").date()
                delta = (exp - today).days
                if delta < 0:
                    expired += 1
                elif delta <= 180:
                    near_expiry += 1
            except Exception:
                pass

        categories = {}
        for item in all_items:
            cat = item.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1

        top_cat = max(categories, key=categories.get) if categories else "—"

        # Method di PQ adalah to_sorted_list(), bukan get_all_sorted()
        top5 = self.pq_price_max.to_sorted_list()[:5]

        return {
            'total_items': total,
            'total_value': total_value,
            'total_qty': total_qty,
            'near_expiry': near_expiry,
            'expired': expired,
            'top_category': top_cat,
            'top_category_count': categories.get(top_cat, 0),
            'top5_expensive': top5,
            'categories': categories,
        }