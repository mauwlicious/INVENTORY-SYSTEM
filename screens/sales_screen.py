import customtkinter as ctk
import math
from datetime import datetime, date

PRIMARY  = "#1E61B8"; TEXT_SEC = ("#5A6A85", "#A3B1CC"); TEXT_PRI = ("#1C1C1C", "#F2F5F7")
RED      = "#D92626"; GREEN    = "#1A9A4A"; ORANGE   = "#D97800"

ROWS_PER_PAGE = 15

# Konfigurasi proporsi & posisi tabel riwayat sesuai referensi items_screen
HIST_HEADERS = ["TRX ID", "TANGGAL", "WAKTU", "NAMA BARANG", "QTY", "TOTAL TRANSAKSI", "AKSI"]
HIST_WIDTHS  = [100, 100, 75, 180, 55, 130, 90]
HIST_ALIGNS  = ["center", "center", "center", "w", "center", "e", "center"]

def _is_dark(): return ctk.get_appearance_mode() == "Dark"
def _card(): return "#2A3448" if _is_dark() else "#FFFFFF"
def _row_bg(even: bool): return ("#1E2A3E" if even else "#172030") if _is_dark() else ("#F0F5FF" if even else "#FFFFFF")

class SalesScreen(ctk.CTkFrame):
    def __init__(self, master, inventory_manager, sales_manager, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=0, **kwargs)
        self.inventory_manager = inventory_manager
        self.sales_manager     = sales_manager
        self._cart             = []
        
        self._pos_page         = 0
        self._pos_results      = []
        self._hist_page        = 0
        self._hist_results     = []

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_layout()
        self.on_show()

    def _build_layout(self):
        tab_bar = ctk.CTkFrame(self, fg_color="transparent")
        tab_bar.grid(row=0, column=0, sticky="ew", padx=24, pady=(16,0))
        self._tabs = {}
        for key, label in [("pos","🛒 Catat Penjualan"),("history","📋 Riwayat & Statistik")]:
            btn = ctk.CTkButton(tab_bar, text=label, width=200, height=36,
                                fg_color="transparent", text_color=TEXT_SEC,
                                hover_color="#E4EDF7", corner_radius=8,
                                font=ctk.CTkFont(size=13),
                                command=lambda k=key: self._switch_tab(k))
            btn.pack(side="left", padx=(0,4))
            self._tabs[key] = btn

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=1, column=0, sticky="nsew", padx=0, pady=(8,0))
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._pages = {}
        self._build_pos_page()
        self._build_history_page()
        self._switch_tab("pos")

    def _switch_tab(self, key):
        for k, btn in self._tabs.items():
            btn.configure(fg_color=PRIMARY if k==key else "transparent",
                          text_color="#FFFFFF" if k==key else TEXT_SEC)
        self._pages[key].tkraise()
        if key == "history": self._load_history()

    def _build_pos_page(self):
        page = ctk.CTkFrame(self._content, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_rowconfigure(0, weight=1)
        page.grid_columnconfigure(0, weight=3)
        page.grid_columnconfigure(1, weight=2)
        self._pages["pos"] = page

        left = ctk.CTkFrame(page, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(24,8), pady=0)
        # Menambahkan baris kosong penyerap ruang di bawah pagination
        left.grid_rowconfigure(4, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Pilih Barang",
                     font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, sticky="w", pady=(0,8))

        # Kontainer baru untuk membungkus pencarian dan opsi pengurutan
        ctrl_frame = ctk.CTkFrame(left, fg_color="transparent")
        ctrl_frame.grid(row=1, column=0, sticky="ew", pady=(0,8))
        ctrl_frame.grid_columnconfigure(0, weight=1)

        sf = ctk.CTkFrame(ctrl_frame, corner_radius=10, height=36)
        sf.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        sf.grid_propagate(False)
        sf.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(sf, text="🔍", font=ctk.CTkFont(size=16), text_color=PRIMARY).grid(row=0, column=0, padx=(12,4), pady=4)
        self._pos_search = ctk.CTkEntry(sf, height=36, fg_color="transparent", border_width=0, placeholder_text="Cari kode atau nama...", font=ctk.CTkFont(size=13), corner_radius=0)
        self._pos_search.grid(row=0, column=1, sticky="ew", padx=(0,12))
        self._pos_search.bind("<KeyRelease>", lambda e: self._pos_search_items())

        # Opsi pengurutan data
        sort_opts = ["Default", "Name A→Z", "Name Z→A", "Price Low→High", "Price High→Low"]
        self._pos_sort_var = ctk.StringVar(value="Default")
        sort_menu = ctk.CTkOptionMenu(ctrl_frame, variable=self._pos_sort_var, values=sort_opts, width=130, height=36, corner_radius=8, command=lambda v: self._pos_search_items())
        sort_menu.grid(row=0, column=1)

        # Kunci tinggi scrollable table agar tidak merosot ke bawah
        self._pos_list = ctk.CTkScrollableFrame(left, corner_radius=8, height=500)
        self._pos_list.grid(row=2, column=0, sticky="ew")
        self._pos_list.grid_columnconfigure(0, weight=1)
        
        self._pos_pag_frame = ctk.CTkFrame(left, fg_color="transparent")
        self._pos_pag_frame.grid(row=3, column=0, sticky="ew", pady=(8,0))
        self._pos_pag_frame.grid_columnconfigure((0,2), weight=1)
        
        self._pos_prev_btn = ctk.CTkButton(self._pos_pag_frame, text="<", width=35, command=lambda: self._change_pos_page(-1))
        self._pos_prev_btn.grid(row=0, column=0, sticky="e", padx=10)
        self._pos_page_lbl = ctk.CTkLabel(self._pos_pag_frame, text="Halaman 1 / 1", font=ctk.CTkFont(size=12))
        self._pos_page_lbl.grid(row=0, column=1)
        self._pos_next_btn = ctk.CTkButton(self._pos_pag_frame, text=">", width=35, command=lambda: self._change_pos_page(1))
        self._pos_next_btn.grid(row=0, column=2, sticky="w", padx=10)

        right = ctk.CTkFrame(page, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=(8,24), pady=0)
        right.grid_rowconfigure(1, weight=1) # Keranjang tetap butuh flexibel memuai
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="🛒 Keranjang",
                     font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, sticky="w", pady=(0,8))

        self._cart_frame = ctk.CTkScrollableFrame(right, corner_radius=8)
        self._cart_frame.grid(row=1, column=0, sticky="nsew")
        self._cart_frame.grid_columnconfigure(0, weight=1)

        bottom = ctk.CTkFrame(right, fg_color=_card(), corner_radius=12)
        bottom.grid(row=2, column=0, sticky="ew", pady=(8,0))
        bottom.grid_columnconfigure(0, weight=1)

        self._total_lbl = ctk.CTkLabel(bottom, text="Total: Rp 0",
                                        font=ctk.CTkFont(size=16, weight="bold"),
                                        text_color=PRIMARY)
        self._total_lbl.grid(row=0, column=0, padx=16, pady=(12,4), sticky="w")

        self._item_count_lbl = ctk.CTkLabel(bottom, text="0 jenis barang",
                                             font=ctk.CTkFont(size=12), text_color=TEXT_SEC)
        self._item_count_lbl.grid(row=1, column=0, padx=16, pady=(0,8), sticky="w")

        btn_row = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_row.grid(row=2, column=0, padx=12, pady=(0,12), sticky="ew")
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_row, text="🗑 Kosongkan", height=36,
                      fg_color="#FFECEC", text_color=RED, hover_color="#FFD5D5",
                      corner_radius=8, font=ctk.CTkFont(size=12),
                      command=self._clear_cart).grid(row=0, column=0, sticky="ew", padx=(0,4))
        ctk.CTkButton(btn_row, text="✅ Proses", height=36,
                      fg_color=GREEN, hover_color="#157A38", text_color="#FFFFFF",
                      corner_radius=8, font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._checkout).grid(row=0, column=1, sticky="ew", padx=(4,0))

    def _pos_search_items(self):
        query = self._pos_search.get().strip().upper()
        all_items = self.inventory_manager.hash_map.all_values()
        
        # Proses penyaringan berdasarkan pencarian teks
        if query:
            filtered = [i for i in all_items if (query in i.get("code", i.get("kode_item", "")).upper() or query in i.get("name", i.get("nama_item", "")).upper())]
        else:
            filtered = all_items
            
        # Proses pengurutan berdasarkan pilihan pada menu
        sort_key = self._pos_sort_var.get() if hasattr(self, "_pos_sort_var") else "Default"
        from data_structures import InventorySorter
        
        if sort_key == "Name A→Z":
            filtered = InventorySorter.sort(filtered, key="nama_item", reverse=False)
        elif sort_key == "Name Z→A":
            filtered = InventorySorter.sort(filtered, key="nama_item", reverse=True)
        elif sort_key == "Price Low→High":
            filtered = InventorySorter.sort(filtered, key="harga", reverse=False)
        elif sort_key == "Price High→Low":
            filtered = InventorySorter.sort(filtered, key="harga", reverse=True)
            
        self._pos_results = filtered
        self._pos_page = 0
        self._render_pos_page()

    def _render_pos_page(self):
        for w in self._pos_list.winfo_children():
            w.destroy()
            
        total_pages = max(1, math.ceil(len(self._pos_results) / ROWS_PER_PAGE))
        self._pos_page_lbl.configure(text=f"Halaman {self._pos_page + 1} / {total_pages}")
        self._pos_prev_btn.configure(state="normal" if self._pos_page > 0 else "disabled")
        self._pos_next_btn.configure(state="normal" if self._pos_page < total_pages - 1 else "disabled")

        start = self._pos_page * ROWS_PER_PAGE
        end = start + ROWS_PER_PAGE
        for item in self._pos_results[start:end]:
            self._pos_item_row(item)

    def _change_pos_page(self, delta):
        self._pos_page += delta
        self._render_pos_page()

    def _pos_item_row(self, item):
        bg = _card()
        row = ctk.CTkFrame(self._pos_list, fg_color=bg, corner_radius=8)
        row.pack(fill="x", padx=4, pady=3, ipady=4)
        row.grid_columnconfigure(1, weight=1)

        qty_avail = item.get("qty", item.get("jumlah", 0))
        is_empty  = qty_avail <= 0
        col       = TEXT_SEC if is_empty else TEXT_PRI
        
        code_str = item.get("code", item.get("kode_item", ""))
        name_str = item.get("name", item.get("nama_item", ""))

        ctk.CTkLabel(row, text=code_str, font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=PRIMARY, width=95, anchor="w").grid(row=0, column=0, padx=(10,4), pady=4)
        ctk.CTkLabel(row, text=name_str, font=ctk.CTkFont(size=11), anchor="w",
                     text_color=col).grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkLabel(row, text=f"Stok:{qty_avail}", font=ctk.CTkFont(size=10),
                     text_color=TEXT_SEC, width=55).grid(row=0, column=2, padx=4)
        ctk.CTkButton(row, text="+", width=30, height=26,
                      fg_color=PRIMARY if not is_empty else "#CCCCCC",
                      text_color="#FFFFFF", corner_radius=6,
                      font=ctk.CTkFont(size=14), state="normal" if not is_empty else "disabled",
                      command=lambda i=item: self._add_to_cart(i)).grid(row=0, column=3, padx=(4,8), pady=4)

    def _add_to_cart(self, item):
        code = item.get("code", item.get("kode_item", ""))
        price = item.get("price", item.get("harga", 0))
        qty_avail = item.get("qty", item.get("jumlah", 0))
        
        for entry in self._cart:
            if entry["code"] == code:
                if entry["qty"] < qty_avail:
                    entry["qty"] += 1
                    entry["subtotal"] = entry["qty"] * price
                self._render_cart()
                return
                
        self._cart.append({
            "code":     code,
            "name":     item.get("name", item.get("nama_item", "")),
            "price":    price,
            "qty":      1,
            "subtotal": price,
            "max_qty":  qty_avail,
        })
        self._render_cart()

    def _render_cart(self):
        for w in self._cart_frame.winfo_children():
            w.destroy()
        if not self._cart:
            ctk.CTkLabel(self._cart_frame, text="Keranjang kosong", font=ctk.CTkFont(size=13), text_color=TEXT_SEC).pack(pady=30)
            self._total_lbl.configure(text="Total: Rp 0")
            self._item_count_lbl.configure(text="0 jenis barang")
            return

        total = 0
        for entry in self._cart:
            total += entry["subtotal"]
            row = ctk.CTkFrame(self._cart_frame, fg_color=_card(), corner_radius=8)
            row.pack(fill="x", padx=4, pady=3)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=entry["name"], font=ctk.CTkFont(size=11), anchor="w").grid(row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=(6,2))
            ctk.CTkLabel(row, text=f"Rp {entry['price']:,.0f}".replace(",","."), font=ctk.CTkFont(size=10), text_color=TEXT_SEC, anchor="w").grid(row=1, column=0, padx=10, pady=(0,6))

            qf = ctk.CTkFrame(row, fg_color="transparent")
            qf.grid(row=1, column=1, sticky="e", padx=8, pady=(0,6))
            code_ref = entry["code"]
            
            ctk.CTkButton(qf, text="−", width=26, height=24, fg_color="#F0F4FF", text_color=PRIMARY, hover_color="#D0DCFF", corner_radius=6, command=lambda c=code_ref: self._change_qty(c,-1)).pack(side="left",padx=2)
            
            qty_ent = ctk.CTkEntry(qf, width=40, height=24, justify="center", font=ctk.CTkFont(size=12, weight="bold"), corner_radius=6, border_width=1)
            qty_ent.insert(0, str(entry["qty"]))
            qty_ent.pack(side="left", padx=2)
            
            qty_ent.bind("<Return>", lambda e, c=code_ref, ent=qty_ent: self._on_qty_change(c, ent.get()))
            qty_ent.bind("<FocusOut>", lambda e, c=code_ref, ent=qty_ent: self._on_qty_change(c, ent.get()))

            ctk.CTkButton(qf, text="+", width=26, height=24, fg_color=PRIMARY, text_color="#FFFFFF", hover_color="#1650A0", corner_radius=6, command=lambda c=code_ref: self._change_qty(c,1)).pack(side="left",padx=2)

            sub_fmt = f"Rp {entry['subtotal']:,.0f}".replace(",",".")
            ctk.CTkLabel(row, text=sub_fmt, font=ctk.CTkFont(size=11, weight="bold"), text_color=PRIMARY).grid(row=1, column=2, padx=8, pady=(0,6))
            ctk.CTkButton(row, text="✕", width=24, height=24, fg_color="#FFECEC", text_color=RED, hover_color="#FFD5D5", corner_radius=5, command=lambda c=code_ref: self._remove_from_cart(c)).grid(row=1, column=3, padx=(0,8), pady=(0,6))

        self._total_lbl.configure(text=f"Total: Rp {total:,.0f}".replace(",","."))
        self._item_count_lbl.configure(text=f"{len(self._cart)} jenis barang")

    def _change_qty(self, code, delta):
        for e in self._cart:
            if e["code"] == code:
                new_qty = e["qty"] + delta
                if new_qty <= 0:
                    self._cart.remove(e)
                elif new_qty <= e["max_qty"]:
                    e["qty"] = new_qty
                    e["subtotal"] = new_qty * e["price"]
                break
        self._render_cart()

    def _on_qty_change(self, code, entry_val):
        target_entry = None
        for e in self._cart:
            if e["code"] == code:
                target_entry = e
                break
        if not target_entry: return
            
        try: new_qty = int(entry_val)
        except ValueError: self._render_cart(); return
            
        if new_qty == target_entry["qty"]: return
            
        if new_qty <= 0:
            self._cart.remove(target_entry)
        elif new_qty <= target_entry["max_qty"]:
            target_entry["qty"] = new_qty
            target_entry["subtotal"] = new_qty * target_entry["price"]
        else:
            target_entry["qty"] = target_entry["max_qty"]
            target_entry["subtotal"] = target_entry["max_qty"] * target_entry["price"]
            self._toast(f"Stok tidak mencukupi! Maksimal {target_entry['max_qty']}", error=True)
            
        self._render_cart()

    def _remove_from_cart(self, code):
        self._cart = [e for e in self._cart if e["code"] != code]
        self._render_cart()

    def _clear_cart(self):
        self._cart = []
        self._render_cart()

    def _checkout(self):
        if not self._cart:
            self._toast("Keranjang masih kosong!", error=True); return
        total = sum(e["subtotal"] for e in self._cart)

        dlg = ctk.CTkToplevel(self)
        dlg.title("Konfirmasi Penjualan")
        dlg.geometry("400x420")
        dlg.resizable(True, True)
        dlg.grab_set()
        dlg.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dlg, text="✅ Konfirmasi Penjualan", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(20,10), sticky="w")

        body = ctk.CTkScrollableFrame(dlg, height=140)
        body.grid(row=1, column=0, sticky="ew", padx=20)
        body.grid_columnconfigure(1, weight=1)
        for e in self._cart:
            ctk.CTkLabel(body, text=f"{e['name']} x{e['qty']}", font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w")

        ctk.CTkLabel(dlg, text=f"Total: Rp {total:,.0f}".replace(",","."), font=ctk.CTkFont(size=15, weight="bold"), text_color=PRIMARY).grid(row=2, column=0, padx=20, pady=8, sticky="w")

        br = ctk.CTkFrame(dlg, fg_color="transparent")
        br.grid(row=3, column=0, padx=20, pady=(0,20), sticky="e")

        def confirm():
            for entry in self._cart:
                try: item = self.inventory_manager.get_item(entry["code"])
                except AttributeError: item = self.inventory_manager.search_by_code(entry["code"])
                    
                if item:
                    self.sales_manager.record_sale(item, entry["qty"])
                    current_qty = item.get("qty", item.get("jumlah", 0))
                    new_qty = max(0, current_qty - entry["qty"])
                    updated = dict(item)
                    updated["qty"] = new_qty
                    updated["jumlah"] = new_qty
                    self.inventory_manager.update_item(entry["code"], updated)
            
            if hasattr(self.inventory_manager, 'autosave'):
                self.inventory_manager.autosave()
                
            dlg.destroy()
            self._cart = []
            self._render_cart()
            self._pos_search_items()
            self._toast(f"✅ Penjualan berhasil! Total: Rp {total:,.0f}".replace(",","."))

        ctk.CTkButton(br, text="Batal", width=90, height=34, fg_color="transparent", border_width=1, text_color=TEXT_PRI, corner_radius=8, command=dlg.destroy).pack(side="left", padx=(0,8))
        ctk.CTkButton(br, text="✅ Konfirmasi", width=130, height=34, fg_color=GREEN, hover_color="#157A38", text_color="#FFFFFF", corner_radius=8, command=confirm).pack(side="left")

    def _build_history_page(self):
        page = ctk.CTkFrame(self._content, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        # Menambahkan baris kosong penyerap sisa layar di baris bawah
        page.grid_rowconfigure(2, weight=1)
        page.grid_columnconfigure(0, weight=1)
        self._pages["history"] = page

        self._summary_frame = ctk.CTkFrame(page, fg_color="transparent")
        self._summary_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(8,8))
        for i in range(4): self._summary_frame.grid_columnconfigure(i, weight=1)

        tbl_wrap = ctk.CTkFrame(page, fg_color="transparent")
        tbl_wrap.grid(row=1, column=0, sticky="ew", padx=24, pady=(0,4))
        tbl_wrap.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(tbl_wrap, fg_color=PRIMARY, corner_radius=8, height=36)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0,4))
        hdr.pack_propagate(False)
        
        for name, width, align in zip(HIST_HEADERS, HIST_WIDTHS, HIST_ALIGNS):
            lbl = ctk.CTkLabel(hdr, text=name, width=width, anchor=align,
                               text_color="#FFFFFF", font=ctk.CTkFont(size=11, weight="bold"),
                               fg_color="transparent")
            lbl.pack(side="left", padx=6, pady=6)

        self._hist_body = ctk.CTkScrollableFrame(tbl_wrap, corner_radius=8, height=500)
        self._hist_body.grid(row=1, column=0, sticky="ew")
        self._hist_body.grid_columnconfigure(0, weight=1)
        
        self._hist_pag_frame = ctk.CTkFrame(tbl_wrap, fg_color="transparent")
        self._hist_pag_frame.grid(row=2, column=0, sticky="ew", pady=(8,0))
        self._hist_pag_frame.grid_columnconfigure((0,2), weight=1)
        
        self._hist_prev_btn = ctk.CTkButton(self._hist_pag_frame, text="<", width=35, command=lambda: self._change_hist_page(-1))
        self._hist_prev_btn.grid(row=0, column=0, sticky="e", padx=10)
        self._hist_page_lbl = ctk.CTkLabel(self._hist_pag_frame, text="Halaman 1 / 1", font=ctk.CTkFont(size=12))
        self._hist_page_lbl.grid(row=0, column=1)
        self._hist_next_btn = ctk.CTkButton(self._hist_pag_frame, text=">", width=35, command=lambda: self._change_hist_page(1))
        self._hist_next_btn.grid(row=0, column=2, sticky="w", padx=10)

    def _load_history(self):
        for w in self._summary_frame.winfo_children(): w.destroy()
        s = self.sales_manager.get_summary()
        rev_fmt = f"Rp {s['total_revenue']:,.0f}".replace(",",".")
        cards = [
            ("💳","Total Transaksi",    str(s["total_trx"]),       "#EBF2FF",PRIMARY),
            ("💰","Total Revenue",       rev_fmt,                   "#F4EEFF","#6B3FC0"),
            ("📦","Total Qty Terjual",  str(s["total_qty_sold"]),  "#EAF7EC",GREEN),
            ("🏆","Item Terlaris",      f"{s['top_item']}",        "#FFF5E6",ORANGE),
        ]
        for i,(icon,label,val,bg,col) in enumerate(cards):
            c = ctk.CTkFrame(self._summary_frame, fg_color=bg, corner_radius=10)
            c.grid(row=0, column=i, sticky="ew", padx=(0 if i==0 else 6,0), ipady=6)
            c.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(c, text=icon, font=ctk.CTkFont(size=24), text_color=col).grid(row=0, column=0, rowspan=2, padx=(12,6))
            ctk.CTkLabel(c, text=val, font=ctk.CTkFont(size=15, weight="bold"), text_color=col, anchor="w").grid(row=0, column=1, sticky="sw", padx=(0,10))
            ctk.CTkLabel(c, text=label, font=ctk.CTkFont(size=10), text_color=TEXT_SEC, anchor="w").grid(row=1, column=1, sticky="nw", padx=(0,10))

        self._hist_results = self.sales_manager.get_recent(1000)
        self._hist_page = 0
        self._render_hist_page()
        
    def _render_hist_page(self):
        for w in self._hist_body.winfo_children(): w.destroy()
        
        total_pages = max(1, math.ceil(len(self._hist_results) / ROWS_PER_PAGE))
        self._hist_page_lbl.configure(text=f"Halaman {self._hist_page + 1} / {total_pages}")
        self._hist_prev_btn.configure(state="normal" if self._hist_page > 0 else "disabled")
        self._hist_next_btn.configure(state="normal" if self._hist_page < total_pages - 1 else "disabled")

        if not self._hist_results:
            ctk.CTkLabel(self._hist_body, text="Belum ada transaksi.", font=ctk.CTkFont(size=13), text_color=TEXT_SEC).pack(pady=30)
            return
            
        start = self._hist_page * ROWS_PER_PAGE
        end = start + ROWS_PER_PAGE
        
        for i, s in enumerate(self._hist_results[start:end]):
            bg_row = _row_bg(i % 2 == 0)
            
            row = ctk.CTkFrame(self._hist_body, fg_color=bg_row, corner_radius=6, height=38)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            
            sub_fmt = f"Rp {float(s.get('subtotal',0)):,.0f}".replace(",",".")
            vals = [
                s.get("sale_id", ""),
                s.get("date", ""),
                s.get("time", "")[:5],
                s.get("item_name", ""),
                str(s.get("qty_sold", "")),
                sub_fmt
            ]
            
            for val, width, align in zip(vals, HIST_WIDTHS[:-1], HIST_ALIGNS[:-1]):
                lbl = ctk.CTkLabel(row, text=val, width=width, anchor=align, font=ctk.CTkFont(size=11))
                lbl.pack(side="left", padx=6, pady=4)
                
            btn_width = HIST_WIDTHS[-1]
            btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=btn_width)
            btn_frame.pack(side="left", padx=6, pady=2)
            btn_frame.pack_propagate(False)
            
            cancel_btn = ctk.CTkButton(btn_frame, text="Batal", width=btn_width - 10, height=24,
                                       fg_color="#FFECEC", text_color=RED, hover_color="#FFD5D5",
                                       font=ctk.CTkFont(size=10, weight="bold"),
                                       command=lambda trx=s.get("sale_id"): self._confirm_cancel(trx))
            cancel_btn.pack(expand=True)

    def _change_hist_page(self, delta):
        self._hist_page += delta
        self._render_hist_page()
        
    def _confirm_cancel(self, sale_id):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Batal Transaksi")
        dlg.geometry("350x180")
        dlg.resizable(False,False)
        dlg.grab_set()
        
        ctk.CTkLabel(dlg, text="Yakin membatalkan transaksi ini?\nStok barang akan dikembalikan utuh.", font=ctk.CTkFont(size=13)).pack(pady=(30, 20))
        
        br = ctk.CTkFrame(dlg, fg_color="transparent")
        br.pack()
        
        def do_cancel():
            record = self.sales_manager.delete_sale(sale_id)
            if record:
                code = record.get("item_code")
                qty = record.get("qty_sold", 0)
                try: item = self.inventory_manager.get_item(code)
                except AttributeError: item = self.inventory_manager.search_by_code(code)
                    
                if item:
                    new_qty = item.get("qty", item.get("jumlah", 0)) + qty
                    updated = dict(item)
                    updated["qty"] = new_qty
                    updated["jumlah"] = new_qty
                    self.inventory_manager.update_item(code, updated)
                    if hasattr(self.inventory_manager, 'autosave'):
                        self.inventory_manager.autosave()
            
            dlg.destroy()
            self._load_history()
            self._toast("Transaksi berhasil dibatalkan!")
            
        ctk.CTkButton(br, text="Tidak", width=80, fg_color="transparent", text_color=TEXT_PRI, border_width=1, command=dlg.destroy).pack(side="left", padx=10)
        ctk.CTkButton(br, text="Ya, Batal", width=80, fg_color=RED, hover_color="#B31E1E", command=do_cancel).pack(side="left", padx=10)

    def on_show(self):
        self._pos_search_items()

    def _toast(self, msg, error=False):
        color = RED if error else GREEN
        t = ctk.CTkToplevel(self)
        t.overrideredirect(True); t.attributes("-topmost", True)
        ctk.CTkLabel(t, text=msg, fg_color=color, text_color="#FFFFFF", font=ctk.CTkFont(size=12), corner_radius=8, padx=16, pady=10).pack()
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width()//2 - 200
        y = self.winfo_rooty() + self.winfo_height() - 60
        t.geometry(f"+{x}+{y}"); t.after(3000, t.destroy)