# sales_manager.py — Modul manajemen data penjualan
import csv, os
from datetime import datetime

SALES_FILE = "sales.csv"
FIELDNAMES = ["sale_id","date","time","item_code","item_name",
              "category","qty_sold","unit_price","subtotal","cashier"]


def _load_sales() -> list:
    rows = []
    if not os.path.exists(SALES_FILE):
        return rows
    try:
        with open(SALES_FILE, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                row["qty_sold"]   = int(row.get("qty_sold", 0))
                row["unit_price"] = float(row.get("unit_price", 0))
                row["subtotal"]   = float(row.get("subtotal", 0))
                rows.append(row)
    except Exception as e:
        print(f"[WARN] Gagal baca sales: {e}")
    return rows


def _save_sales(rows: list):
    try:
        with open(SALES_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
    except Exception as e:
        print(f"[WARN] Gagal simpan sales: {e}")


def _next_id(rows: list) -> str:
    if not rows:
        return "TRX-0001"
    last = rows[-1].get("sale_id","TRX-0000")
    try:
        n = int(last.split("-")[1]) + 1
    except Exception:
        n = len(rows) + 1
    return f"TRX-{n:04d}"


class SalesManager:
    """Mengelola riwayat penjualan dengan list of dict (disimpan ke CSV)."""

    def __init__(self):
        self._sales = _load_sales()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def record_sale(self, item: dict, qty_sold: int, cashier: str = "Admin") -> dict:
        """Catat penjualan. Mengembalikan dict transaksi baru."""
        now       = datetime.now()
        unit_price = item.get("price", 0)
        subtotal   = unit_price * qty_sold
        record = {
            "sale_id":    _next_id(self._sales),
            "date":       now.strftime("%Y-%m-%d"),
            "time":       now.strftime("%H:%M:%S"),
            "item_code":  item.get("code", ""),
            "item_name":  item.get("name", ""),
            "category":   item.get("category", ""),
            "qty_sold":   qty_sold,
            "unit_price": unit_price,
            "subtotal":   subtotal,
            "cashier":    cashier,
        }
        self._sales.append(record)
        _save_sales(self._sales)
        return record

    def get_all(self) -> list:
        return list(self._sales)

    def get_summary(self) -> dict:
        """Hitung statistik total penjualan."""
        total_trx      = len(self._sales)
        total_revenue  = sum(s["subtotal"] for s in self._sales)
        total_qty_sold = sum(s["qty_sold"]  for s in self._sales)

        # Item paling banyak terjual (menggunakan dict untuk menghitung)
        item_count: dict = {}
        for s in self._sales:
            k = s["item_code"]
            item_count[k] = item_count.get(k, 0) + s["qty_sold"]
        top_item = max(item_count, key=item_count.get) if item_count else "—"
        top_item_qty = item_count.get(top_item, 0)

        # Revenue per kategori
        cat_rev: dict = {}
        for s in self._sales:
            cat = s.get("category","Lainnya")
            cat_rev[cat] = cat_rev.get(cat, 0) + s["subtotal"]

        return {
            "total_trx":       total_trx,
            "total_revenue":   total_revenue,
            "total_qty_sold":  total_qty_sold,
            "top_item":        top_item,
            "top_item_qty":    top_item_qty,
            "revenue_by_cat":  cat_rev,
        }

    def get_recent(self, n: int = 20) -> list:
        """N transaksi terbaru (urutan terbalik)."""
        return list(reversed(self._sales[-n:]))