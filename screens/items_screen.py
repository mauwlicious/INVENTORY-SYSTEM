# screens/items_screen.py
import customtkinter as ctk
from datetime import datetime, date

PRIMARY    = "#1E61B8"
TEXT_SEC   = "#7A8A9A"
TEXT_PRI   = "#1A2A3A"
RED        = "#D92626"
GREEN      = "#1A9A4A"
ORANGE     = "#D97800"

CATEGORIES = ["Electronics", "Furniture", "Clothing", "Food & Beverage",
              "Tools", "Stationary", "Cleaning", "Medical"]

COL_HEADERS = ["CODE", "NAME", "CATEGORY", "QTY", "PRICE", "EXPIRY", "ACTIONS"]
COL_WIDTHS  = [100, 150, 130, 55, 120, 100, 165]

ROWS_PER_PAGE = 10


def _is_dark():
    return ctk.get_appearance_mode() == "Dark"

def _row_bg(even: bool):
    return ("#1E2A3E" if even else "#172030") if _is_dark() else ("#F0F5FF" if even else "#FFFFFF")

def _table_bg():
    return "#172030" if _is_dark() else "#FFFFFF"

def expiry_status(exp_str):
    """Returns (color, badge_text)"""
    if not exp_str:
        return TEXT_SEC, "—"
    try:
        delta = (datetime.strptime(exp_str, "%Y-%m-%d").date() - date.today()).days
        if delta < 0:    return RED,    f"Expired"
        if delta <= 30:  return RED,    f"{delta}d"
        if delta <= 90:  return ORANGE, f"{delta}d"
        return GREEN, exp_str
    except Exception:
        return TEXT_SEC, exp_str


# ─────────────────────────────────────────────────────────────────────────────
# Shared dialog helpers
# ─────────────────────────────────────────────────────────────────────────────

def show_validation_dialog(parent, errors: list):
    dlg = ctk.CTkToplevel(parent)
    dlg.title("Input Tidak Valid")
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(dlg, text="⚠ Terdapat Kesalahan Input",
                 font=ctk.CTkFont(size=15, weight="bold"),
                 text_color=RED).grid(row=0, column=0, padx=24, pady=(20, 8), sticky="w")

    for i, err in enumerate(errors):
        ctk.CTkLabel(dlg, text=err,
                     font=ctk.CTkFont(size=12), text_color=TEXT_PRI,
                     anchor="w", justify="left").grid(
            row=i+1, column=0, padx=28, pady=2, sticky="w")

    ctk.CTkLabel(dlg, text="Silahkan periksa kembali dan ulangi.",
                 font=ctk.CTkFont(size=12), text_color=TEXT_SEC).grid(
        row=len(errors)+1, column=0, padx=24, pady=(10, 4), sticky="w")

    ctk.CTkButton(dlg, text="OK, Ulangi", width=120, height=34,
                  fg_color=PRIMARY, hover_color="#1650A0",
                  corner_radius=8, command=dlg.destroy).grid(
        row=len(errors)+2, column=0, padx=24, pady=(8, 20))

    # Ukuran dialog menyesuaikan jumlah error
    h = 160 + len(errors) * 28
    dlg.geometry(f"400x{h}")


def validate_item_form(code, name, cat, qty_str, price_str, expiry_str,
                       inventory_manager, is_edit=False, original_code=None):
    errors = []
    code = code.strip().upper()
    name = name.strip()

    if not code:
        errors.append("• Kode item tidak boleh kosong.")
    elif not is_edit and inventory_manager.hash_map.contains(code):
        errors.append(f"• Kode '{code}' sudah ada di inventory.")
    elif is_edit and code != original_code and inventory_manager.hash_map.contains(code):
        errors.append(f"• Kode '{code}' sudah digunakan item lain.")

    if not name:
        errors.append("• Nama item tidak boleh kosong.")

    if not cat or cat == "— Pilih Kategori —":
        errors.append("• Kategori harus dipilih.")

    try:
        qty = int(qty_str.strip() or "x")
        if qty < 0:
            errors.append("• Jumlah tidak boleh negatif.")
    except ValueError:
        errors.append("• Jumlah harus berupa angka bulat (contoh: 10).")

    price_clean = price_str.strip().replace(".", "").replace(",", "").replace("Rp", "").strip()
    try:
        price = float(price_clean or "x")
        if price < 0:
            errors.append("• Harga tidak boleh negatif.")
    except ValueError:
        errors.append("• Harga harus berupa angka (contoh: 50000).")

    if expiry_str.strip():
        try:
            datetime.strptime(expiry_str.strip(), "%Y-%m-%d")
        except ValueError:
            errors.append("• Format tanggal kadaluarsa harus YYYY-MM-DD (contoh: 2026-12-31).")

    return errors


