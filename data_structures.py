# data_structures.py
# Implementasi struktur data untuk PT ABC Inventory System
# 1. HashMap   - pencarian O(1) berdasarkan kode_item
# 2. MergeSort - sorting nama dan harga
# 3. MinHeap   - priority queue berdasarkan harga atau tanggal kadaluarsa

import heapq
from datetime import datetime


# ─────────────────────────────────────────────────────────────────
# 1. HASH MAP  –  pencarian O(1) dengan kode_item sebagai kunci
# ─────────────────────────────────────────────────────────────────

class InventoryHashMap:
    """
    Custom Hash Map menggunakan separate chaining untuk collision handling.
    Kunci: kode_item (str)  →  Nilai: dict item
    """

    def __init__(self, initial_capacity=256):
        self._capacity = initial_capacity
        self._buckets  = [[] for _ in range(self._capacity)]
        self._size     = 0
        self._load_factor_threshold = 0.75

    # ── private ──────────────────────────────────────────────────
    def _hash(self, key: str) -> int:
        """Polynomial rolling hash"""
        h, base, mod = 0, 31, self._capacity
        for ch in key:
            h = (h * base + ord(ch)) % mod
        return h

    def _resize(self):
        old_buckets    = self._buckets
        self._capacity *= 2
        self._buckets  = [[] for _ in range(self._capacity)]
        self._size     = 0
        for bucket in old_buckets:
            for k, v in bucket:
                self.put(k, v)

    # ── public ───────────────────────────────────────────────────
    def put(self, key: str, value: dict):
        if self._size / self._capacity >= self._load_factor_threshold:
            self._resize()
        idx    = self._hash(key)
        bucket = self._buckets[idx]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return
        bucket.append((key, value))
        self._size += 1

    def get(self, key: str):
        """Kembalikan item dict atau None"""
        idx = self._hash(key)
        for k, v in self._buckets[idx]:
            if k == key:
                return v
        return None

    def delete(self, key: str) -> bool:
        idx    = self._hash(key)
        bucket = self._buckets[idx]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self._size -= 1
                return True
        return False

    def contains(self, key: str) -> bool:
        return self.get(key) is not None

    def all_values(self) -> list:
        result = []
        for bucket in self._buckets:
            for _, v in bucket:
                result.append(v)
        return result

    def all_keys(self) -> list:
        result = []
        for bucket in self._buckets:
            for k, _ in bucket:
                result.append(k)
        return result

    def search_prefix(self, prefix: str) -> list:
        """Cari semua item yang kode_item-nya diawali prefix (untuk autocomplete)"""
        prefix = prefix.upper()
        return [v for k, v in
                ((k, v) for bucket in self._buckets for k, v in bucket)
                if k.startswith(prefix)]

    def __len__(self):
        return self._size

    def __repr__(self):
        return f"InventoryHashMap(size={self._size}, capacity={self._capacity})"


# ─────────────────────────────────────────────────────────────────
# 2. MERGE SORT  –  sorting stabil berdasarkan nama / harga
# ─────────────────────────────────────────────────────────────────

class InventorySorter:
    """
    Implementasi Merge Sort O(n log n) untuk mengurutkan list item.
    Mendukung multi-key dan arah asc/desc.
    """

    @staticmethod
    def _merge(left: list, right: list, key_fn, reverse: bool) -> list:
        result, i, j = [], 0, 0
        while i < len(left) and j < len(right):
            lv, rv = key_fn(left[i]), key_fn(right[j])
            # perbandingan string case-insensitive
            if isinstance(lv, str):
                lv, rv = lv.lower(), rv.lower()
            cond = lv > rv if reverse else lv <= rv
            if cond:
                result.append(left[i]); i += 1
            else:
                result.append(right[j]); j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    @classmethod
    def sort(cls, items: list, key: str = "nama_item", reverse: bool = False) -> list:
        """
        key: 'nama_item' | 'harga' | 'jumlah' | 'kode_item'
        """
        if len(items) <= 1:
            return items[:]

        valid_keys = {"nama_item", "harga", "jumlah", "kode_item", "kategori"}
        if key not in valid_keys:
            raise ValueError(f"Sort key '{key}' tidak valid. Pilih: {valid_keys}")

        key_fn = lambda item: item.get(key, "")

        def _merge_sort(arr):
            if len(arr) <= 1:
                return arr
            mid   = len(arr) // 2
            left  = _merge_sort(arr[:mid])
            right = _merge_sort(arr[mid:])
            return cls._merge(left, right, key_fn, reverse)

        return _merge_sort(items)

    @staticmethod
    def sort_multi(items: list, keys: list) -> list:
        """
        Sort berdasarkan banyak kunci sekaligus, menggunakan Python built-in timsort.
        keys contoh: [('harga', False), ('nama_item', True)]
        """
        result = items[:]
        for key, reverse in reversed(keys):
            result.sort(
                key=lambda x: (x.get(key) or "").lower()
                              if isinstance(x.get(key), str) else x.get(key, 0),
                reverse=reverse
            )
        return result


