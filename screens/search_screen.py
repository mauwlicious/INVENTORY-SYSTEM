# screens/search_screen.py
import customtkinter as ctk
from screens.items_screen import open_details_dialog, validate_item_form, \
                                  show_validation_dialog, CATEGORIES, expiry_status

PRIMARY  = "#1E61B8"
TEXT_SEC = "#7A8A9A"
TEXT_PRI = "#1A2A3A"
GREEN    = "#1A9A4A"
RED      = "#D92626"


class SearchScreen(ctk.CTkFrame):
    def __init__(self, master, inventory_manager, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=0, **kwargs)
        self.inventory_manager = inventory_manager
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_layout()

    def _build_layout(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        ctk.CTkLabel(hdr, text="Search Inventory",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(hdr, text="O(1) lookup by item code via Hash Map",
                     font=ctk.CTkFont(size=12), text_color=TEXT_SEC).pack(anchor="w")

        search_frame = ctk.CTkFrame(self, corner_radius=12, height=56)
        search_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(16, 12))
        search_frame.grid_propagate(False)
        search_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=20),
                     text_color=PRIMARY).grid(row=0, column=0, padx=(16, 4))
        self._search_entry = ctk.CTkEntry(
            search_frame, height=40,
            placeholder_text="Enter item code (e.g. ELC-0001)...",
            fg_color="transparent", border_width=0,
            font=ctk.CTkFont(size=14), corner_radius=0)
        self._search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 16))
        self._search_entry.bind("<KeyRelease>", lambda e: self._do_search())

        ctk.CTkLabel(self, text='💡 Tip: type any part of the code — e.g. "ELC", "MED-0"',
                     font=ctk.CTkFont(size=11), text_color=TEXT_SEC).grid(
            row=2, column=0, sticky="w", padx=28, pady=(0, 6))

        self._result = ctk.CTkScrollableFrame(self, corner_radius=12)
        self._result.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self._result.grid_columnconfigure(0, weight=1)
        self._show_placeholder()

    def on_show(self):
        pass

    # ── Search logic ──────────────────────────────────────────────────────────
    def _do_search(self):
        text = self._search_entry.get().strip().upper()
        self._clear_result()
        if not text:
            self._show_placeholder()
            return
        item = self.inventory_manager.hash_map.get(text)
        if item:
            self._show_item(item, exact=True)
            return
        results = [v for v in self.inventory_manager.hash_map.all_values()
                   if text in v.get("code", "").upper()]
        if results:
            self._show_multi(results)
        else:
            self._show_not_found(text)

    def _clear_result(self):
        for w in self._result.winfo_children():
            w.destroy()

    def _show_placeholder(self):
        ctk.CTkLabel(self._result, text="Type a code above to search...",
                     font=ctk.CTkFont(size=14), text_color=TEXT_SEC).pack(pady=40)

    def _show_not_found(self, text):
        ctk.CTkLabel(self._result, text=f'❌ No item found with code "{text}"',
                     font=ctk.CTkFont(size=14), text_color=RED).pack(pady=40)

    # ── Single item result ────────────────────────────────────────────────────
    def _show_item(self, item, exact=False):
        # Header
        ctk.CTkLabel(self._result,
                     text="✅ Item Found (Exact Match)" if exact else "✅ Item Found",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=GREEN).pack(anchor="w", padx=20, pady=(16, 4))

        # Action buttons row
        btn_row = ctk.CTkFrame(self._result, fg_color="transparent")
        btn_row.pack(anchor="w", padx=20, pady=(0, 10))

        code = item.get("code", "")

        ctk.CTkButton(btn_row, text="✏ Edit", width=100, height=32,
                      fg_color="#E8F0FE", text_color=PRIMARY,
                      hover_color="#C5D8FF", corner_radius=8,
                      font=ctk.CTkFont(size=12),
                      command=lambda: self._open_edit_dialog(dict(item))).pack(
            side="left", padx=(0, 8))

        ctk.CTkButton(btn_row, text="📋 Details", width=110, height=32,
                      fg_color="#EAF7EC", text_color=GREEN,
                      hover_color="#C5EDD0", corner_radius=8,
                      font=ctk.CTkFont(size=12),
                      command=lambda: open_details_dialog(self, dict(item))).pack(
            side="left")

        # Fields
        exp_col, exp_badge = expiry_status(item.get("expiry_date", ""))
        fields = [
            ("🏷  Code",         item.get("code", ""),                    None),
            ("📦  Name",         item.get("name", ""),                    None),
            ("🗂  Category",     item.get("category", ""),                None),
            ("🔢  Quantity",     f"{item.get('qty', 0)} {item.get('satuan','pcs')}", None),
            ("💰  Price",        f"Rp {item.get('price', 0):,.0f}".replace(",", "."), PRIMARY),
            ("📅  Expiry",       exp_badge if item.get("expiry_date") else "—", exp_col),
            ("📍  Location",     item.get("lokasi", item.get("store", "—")), None),
        ]
        for label, value, color in fields:
            row = ctk.CTkFrame(self._result, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=f"{label}:",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=TEXT_SEC, width=130, anchor="w").grid(
                row=0, column=0, sticky="w")
            kw = dict(text=value, font=ctk.CTkFont(size=12), anchor="w")
            if color: kw["text_color"] = color
            ctk.CTkLabel(row, **kw).grid(row=0, column=1, sticky="w", padx=8)

    # ── Multi-result list ─────────────────────────────────────────────────────
    def _show_multi(self, results):
        ctk.CTkLabel(self._result,
                     text=f"🔍 Found {len(results)} matching items",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=PRIMARY).pack(anchor="w", padx=20, pady=(16, 6))

        # Column header — lebar kolom IDENTIK dengan baris data di bawah
        hdr = ctk.CTkFrame(self._result, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(0, 2))
        for txt, w, anchor in [
            ("CODE", 110, "w"), ("NAME", 0, "w"),
            ("CATEGORY", 140, "w"), ("PRICE", 130, "e")
        ]:
            ctk.CTkLabel(hdr, text=txt, width=w if w else None,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=TEXT_SEC, anchor=anchor).pack(
                side="left", padx=(2 if txt != "CODE" else 10, 2),
                expand=(w == 0), fill="x" if w == 0 else None)

        for i, item in enumerate(results[:100]):
            row = ctk.CTkFrame(self._result, corner_radius=8)
            row.pack(fill="x", padx=12, pady=2, ipady=4)

            # CODE — fixed 110px
            ctk.CTkLabel(row, text=item.get("code", ""),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=PRIMARY, anchor="w",
                         width=110).pack(side="left", padx=(12, 4), pady=5)

            # NAME — expands
            ctk.CTkLabel(row, text=item.get("name", ""),
                         font=ctk.CTkFont(size=12), anchor="w").pack(
                side="left", padx=4, pady=5, fill="x", expand=True)

            # CATEGORY — fixed 140px
            ctk.CTkLabel(row, text=item.get("category", ""),
                         font=ctk.CTkFont(size=11), text_color=TEXT_SEC,
                         anchor="w", width=140).pack(side="left", padx=4, pady=5)

            # PRICE — fixed 130px
            price_fmt = f"Rp {item.get('price', 0):,.0f}".replace(",", ".")
            ctk.CTkLabel(row, text=price_fmt,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=PRIMARY, anchor="e",
                         width=130).pack(side="left", padx=(4, 12), pady=5)

    # ── Edit dialog (dari search) ─────────────────────────────────────────────
    def _open_edit_dialog(self, item: dict):
        original_code = item.get("code", "")

        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Edit Item — {original_code}")
        dlg.geometry("440x600")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dlg, text="✏ Edit Item",
                     font=ctk.CTkFont(size=17, weight="bold")).grid(
            row=0, column=0, padx=24, pady=(20, 4), sticky="w")
        ctk.CTkLabel(dlg, text=f"Kode: {original_code}",
                     font=ctk.CTkFont(size=12), text_color=PRIMARY).grid(
            row=1, column=0, padx=24, pady=(0, 10), sticky="w")

        fields = {}

        def field_row(row, key, label, prefill=""):
            ctk.CTkLabel(dlg, text=label, font=ctk.CTkFont(size=12),
                         text_color=TEXT_SEC).grid(row=row*2, column=0,
                                                    padx=24, sticky="w", pady=(6, 0))
            e = ctk.CTkEntry(dlg, width=392, height=36, corner_radius=8)
            e.grid(row=row*2+1, column=0, padx=24)
            e.insert(0, str(prefill))
            fields[key] = e

        field_row(1, "name",   "Nama Item *",       item.get("name", ""))
        field_row(3, "qty",    "Jumlah *",           item.get("qty", 0))
        field_row(4, "price",  "Harga (Rp) *",       int(item.get("price", 0)))
        field_row(5, "expiry", "Tanggal Kadaluarsa", item.get("expiry_date", ""))
        field_row(6, "store",  "Lokasi / Gudang",    item.get("lokasi", item.get("store", "")))

        ctk.CTkLabel(dlg, text="Kategori *", font=ctk.CTkFont(size=12),
                     text_color=TEXT_SEC).grid(row=4, column=0, padx=24,
                                                sticky="w", pady=(6, 0))
        cat_var = ctk.StringVar(value=item.get("category", CATEGORIES[0]))
        ctk.CTkOptionMenu(dlg, variable=cat_var, values=CATEGORIES,
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
            # Refresh hasil search agar menampilkan data terbaru
            self._do_search()
            self._show_toast(f"✅ Item {original_code} berhasil diperbarui!")

        ctk.CTkButton(btn_row, text="Batal", width=100, height=36,
                      fg_color="transparent", border_width=1,
                      text_color=TEXT_PRI, corner_radius=8,
                      command=dlg.destroy).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Simpan Perubahan", width=150, height=36,
                      fg_color=PRIMARY, hover_color="#1650A0",
                      corner_radius=8, command=do_edit).pack(side="left")

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