class ItemsScreen(ctk.CTkFrame):
    def __init__(self, master, inventory_manager, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=0, **kwargs)
        self.inventory_manager = inventory_manager
        self.category_filter   = "All"
        self._search_code      = ""
        self._search_name      = ""
        self._debounce_id      = None
        self._current_page     = 0
        self._all_items        = []

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_layout()
        self.on_show()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_layout(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent", height=50)
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 0))
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(left, text="Items Inventory",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")
        self._count_lbl = ctk.CTkLabel(left, text="",
                                        font=ctk.CTkFont(size=12), text_color=TEXT_SEC)
        self._count_lbl.pack(anchor="w")

        ctk.CTkButton(hdr, text="+ Add Item", width=130, height=36,
                      fg_color=PRIMARY, hover_color="#1650A0",
                      font=ctk.CTkFont(size=13), corner_radius=8,
                      command=self._open_add_dialog).grid(row=0, column=2)

        frow = ctk.CTkFrame(self, fg_color="transparent")
        frow.grid(row=1, column=0, sticky="ew", padx=24, pady=(10, 6))

        self._code_entry = ctk.CTkEntry(frow, width=175, height=36,
                                         placeholder_text="🔍 Code...", corner_radius=8)
        self._code_entry.pack(side="left", padx=(0, 8))
        self._code_entry.bind("<KeyRelease>", lambda e: self._schedule_search())

        self._name_entry = ctk.CTkEntry(frow, width=195, height=36,
                                         placeholder_text="🔤 Name...", corner_radius=8)
        self._name_entry.pack(side="left", padx=(0, 8))
        self._name_entry.bind("<KeyRelease>", lambda e: self._schedule_search())

        sort_opts = ["Default", "Name A→Z", "Name Z→A", "Price Low→High", "Price High→Low"]
        self._sort_var = ctk.StringVar(value="Default")
        ctk.CTkOptionMenu(frow, variable=self._sort_var, values=sort_opts,
                          width=155, height=36, corner_radius=8,
                          command=self._on_sort).pack(side="left", padx=(0, 8))

        cat_opts = ["All Categories"] + CATEGORIES
        self._cat_var = ctk.StringVar(value="All Categories")
        ctk.CTkOptionMenu(frow, variable=self._cat_var, values=cat_opts,
                          width=155, height=36, corner_radius=8,
                          command=self._on_category).pack(side="left")

        self._build_table_header()

        self._table_outer = ctk.CTkFrame(self, fg_color=_table_bg(), corner_radius=8)
        self._table_outer.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 4))
        self._table_outer.grid_columnconfigure(0, weight=1)
        self._table_outer.grid_rowconfigure(0, weight=1)

        self._table = ctk.CTkFrame(self._table_outer, fg_color="transparent")
        self._table.grid(row=0, column=0, sticky="nsew")
        self._table.grid_columnconfigure(0, weight=1)

        self._build_pagination_bar()

    def _build_table_header(self):
        hdr = ctk.CTkFrame(self, fg_color=PRIMARY, corner_radius=8, height=34)
        hdr.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 2))
        hdr.grid_propagate(False)
        for i, (col, w) in enumerate(zip(COL_HEADERS, COL_WIDTHS)):
            hdr.grid_columnconfigure(i, minsize=w, weight=1 if col == "NAME" else 0)
            ctk.CTkLabel(hdr, text=col, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#FFFFFF", anchor="center").grid(
                row=0, column=i, sticky="ew", padx=6, pady=7)

    def _build_pagination_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent", height=40)
        bar.grid(row=4, column=0, sticky="ew", padx=24, pady=(2, 12))
        bar.grid_columnconfigure(1, weight=1)

        self._prev_btn = ctk.CTkButton(bar, text="◀ Prev", width=90, height=30,
                                        fg_color=PRIMARY, hover_color="#1650A0",
                                        font=ctk.CTkFont(size=12), corner_radius=8,
                                        command=self._prev_page)
        self._prev_btn.grid(row=0, column=0, padx=(0, 8))
        self._page_lbl = ctk.CTkLabel(bar, text="Page 1 / 1",
                                       font=ctk.CTkFont(size=12), text_color=TEXT_SEC)
        self._page_lbl.grid(row=0, column=1)
        self._next_btn = ctk.CTkButton(bar, text="Next ▶", width=90, height=30,
                                        fg_color=PRIMARY, hover_color="#1650A0",
                                        font=ctk.CTkFont(size=12), corner_radius=8,
                                        command=self._next_page)
        self._next_btn.grid(row=0, column=2, padx=(8, 0))

    # ── Debounce ──────────────────────────────────────────────────────────────
    def _schedule_search(self):
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(300, self._on_search)

    # ── Data ──────────────────────────────────────────────────────────────────
    def on_show(self):
        self._table_outer.configure(fg_color=_table_bg())
        self._load_items()
        self._render_page()

    def _load_items(self):
        items = self.inventory_manager.hash_map.all_values()
        if self.category_filter not in ("All", "All Categories"):
            items = [x for x in items if x.get("category") == self.category_filter]
        code_q = self._search_code.strip().upper()
        name_q = self._search_name.strip().lower()
        if code_q:
            items = [x for x in items if code_q in x.get("code", "").upper()]
        if name_q:
            items = [x for x in items if name_q in x.get("name", "").lower()]
        sort_key = self._sort_var.get() if hasattr(self, "_sort_var") else "Default"
        from data_structures import InventorySorter
        if   sort_key == "Name A→Z":        items = InventorySorter.sort(items, key="nama_item", reverse=False)
        elif sort_key == "Name Z→A":        items = InventorySorter.sort(items, key="nama_item", reverse=True)
        elif sort_key == "Price Low→High":  items = InventorySorter.sort(items, key="harga",     reverse=False)
        elif sort_key == "Price High→Low":  items = InventorySorter.sort(items, key="harga",     reverse=True)
        self._all_items    = items
        self._current_page = 0

    def _total_pages(self):
        return max(1, -(-len(self._all_items) // ROWS_PER_PAGE))

    def _render_page(self):
        for w in self._table.winfo_children():
            w.destroy()
        total      = len(self._all_items)
        n_pages    = self._total_pages()
        start      = self._current_page * ROWS_PER_PAGE
        end        = min(start + ROWS_PER_PAGE, total)
        page_items = self._all_items[start:end]
        self._count_lbl.configure(
            text=f"{total} items  •  showing {start+1}–{end}" if total > 0 else "No items found")
        self._page_lbl.configure(text=f"Page {self._current_page + 1} / {n_pages}")
        self._prev_btn.configure(state="normal" if self._current_page > 0 else "disabled")
        self._next_btn.configure(state="normal" if self._current_page < n_pages - 1 else "disabled")
        for i, item in enumerate(page_items):
            self._add_row(i, item)

    def _add_row(self, row_idx, item):
        bg  = _row_bg(row_idx % 2 == 0)
        exp_col, exp_badge = expiry_status(item.get("expiry_date", ""))
        price_fmt = f"Rp {item.get('price', 0):,.0f}".replace(",", ".")

        row_frame = ctk.CTkFrame(self._table, fg_color=bg, corner_radius=6)
        row_frame.grid(row=row_idx, column=0, sticky="ew", pady=1)
        for i, (col, w) in enumerate(zip(COL_HEADERS, COL_WIDTHS)):
            row_frame.grid_columnconfigure(i, minsize=w, weight=1 if col == "NAME" else 0)

        def lbl(text, col_i, anchor="w", color=None, bold=False):
            kw = dict(text=text, anchor=anchor, fg_color="transparent",
                      font=ctk.CTkFont(size=11, weight="bold" if bold else "normal"))
            if color: kw["text_color"] = color
            ctk.CTkLabel(row_frame, **kw).grid(row=0, column=col_i, sticky="ew", padx=6, pady=6)

        lbl(item.get("code", ""),     0, color=PRIMARY, bold=True)
        lbl(item.get("name", ""),     1)
        lbl(item.get("category", ""), 2, color=TEXT_SEC)
        lbl(str(item.get("qty", 0)),  3, anchor="center")
        lbl(price_fmt,                4, anchor="e")

        ctk.CTkLabel(row_frame, text=exp_badge, anchor="center",
                     fg_color="transparent", font=ctk.CTkFont(size=11),
                     text_color=exp_col).grid(row=0, column=5, sticky="ew", padx=6, pady=6)

        # ── Action buttons ────────────────────────────────────────────────────
        code = item.get("code", "")
        btn_f = ctk.CTkFrame(row_frame, fg_color="transparent")
        btn_f.grid(row=0, column=6, padx=4, pady=4)

        ctk.CTkButton(btn_f, text="✏", width=36, height=26,
                      fg_color="#E8F0FE", text_color=PRIMARY,
                      hover_color="#C5D8FF", corner_radius=6,
                      font=ctk.CTkFont(size=13),
                      command=lambda i=item: self._open_edit_dialog(dict(i))).pack(side="left", padx=2)

        ctk.CTkButton(btn_f, text="📋", width=36, height=26,
                      fg_color="#EAF7EC", text_color=GREEN,
                      hover_color="#C5EDD0", corner_radius=6,
                      font=ctk.CTkFont(size=13),
                      command=lambda i=item: self._open_details_dialog(dict(i))).pack(side="left", padx=2)

        ctk.CTkButton(btn_f, text="🗑", width=36, height=26,
                      fg_color="#FFECEC", text_color=RED,
                      hover_color="#FFD5D5", corner_radius=6,
                      font=ctk.CTkFont(size=13),
                      command=lambda c=code: self._confirm_delete(c)).pack(side="left", padx=2)

    # ── Pagination ────────────────────────────────────────────────────────────
    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_page()

    def _next_page(self):
        if self._current_page < self._total_pages() - 1:
            self._current_page += 1
            self._render_page()

    # ── Callbacks ─────────────────────────────────────────────────────────────
    def _on_search(self):
        self._search_code = self._code_entry.get()
        self._search_name = self._name_entry.get()
        self._load_items()
        self._render_page()

    def _on_sort(self, val):
        self._load_items()
        self._render_page()

    def _on_category(self, val):
        self.category_filter = val
        self._load_items()
        self._render_page()

    # ── ADD ITEM dialog ───────────────────────────────────────────────────────
    def _open_add_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Add New Item")
        dlg.geometry("440x580")
        dlg.resizable(True, True)
        dlg.grab_set()
        dlg.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dlg, text="➕ Add New Item",
                     font=ctk.CTkFont(size=17, weight="bold")).grid(
            row=0, column=0, padx=24, pady=(20, 14), sticky="w")

        fields = {}

        def field_row(row, key, label, placeholder=""):
            ctk.CTkLabel(dlg, text=label, font=ctk.CTkFont(size=12),
                         text_color=TEXT_SEC).grid(row=row*2-1, column=0, padx=24, sticky="w", pady=(6,0))
            e = ctk.CTkEntry(dlg, width=392, height=36, placeholder_text=placeholder, corner_radius=8)
            e.grid(row=row*2, column=0, padx=24)
            fields[key] = e

        field_row(1, "code",   "Kode Item *",   "Contoh: ITM-0999")
        field_row(2, "name",   "Nama Item *",   "Nama lengkap barang")
        field_row(4, "qty",    "Jumlah *",      "Contoh: 50")
        field_row(5, "price",  "Harga (Rp) *",  "Contoh: 150000")
        field_row(6, "expiry", "Tanggal Kadaluarsa", "YYYY-MM-DD (kosongkan jika tidak ada)")
        field_row(7, "store",  "Lokasi / Gudang", "Contoh: Gudang A")

        # Category dropdown
        ctk.CTkLabel(dlg, text="Kategori *", font=ctk.CTkFont(size=12),
                     text_color=TEXT_SEC).grid(row=5, column=0, padx=24, sticky="w", pady=(6,0))
        cat_var = ctk.StringVar(value="— Pilih Kategori —")
        cat_menu = ctk.CTkOptionMenu(dlg, variable=cat_var,
                                      values=["— Pilih Kategori —"] + CATEGORIES,
                                      width=392, height=36, corner_radius=8)
        cat_menu.grid(row=6, column=0, padx=24)
        fields["category_var"] = cat_var

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.grid(row=99, column=0, padx=24, pady=(16, 20), sticky="e")

        def do_add():
            code       = fields["code"].get().strip().upper()
            name       = fields["name"].get().strip()
            cat        = cat_var.get()
            qty_str    = fields["qty"].get().strip()
            price_str  = fields["price"].get().strip()
            expiry_str = fields["expiry"].get().strip()
            store      = fields["store"].get().strip()

            errors = validate_item_form(code, name, cat, qty_str, price_str,
                                        expiry_str, self.inventory_manager)
            if errors:
                show_validation_dialog(dlg, errors)
                return

            new_item = {
                "code": code, "kode_item": code,
                "name": name, "nama_item": name,
                "category": cat, "kategori": cat,
                "qty": int(qty_str), "jumlah": int(qty_str),
                "price": float(price_str.replace(".", "").replace(",", "")),
                "harga": float(price_str.replace(".", "").replace(",", "")),
                "expiry_date": expiry_str, "tanggal_kadaluarsa": expiry_str,
                "store": store or "—", "lokasi": store or "—",
                "satuan": "pcs",
            }
            self.inventory_manager.add_item(new_item)
            self.inventory_manager.autosave()
            dlg.destroy()
            self._load_items()
            self._render_page()
            self._show_toast(f"✅ Item {code} berhasil ditambahkan!")

        ctk.CTkButton(btn_row, text="Batal", width=100, height=36,
                      fg_color="transparent", border_width=1,
                      text_color=TEXT_PRI, corner_radius=8,
                      command=dlg.destroy).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Simpan Item", width=130, height=36,
                      fg_color=PRIMARY, hover_color="#1650A0",
                      corner_radius=8, command=do_add).pack(side="left")

    # ── EDIT ITEM dialog ──────────────────────────────────────────────────────
    def _open_edit_dialog(self, item: dict):
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Edit Item — {item.get('code','')}")
        dlg.geometry("440x600")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.grid_columnconfigure(0, weight=1)

        original_code = item.get("code", "")

        ctk.CTkLabel(dlg, text=f"✏ Edit Item",
                     font=ctk.CTkFont(size=17, weight="bold")).grid(
            row=0, column=0, padx=24, pady=(20, 4), sticky="w")
        ctk.CTkLabel(dlg, text=f"Kode: {original_code}",
                     font=ctk.CTkFont(size=12), text_color=PRIMARY).grid(
            row=1, column=0, padx=24, pady=(0, 10), sticky="w")

        fields = {}

        def field_row(row, key, label, prefill=""):
            ctk.CTkLabel(dlg, text=label, font=ctk.CTkFont(size=12),
                         text_color=TEXT_SEC).grid(row=row*2, column=0, padx=24, sticky="w", pady=(6,0))
            e = ctk.CTkEntry(dlg, width=392, height=36, corner_radius=8)
            e.grid(row=row*2+1, column=0, padx=24)
            e.insert(0, str(prefill))
            fields[key] = e

        field_row(1, "name",   "Nama Item *",        item.get("name", ""))
        field_row(3, "qty",    "Jumlah *",            item.get("qty", 0))
        field_row(4, "price",  "Harga (Rp) *",        int(item.get("price", 0)))
        field_row(5, "expiry", "Tanggal Kadaluarsa",  item.get("expiry_date", ""))
        field_row(6, "store",  "Lokasi / Gudang",     item.get("lokasi", item.get("store", "")))

        # Category dropdown
        ctk.CTkLabel(dlg, text="Kategori *", font=ctk.CTkFont(size=12),
                     text_color=TEXT_SEC).grid(row=4, column=0, padx=24, sticky="w", pady=(6,0))
        cat_var = ctk.StringVar(value=item.get("category", CATEGORIES[0]))
        ctk.CTkOptionMenu(dlg, variable=cat_var,
                           values=CATEGORIES,
                           width=392, height=36, corner_radius=8).grid(
            row=5, column=0, padx=24)

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.grid(row=99, column=0, padx=24, pady=(16, 20), sticky="e")

        def do_edit():
            name       = fields["name"].get().strip()
            cat        = cat_var.get()
            qty_str    = fields["qty"].get().strip()
            price_str  = fields["price"].get().strip()
            expiry_str = fields["expiry"].get().strip()
            store      = fields["store"].get().strip()

            errors = validate_item_form(
                original_code, name, cat, qty_str, price_str, expiry_str,
                self.inventory_manager, is_edit=True, original_code=original_code)
            if errors:
                show_validation_dialog(dlg, errors)
                return

            updated = {
                "code": original_code, "kode_item": original_code,
                "name": name, "nama_item": name,
                "category": cat, "kategori": cat,
                "qty": int(qty_str), "jumlah": int(qty_str),
                "price": float(price_str.replace(".", "").replace(",", "")),
                "harga": float(price_str.replace(".", "").replace(",", "")),
                "expiry_date": expiry_str, "tanggal_kadaluarsa": expiry_str,
                "store": store or "—", "lokasi": store or "—",
                "satuan": item.get("satuan", "pcs"),
            }
            self.inventory_manager.update_item(original_code, updated)
            self.inventory_manager.autosave()
            dlg.destroy()
            self._load_items()
            self._render_page()
            self._show_toast(f"✅ Item {original_code} berhasil diperbarui!")

        ctk.CTkButton(btn_row, text="Batal", width=100, height=36,
                      fg_color="transparent", border_width=1,
                      text_color=TEXT_PRI, corner_radius=8,
                      command=dlg.destroy).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Simpan Perubahan", width=150, height=36,
                      fg_color=PRIMARY, hover_color="#1650A0",
                      corner_radius=8, command=do_edit).pack(side="left")

    # ── DETAILS dialog ────────────────────────────────────────────────────────
    def _open_details_dialog(self, item: dict):
        open_details_dialog(self, item)

    # ── DELETE dialog ─────────────────────────────────────────────────────────
    def _confirm_delete(self, code):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Konfirmasi Hapus")
        dlg.geometry("360x180")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dlg, text="🗑 Hapus Item",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=24, pady=(20, 8), sticky="w")
        ctk.CTkLabel(dlg, text=f"Yakin ingin menghapus item\n{code} secara permanen?",
                     font=ctk.CTkFont(size=13), text_color=TEXT_SEC,
                     justify="left").grid(row=1, column=0, padx=24, sticky="w")

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.grid(row=2, column=0, padx=24, pady=(16, 20), sticky="e")

        def do_delete():
            success = self.inventory_manager.remove_item(code)
            self.inventory_manager.autosave()
            dlg.destroy()
            if success:
                self._load_items()
                self._render_page()
                self._show_toast(f"🗑 Item {code} dihapus.")
            else:
                self._show_toast(f"❌ Item {code} tidak ditemukan!", error=True)

        ctk.CTkButton(btn_row, text="Batal", width=90, height=34,
                      fg_color="transparent", border_width=1,
                      text_color=TEXT_PRI, corner_radius=8,
                      command=dlg.destroy).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Hapus", width=100, height=34,
                      fg_color=RED, hover_color="#B01C1C",
                      corner_radius=8, command=do_delete).pack(side="left")

    # ── Toast ─────────────────────────────────────────────────────────────────
    def _show_toast(self, msg, error=False):
        color = RED if error else GREEN
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        ctk.CTkLabel(toast, text=msg, font=ctk.CTkFont(size=12),
                     fg_color=color, text_color="#FFFFFF",
                     corner_radius=8, padx=16, pady=10).pack()
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 180
        y = self.winfo_rooty() + self.winfo_height() - 60
        toast.geometry(f"+{x}+{y}")
        toast.after(2500, toast.destroy)


