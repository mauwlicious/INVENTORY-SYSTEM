# screens/items_screen.py
import customtkinter as ctk
from datetime import datetime, date

PRIMARY    = "#1E61B8"
TEXT_SEC   = "#7A8A9A"
TEXT_PRI   = "#1A2A3A"
RED        = "#D92626"
GREEN      = "#1A9A4A"

CATEGORIES = ["Electronics", "Furniture", "Clothing", "Food & Beverage",
              "Tools", "Stationary", "Cleaning", "Medical"]

COL_HEADERS = ["CODE", "NAME", "CATEGORY", "QTY", "PRICE", "EXPIRY", "ACTION"]
COL_WIDTHS  = [100, 150, 150, 55, 130, 100, 70]

ROWS_PER_PAGE = 10


def _is_dark():
    return ctk.get_appearance_mode() == "Dark"

def _row_bg(even: bool):
    """Warna zebra-stripe yang aware dark/light mode."""
    if _is_dark():
        return "#1E2A3E" if even else "#172030"
    return "#F0F5FF" if even else "#FFFFFF"

def _table_bg():
    return "#172030" if _is_dark() else "#FFFFFF"

def expiry_color(exp_str):
    try:
        d = datetime.strptime(exp_str, "%Y-%m-%d").date()
        delta = (d - date.today()).days
        if delta < 0:   return RED
        if delta <= 90: return "#D97800"
        return GREEN
    except Exception:
        return TEXT_SEC


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

        self._code_entry = ctk.CTkEntry(frow, width=180, height=36,
                                         placeholder_text="🔍 Code...", corner_radius=8)
        self._code_entry.pack(side="left", padx=(0, 8))
        self._code_entry.bind("<KeyRelease>", lambda e: self._schedule_search())

        self._name_entry = ctk.CTkEntry(frow, width=200, height=36,
                                         placeholder_text="🔤 Name...", corner_radius=8)
        self._name_entry.pack(side="left", padx=(0, 8))
        self._name_entry.bind("<KeyRelease>", lambda e: self._schedule_search())

        sort_opts = ["Default", "Name A→Z", "Name Z→A", "Price Low→High", "Price High→Low"]
        self._sort_var = ctk.StringVar(value="Default")
        ctk.CTkOptionMenu(frow, variable=self._sort_var, values=sort_opts,
                          width=160, height=36, corner_radius=8,
                          command=self._on_sort).pack(side="left", padx=(0, 8))

        cat_opts = ["All Categories"] + CATEGORIES
        self._cat_var = ctk.StringVar(value="All Categories")
        ctk.CTkOptionMenu(frow, variable=self._cat_var, values=cat_opts,
                          width=160, height=36, corner_radius=8,
                          command=self._on_category).pack(side="left")

        self._build_table_header()

        # _table_outer: warna dinamis, bukan hardcode WHITE
        self._table_outer = ctk.CTkFrame(self, fg_color=_table_bg(), corner_radius=8)
        self._table_outer.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 4))
        self._table_outer.grid_columnconfigure(0, weight=1)
        self._table_outer.grid_rowconfigure(0, weight=1)

        self._table = ctk.CTkFrame(self._table_outer, fg_color="transparent")
        self._table.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self._table.grid_columnconfigure(0, weight=1)

        self._build_pagination_bar()

    def _build_table_header(self):
        hdr = ctk.CTkFrame(self, fg_color=PRIMARY, corner_radius=8, height=34)
        hdr.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 2))
        hdr.grid_propagate(False)
        for i, (col, w) in enumerate(zip(COL_HEADERS, COL_WIDTHS)):
            hdr.grid_columnconfigure(i, minsize=w, weight=1 if col == "NAME" else 0)
            ctk.CTkLabel(hdr, text=col,
                         font=ctk.CTkFont(size=11, weight="bold"),
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
        # Update warna tabel setiap kali screen ditampilkan (bisa habis theme switch)
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
        if sort_key == "Name A→Z":
            items = InventorySorter.sort(items, key="nama_item", reverse=False)
        elif sort_key == "Name Z→A":
            items = InventorySorter.sort(items, key="nama_item", reverse=True)
        elif sort_key == "Price Low→High":
            items = InventorySorter.sort(items, key="harga", reverse=False)
        elif sort_key == "Price High→Low":
            items = InventorySorter.sort(items, key="harga", reverse=True)

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
        bg        = _row_bg(row_idx % 2 == 0)
        exp_str   = item.get("expiry_date", "")
        exp_col   = expiry_color(exp_str)
        price_fmt = f"Rp {item.get('price', 0):,.0f}".replace(",", ".")

        row_frame = ctk.CTkFrame(self._table, fg_color=bg, corner_radius=6)
        row_frame.grid(row=row_idx, column=0, sticky="ew", pady=1)

        for i, (col, w) in enumerate(zip(COL_HEADERS, COL_WIDTHS)):
            row_frame.grid_columnconfigure(i, minsize=w, weight=1 if col == "NAME" else 0)

        def lbl(text, col_i, anchor="w", color=None, bold=False):
            kw = dict(text=text, anchor=anchor, fg_color="transparent",
                      font=ctk.CTkFont(size=11, weight="bold" if bold else "normal"))
            if color:
                kw["text_color"] = color
            ctk.CTkLabel(row_frame, **kw).grid(
                row=0, column=col_i, sticky="ew", padx=6, pady=6)

        lbl(item.get("code", ""),     0, color=PRIMARY, bold=True)
        lbl(item.get("name", ""),     1)
        lbl(item.get("category", ""), 2, color=TEXT_SEC)
        lbl(str(item.get("qty", 0)),  3, anchor="center")
        lbl(price_fmt,                4, anchor="e")

        ctk.CTkLabel(row_frame, text=exp_str or "—", anchor="center",
                     fg_color="transparent", font=ctk.CTkFont(size=11),
                     text_color=exp_col).grid(
            row=0, column=5, sticky="ew", padx=6, pady=6)

        code = item.get("code", "")
        ctk.CTkButton(row_frame, text="🗑", width=38, height=26,
                      fg_color="#FFECEC", text_color=RED,
                      hover_color="#FFD5D5", font=ctk.CTkFont(size=12),
                      corner_radius=6,
                      command=lambda c=code: self._confirm_delete(c)).grid(
            row=0, column=6, padx=6, pady=6)

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

    # ── Add dialog ────────────────────────────────────────────────────────────
    def _open_add_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Add New Item")
        dlg.geometry("420x540")
        dlg.resizable(True, True)
        dlg.grab_set()
        dlg.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dlg, text="Add New Item",
                     font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, padx=24, pady=(20, 16), sticky="w")

        fields = {}
        labels = [
            ("code",    "Item Code (e.g. ITM-0999)"),
            ("name",    "Item Name"),
            ("category","Category"),
            ("qty",     "Quantity"),
            ("price",   "Price (Rp)"),
            ("expiry",  "Expiry Date (YYYY-MM-DD)"),
            ("store",   "Store / Location"),
        ]
        for i, (key, hint) in enumerate(labels):
            ctk.CTkLabel(dlg, text=hint, font=ctk.CTkFont(size=12),
                         text_color=TEXT_SEC).grid(
                row=i*2+1, column=0, padx=24, sticky="w", pady=(6, 0))
            entry = ctk.CTkEntry(dlg, width=372, height=36,
                                  placeholder_text=hint, corner_radius=8)
            entry.grid(row=i*2+2, column=0, padx=24)
            fields[key] = entry

        err_lbl = ctk.CTkLabel(dlg, text="", font=ctk.CTkFont(size=11), text_color=RED)
        err_lbl.grid(row=99, column=0, padx=24, pady=(6, 0), sticky="w")

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.grid(row=100, column=0, padx=24, pady=(10, 20), sticky="e")

        def do_add():
            try:
                code   = fields["code"].get().strip().upper()
                name   = fields["name"].get().strip()
                cat    = fields["category"].get().strip()
                qty    = int(fields["qty"].get().strip() or "0")
                price  = float(fields["price"].get().strip().replace(".", "").replace(",", "") or "0")
                expiry = fields["expiry"].get().strip()
                store  = fields["store"].get().strip()
                if not code or not name:
                    err_lbl.configure(text="Code and Name are required!")
                    return
                if self.inventory_manager.hash_map.contains(code):
                    err_lbl.configure(text=f"Code {code} already exists!")
                    return
                new_item = {
                    "code": code, "kode_item": code,
                    "name": name, "nama_item": name,
                    "category": cat, "kategori": cat,
                    "qty": qty, "jumlah": qty,
                    "price": price, "harga": price,
                    "expiry_date": expiry or "",
                    "tanggal_kadaluarsa": expiry or "",
                    "store": store or "—", "lokasi": store or "—",
                }
                self.inventory_manager.add_item(new_item)
                dlg.destroy()
                self._load_items()
                self._render_page()
                self._show_toast(f"✅ Item {code} added!")
            except ValueError:
                err_lbl.configure(text="Invalid number format!")

        ctk.CTkButton(btn_row, text="Cancel", width=100, height=36,
                      fg_color="transparent", border_width=1,
                      text_color=TEXT_PRI, corner_radius=8,
                      command=dlg.destroy).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Add Item", width=120, height=36,
                      fg_color=PRIMARY, hover_color="#1650A0",
                      corner_radius=8, command=do_add).pack(side="left")

    # ── Delete dialog ─────────────────────────────────────────────────────────
    def _confirm_delete(self, code):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Confirm Delete")
        dlg.geometry("360x175")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dlg, text="Delete Item",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=24, pady=(20, 8), sticky="w")
        ctk.CTkLabel(dlg, text=f"Are you sure you want to delete\n{code}?",
                     font=ctk.CTkFont(size=13), text_color=TEXT_SEC,
                     justify="left").grid(row=1, column=0, padx=24, sticky="w")

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.grid(row=2, column=0, padx=24, pady=(16, 20), sticky="e")

        def do_delete():
            success = self.inventory_manager.remove_item(code)
            dlg.destroy()
            if success:
                self._load_items()
                self._render_page()
                self._show_toast(f"🗑 {code} deleted.")
            else:
                self._show_toast(f"❌ {code} not found!", error=True)

        ctk.CTkButton(btn_row, text="Cancel", width=90, height=34,
                      fg_color="transparent", border_width=1,
                      text_color=TEXT_PRI, corner_radius=8,
                      command=dlg.destroy).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Delete", width=100, height=34,
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