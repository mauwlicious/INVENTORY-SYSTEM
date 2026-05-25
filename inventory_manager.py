# inventory_manager.py
import csv
from data_structures import InventoryHashMap, InventoryPriorityQueue
from inventory_data import load_from_csv

class InventoryManager:
    def __init__(self):
        self.hash_map      = InventoryHashMap(initial_capacity=512)
        self.pq_price_min  = InventoryPriorityQueue(mode='harga')
        self.pq_price_max  = InventoryPriorityQueue(mode='harga_max')
        self.pq_expiry     = InventoryPriorityQueue(mode='expired')
        self.pq_expiry.get_all_sorted = self.pq_expiry.to_sorted_list
        self._load_initial_data()

    def _load_initial_data(self):
        items = load_from_csv()
        for item in items:
            item['code']        = item.get('kode_item', '')
            item['name']        = item.get('nama_item', '')
            item['category']    = item.get('kategori', '')
            item['qty']         = item.get('jumlah', 0)
            item['price']       = item.get('harga', 0.0)
            item['expiry_date'] = item.get('tanggal_kadaluarsa', '')
            self.hash_map.put(item['code'], item)
            self.pq_price_min.push(item)
            self.pq_price_max.push(item)
            self.pq_expiry.push(item)

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def add_item(self, item: dict):
        code = item.get('code') or item.get('kode_item')
        self.hash_map.put(code, item)
        self.pq_price_min.push(item)
        self.pq_price_max.push(item)
        self.pq_expiry.push(item)

    def remove_item(self, code: str) -> bool:
        success = self.hash_map.delete(code)
        if success:
            self.pq_price_min.remove_by_code(code)
            self.pq_price_max.remove_by_code(code)
            self.pq_expiry.remove_by_code(code)
        return success

    def get_item(self, code: str) -> dict:
        return self.hash_map.get(code)

    def update_item(self, code: str, updated_data: dict):
        self.remove_item(code)
        updated_data['code'] = code
        self.add_item(updated_data)

    # ── Autosave ──────────────────────────────────────────────────────────────
    def autosave(self, filepath="inventory.csv"):
        """Simpan semua item ke CSV setelah setiap perubahan."""
        fieldnames = ["kode_item", "nama_item", "kategori", "jumlah",
                      "harga", "satuan", "tanggal_kadaluarsa", "lokasi"]
        items = self.hash_map.all_values()
        rows  = []
        for item in items:
            rows.append({
                "kode_item":          item.get("kode_item",  item.get("code", "")),
                "nama_item":          item.get("nama_item",  item.get("name", "")),
                "kategori":           item.get("kategori",   item.get("category", "")),
                "jumlah":             item.get("jumlah",     item.get("qty", 0)),
                "harga":              item.get("harga",      item.get("price", 0.0)),
                "satuan":             item.get("satuan", "pcs"),
                "tanggal_kadaluarsa": item.get("tanggal_kadaluarsa",
                                               item.get("expiry_date", "")),
                "lokasi":             item.get("lokasi", item.get("store", "")),
            })
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        except Exception as e:
            print(f"[WARN] Autosave failed: {e}")

    # ── Stats ──────────────────────────────────────────────────────────────────
    def get_stats(self) -> dict:
        from datetime import date, datetime
        all_items   = self.hash_map.all_values()
        total       = len(all_items)
        total_value = sum(i.get('price', 0) * i.get('qty', 0) for i in all_items)
        total_qty   = sum(i.get('qty', 0) for i in all_items)
        today       = date.today()
        near_expiry = expired = 0
        for item in all_items:
            try:
                exp_str = item.get('expiry_date', '')
                if not exp_str: continue
                exp   = datetime.strptime(exp_str, "%Y-%m-%d").date()
                delta = (exp - today).days
                if delta < 0:        expired     += 1
                elif delta <= 180:   near_expiry += 1
            except Exception: pass
        categories = {}
        for item in all_items:
            cat = item.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        top_cat = max(categories, key=categories.get) if categories else "—"
        top5    = self.pq_price_max.to_sorted_list()[:5]
        return {
            'total_items':        total,
            'total_value':        total_value,
            'total_qty':          total_qty,
            'near_expiry':        near_expiry,
            'expired':            expired,
            'top_category':       top_cat,
            'top_category_count': categories.get(top_cat, 0),
            'top5_expensive':     top5,
            'categories':         categories,
        }