# ─────────────────────────────────────────────────────────────────────────────
# Reusable Details Dialog (dipakai juga oleh search_screen)
# ─────────────────────────────────────────────────────────────────────────────

def open_details_dialog(parent, item: dict):
    exp_str = item.get("expiry_date", "")
    exp_col, exp_badge = expiry_status(exp_str)

    dlg = ctk.CTkToplevel(parent)
    dlg.title(f"Detail Item — {item.get('code','')}")
    dlg.geometry("460x500")
    dlg.resizable(False, False)
    dlg.grab_set()
    dlg.grid_columnconfigure(0, weight=1)

    # Header card
    top = ctk.CTkFrame(dlg, fg_color=PRIMARY, corner_radius=12)
    top.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="ew")
    top.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(top, text=item.get("code", ""),
                 font=ctk.CTkFont(size=22, weight="bold"),
                 text_color="#FFFFFF").grid(row=0, column=0, padx=20, pady=(16, 2), sticky="w")
    ctk.CTkLabel(top, text=item.get("name", ""),
                 font=ctk.CTkFont(size=14), text_color="#C0D8F5").grid(
        row=1, column=0, padx=20, pady=(0, 14), sticky="w")

    # Detail fields
    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.grid(row=1, column=0, padx=20, pady=(14, 0), sticky="nsew")
    body.grid_columnconfigure(1, weight=1)

    def detail_row(r, icon, label, value, val_color=None):
        ctk.CTkLabel(body, text=f"{icon}  {label}",
                     font=ctk.CTkFont(size=12), text_color=TEXT_SEC,
                     width=160, anchor="w").grid(row=r, column=0, sticky="w", pady=5)
        kw = dict(text=str(value), font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
        if val_color: kw["text_color"] = val_color
        ctk.CTkLabel(body, **kw).grid(row=r, column=1, sticky="w", padx=8, pady=5)

    price_fmt = f"Rp {item.get('price', 0):,.0f}".replace(",", ".")
    total_fmt = f"Rp {item.get('price', 0) * item.get('qty', 0):,.0f}".replace(",", ".")

    detail_row(0, "🏷",  "Kode Item",      item.get("code", ""),           PRIMARY)
    detail_row(1, "📦",  "Nama Barang",    item.get("name", ""))
    detail_row(2, "🗂",  "Kategori",       item.get("category", ""))
    detail_row(3, "🔢",  "Jumlah Stok",   f"{item.get('qty', 0)} {item.get('satuan','pcs')}")
    detail_row(4, "💰",  "Harga Satuan",  price_fmt,                       PRIMARY)
    detail_row(5, "💵",  "Total Nilai",   total_fmt,                       "#6B3FC0")
    detail_row(6, "📅",  "Kadaluarsa",   exp_badge if exp_str else "—",   exp_col)
    detail_row(7, "📍",  "Lokasi",        item.get("lokasi", item.get("store", "—")))

    ctk.CTkButton(dlg, text="Tutup", width=120, height=36,
                  fg_color=PRIMARY, hover_color="#1650A0",
                  corner_radius=8,
                  command=dlg.destroy).grid(row=2, column=0, pady=(16, 20))