# ─────────────────────────────────────────────────────────────────
# 3. PRIORITY QUEUE (MIN-HEAP)  –  berdasarkan harga / expired
# ─────────────────────────────────────────────────────────────────

class InventoryPriorityQueue:
    """
    Priority Queue berbasis heap.
    mode='harga'    → prioritas = harga terendah (barang murah muncul duluan)
    mode='expired'  → prioritas = tanggal kadaluarsa paling dekat
    mode='harga_max'→ prioritas = harga tertinggi (max-heap via negasi)
    """

    FUTURE_DATE = "9999-12-31"

    def __init__(self, mode: str = "harga"):
        if mode not in ("harga", "harga_max", "expired"):
            raise ValueError("mode harus 'harga', 'harga_max', atau 'expired'")
        self._heap   = []
        self._mode   = mode
        self._counter = 0   # tiebreaker agar item dict bisa dibandingkan

    def _priority(self, item: dict):
        if self._mode == "harga":
            return float(item.get("harga", 0))
        if self._mode == "harga_max":
            return -float(item.get("harga", 0))
        # mode = expired
        exp = item.get("tanggal_kadaluarsa", "") or self.FUTURE_DATE
        try:
            return datetime.strptime(exp, "%Y-%m-%d")
        except ValueError:
            return datetime.strptime(self.FUTURE_DATE, "%Y-%m-%d")

    def push(self, item: dict):
        priority = self._priority(item)
        heapq.heappush(self._heap, (priority, self._counter, item))
        self._counter += 1

    def pop(self) -> dict:
        if not self._heap:
            raise IndexError("Priority queue kosong")
        _, _, item = heapq.heappop(self._heap)
        return item

    def peek(self) -> dict:
        if not self._heap:
            return None
        return self._heap[0][2]

    def push_all(self, items: list):
        for item in items:
            self.push(item)

    def pop_all_sorted(self) -> list:
        """Kembalikan semua item dalam urutan prioritas (mengosongkan queue)"""
        result = []
        while self._heap:
            result.append(self.pop())
        return result

    def to_sorted_list(self) -> list:
        """Kembalikan snapshot terurut tanpa mengosongkan queue"""
        snapshot = list(self._heap)
        snapshot.sort(key=lambda x: x[0])
        return [item for _, _, item in snapshot]

    def remove_by_code(self, kode_item: str) -> bool:
        """Hapus item berdasarkan kode, lalu heapify ulang"""
        before = len(self._heap)
        self._heap = [(p, c, it) for p, c, it in self._heap
                      if it.get("kode_item") != kode_item]
        if len(self._heap) < before:
            heapq.heapify(self._heap)
            return True
        return False

    def update_item(self, kode_item: str, updated_item: dict) -> bool:
        """Update item dalam queue"""
        removed = self.remove_by_code(kode_item)
        if removed:
            self.push(updated_item)
        return removed

    def __len__(self):
        return len(self._heap)

    def __repr__(self):
        return f"InventoryPriorityQueue(mode='{self._mode}', size={len(self._heap)})"


# ─────────────────────────────────────────────────────────────────
# 4. INVENTORY MANAGER  –  façade yang menyatukan semua struktur
# ─────────────────────────────────────────────────────────────────

class InventoryManager:
    """
    Façade tunggal untuk semua operasi inventory.
    Menjaga konsistensi antara HashMap, Sorter, dan PriorityQueue.
    """

    def __init__(self):
        self.hashmap     = InventoryHashMap()
        self.sorter      = InventorySorter()
        self.pq_harga    = InventoryPriorityQueue(mode="harga")
        self.pq_expired  = InventoryPriorityQueue(mode="expired")
        self._loaded     = False

    # ── Load / Init ──────────────────────────────────────────────
    def load_items(self, items: list):
        self.hashmap     = InventoryHashMap()
        self.pq_harga    = InventoryPriorityQueue(mode="harga")
        self.pq_expired  = InventoryPriorityQueue(mode="expired")
        for item in items:
            self.hashmap.put(item["kode_item"], item)
            self.pq_harga.push(item)
            if item.get("tanggal_kadaluarsa"):
                self.pq_expired.push(item)
        self._loaded = True
        print(f"[InventoryManager] Loaded {len(items)} items.")

    # ── CRUD ─────────────────────────────────────────────────────
    def add_item(self, item: dict) -> bool:
        if self.hashmap.contains(item["kode_item"]):
            return False   # kode duplikat
        self.hashmap.put(item["kode_item"], item)
        self.pq_harga.push(item)
        if item.get("tanggal_kadaluarsa"):
            self.pq_expired.push(item)
        return True

    def update_item(self, kode_item: str, updated: dict) -> bool:
        if not self.hashmap.contains(kode_item):
            return False
        self.hashmap.put(kode_item, updated)
        self.pq_harga.update_item(kode_item, updated)
        self.pq_expired.update_item(kode_item, updated)
        return True

    def delete_item(self, kode_item: str) -> bool:
        if not self.hashmap.delete(kode_item):
            return False
        self.pq_harga.remove_by_code(kode_item)
        self.pq_expired.remove_by_code(kode_item)
        return True

    # ── Search ───────────────────────────────────────────────────
    def search_by_code(self, kode: str) -> dict:
        return self.hashmap.get(kode.upper().strip())

    def search_prefix(self, prefix: str) -> list:
        return self.hashmap.search_prefix(prefix)

    def get_all_items(self) -> list:
        return self.hashmap.all_values()

    # ── Sort ─────────────────────────────────────────────────────
    def get_sorted(self, key: str = "nama_item", reverse: bool = False) -> list:
        return self.sorter.sort(self.get_all_items(), key=key, reverse=reverse)

    # ── Priority Queue Views ──────────────────────────────────────
    def get_by_price_priority(self, top_n: int = None, cheapest: bool = True) -> list:
        if cheapest:
            result = self.pq_harga.to_sorted_list()
        else:
            tmp = InventoryPriorityQueue(mode="harga_max")
            tmp.push_all(self.get_all_items())
            result = tmp.to_sorted_list()
        return result[:top_n] if top_n else result

    def get_by_expiry_priority(self, top_n: int = None) -> list:
        result = self.pq_expired.to_sorted_list()
        return result[:top_n] if top_n else result

    def get_expiring_soon(self, days: int = 30) -> list:
        """Item yang kadaluarsa dalam `days` hari ke depan"""
        cutoff = datetime.today() + __import__('datetime').timedelta(days=days)
        result = []
        for item in self.pq_expired.to_sorted_list():
            exp_str = item.get("tanggal_kadaluarsa", "")
            if not exp_str:
                continue
            try:
                exp_dt = datetime.strptime(exp_str, "%Y-%m-%d")
                if exp_dt <= cutoff:
                    result.append(item)
            except ValueError:
                pass
        return result

    def get_statistics(self) -> dict:
        all_items = self.get_all_items()
        if not all_items:
            return {}
        prices  = [i["harga"] for i in all_items]
        stocks  = [i["jumlah"] for i in all_items]
        expired = [i for i in all_items
                   if i.get("tanggal_kadaluarsa") and
                   datetime.strptime(i["tanggal_kadaluarsa"], "%Y-%m-%d") < datetime.today()]
        total_value = sum(i["harga"] * i["jumlah"] for i in all_items)
        categories  = {}
        for i in all_items:
            cat = i.get("kategori", "Lainnya")
            categories[cat] = categories.get(cat, 0) + 1
        return {
            "total_items":     len(all_items),
            "avg_price":       sum(prices) / len(prices),
            "max_price":       max(prices),
            "min_price":       min(prices),
            "total_stock":     sum(stocks),
            "total_value":     total_value,
            "expired_count":   len(expired),
            "categories":      categories,
        }

    def __len__(self):
        return len(self.hashmap)