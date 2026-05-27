import customtkinter as ctk
from datetime import datetime, date

PRIMARY  = "#1E61B8"; TEXT_SEC = ("#5A6A85", "#A3B1CC"); TEXT_PRI = ("#1C1C1C", "#F2F5F7")
RED      = "#D92626"; GREEN    = "#1A9A4A"; ORANGE   = "#D97800"

ROWS_PER_PAGE = 15

def _is_dark(): return ctk.get_appearance_mode() == "Dark"
def _card(): return "#2A3448" if _is_dark() else "#FFFFFF"


class SalesScreen(ctk.CTkFrame):
    def __init__(self, master, inventory_manager, sales_manager, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=0, **kwargs)
        self.inventory_manager = inventory_manager
        self.sales_manager     = sales_manager
        self._cart             = []   # list of {item, qty, subtotal}
        self._history_page     = 0
        self._history_items    = []

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_layout()
        self.on_show()

    def _build_layout(self):
        # Tabs
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

        # Tab content
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

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 1: POINT OF SALE
    # ═══════════════════════════════════════════════════════════════════════
    def _build_pos_page(self):
        page = ctk.CTkFrame(self._content, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_rowconfigure(1, weight=1)
        page.grid_columnconfigure(0, weight=3)
        page.grid_columnconfigure(1, weight=2)
        self._pages["pos"] = page

        # ── Kiri: pencarian & daftar item ────────────────────────────────
        left = ctk.CTkFrame(page, fg_color="transparent")
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(24,8), pady=0)
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Pilih Barang",
                     font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, sticky="w", pady=(0,8))

        sf = ctk.CTkFrame(left, corner_radius=10, height=42)
        sf.grid(row=1, column=0, sticky="ew", pady=(0,8))
        sf.grid_propagate(False)
        sf.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(sf, text="🔍", font=ctk.CTkFont(size=16),
                     text_color=PRIMARY).grid(row=0, column=0, padx=(12,4))
        self._pos_search = ctk.CTkEntry(sf, height=36, fg_color="transparent",
                                         border_width=0, placeholder_text="Cari kode atau nama...",
                                         font=ctk.CTkFont(size=13), corner_radius=0)
        self._pos_search.grid(row=0, column=1, sticky="ew", padx=(0,12))
        self._pos_search.bind("<KeyRelease>", lambda e: self._pos_search_items())

        self._pos_list = ctk.CTkScrollableFrame(left, corner_radius=8)
        self._pos_list.grid(row=2, column=0, sticky="nsew")
        self._pos_list.grid_columnconfigure(0, weight=1)
        self._pos_search_items()

        # ── Kanan: keranjang & total ──────────────────────────────────────
        right = ctk.CTkFrame(page, fg_color="transparent")
        right.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(8,24), pady=0)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="🛒 Keranjang",
                     font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, sticky="w", pady=(0,8))

        self._cart_frame = ctk.CTkScrollableFrame(right, corner_radius=8)
        self._cart_frame.grid(row=1, column=0, sticky="nsew")
        self._cart_frame.grid_columnconfigure(0, weight=1)

        # Total & checkout
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
        for w in self._pos_list.winfo_children():
            w.destroy()
        all_items = self.inventory_manager.hash_map.all_values()
        results = [i for i in all_items if
                   (query in i.get("code","").upper() or
                    query in i.get("name","").upper())] if query else all_items[:50]
        for item in results[:60]:
            self._pos_item_row(item)

    def _pos_item_row(self, item):
        bg = _card()
        row = ctk.CTkFrame(self._pos_list, fg_color=bg, corner_radius=8)
        row.pack(fill="x", padx=4, pady=3, ipady=4)
        row.grid_columnconfigure(1, weight=1)

        qty_avail = item.get("qty", 0)
        is_empty  = qty_avail <= 0
        col       = TEXT_SEC if is_empty else TEXT_PRI

        ctk.CTkLabel(row, text=item.get("code",""),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=PRIMARY, width=95, anchor="w").grid(
            row=0, column=0, padx=(10,4), pady=4)
        ctk.CTkLabel(row, text=item.get("name",""),
                     font=ctk.CTkFont(size=11), anchor="w",
                     text_color=col).grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkLabel(row, text=f"Stok:{qty_avail}",
                     font=ctk.CTkFont(size=10), text_color=TEXT_SEC, width=55).grid(
            row=0, column=2, padx=4)
        ctk.CTkButton(row, text="+", width=30, height=26,
                      fg_color=PRIMARY if not is_empty else "#CCCCCC",
                      text_color="#FFFFFF", corner_radius=6,
                      font=ctk.CTkFont(size=14),
                      state="normal" if not is_empty else "disabled",
                      command=lambda i=item: self._add_to_cart(i)).grid(
            row=0, column=3, padx=(4,8), pady=4)

    def _add_to_cart(self, item):
        code = item.get("code","")
        for entry in self._cart:
            if entry["code"] == code:
                if entry["qty"] < item.get("qty",0):
                    entry["qty"]      += 1
                    entry["subtotal"]  = entry["qty"] * item.get("price",0)
                self._render_cart()
                return
        self._cart.append({
            "code":     code,
            "name":     item.get("name",""),
            "price":    item.get("price",0),
            "qty":      1,
            "subtotal": item.get("price",0),
            "max_qty":  item.get("qty",0),
        })
        self._render_cart()

    def _render_cart(self):
        for w in self._cart_frame.winfo_children():
            w.destroy()
        if not self._cart:
            ctk.CTkLabel(self._cart_frame, text="Keranjang kosong",
                         font=ctk.CTkFont(size=13), text_color=TEXT_SEC).pack(pady=30)
            self._total_lbl.configure(text="Total: Rp 0")
            self._item_count_lbl.configure(text="0 jenis barang")
            return

        total = 0
        for entry in self._cart:
            total += entry["subtotal"]
            row    = ctk.CTkFrame(self._cart_frame, fg_color=_card(), corner_radius=8)
            row.pack(fill="x", padx=4, pady=3)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=entry["name"],
                         font=ctk.CTkFont(size=11), anchor="w").grid(
                row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=(6,2))

            ctk.CTkLabel(row, text=f"Rp {entry['price']:,.0f}".replace(",","."),
                         font=ctk.CTkFont(size=10), text_color=TEXT_SEC, anchor="w").grid(
                row=1, column=0, padx=10, pady=(0,6))

            # Qty control dengan Entry Input
            qf = ctk.CTkFrame(row, fg_color="transparent")
            qf.grid(row=1, column=1, sticky="e", padx=8, pady=(0,6))
            code_ref = entry["code"]
            
            ctk.CTkButton(qf, text="−", width=26, height=24,
                          fg_color="#F0F4FF", text_color=PRIMARY,
                          hover_color="#D0DCFF", corner_radius=6,
                          font=ctk.CTkFont(size=13),
                          command=lambda c=code_ref: self._change_qty(c,-1)).pack(side="left",padx=2)
            
            qty_ent = ctk.CTkEntry(qf, width=40, height=24, justify="center",
                                   font=ctk.CTkFont(size=12, weight="bold"),
                                   corner_radius=6, border_width=1)
            qty_ent.insert(0, str(entry["qty"]))
            qty_ent.pack(side="left", padx=2)
            
            qty_ent.bind("<Return>", lambda e, c=code_ref, ent=qty_ent: self._on_qty_change(c, ent.get()))
            qty_ent.bind("<FocusOut>", lambda e, c=code_ref, ent=qty_ent: self._on_qty_change(c, ent.get()))

            ctk.CTkButton(qf, text="+", width=26, height=24,
                          fg_color=PRIMARY, text_color="#FFFFFF",
                          hover_color="#1650A0", corner_radius=6,
                          font=ctk.CTkFont(size=13),
                          command=lambda c=code_ref: self._change_qty(c,1)).pack(side="left",padx=2)

            sub_fmt = f"Rp {entry['subtotal']:,.0f}".replace(",",".")
            ctk.CTkLabel(row, text=sub_fmt,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=PRIMARY).grid(row=1, column=2, padx=8, pady=(0,6))
            ctk.CTkButton(row, text="✕", width=24, height=24,
                          fg_color="#FFECEC", text_color=RED,
                          hover_color="#FFD5D5", corner_radius=5,
                          font=ctk.CTkFont(size=11),
                          command=lambda c=code_ref: self._remove_from_cart(c)).grid(
                row=1, column=3, padx=(0,8), pady=(0,6))

        total_fmt = f"Rp {total:,.0f}".replace(",",".")
        self._total_lbl.configure(text=f"Total: {total_fmt}")
        self._item_count_lbl.configure(text=f"{len(self._cart)} jenis barang")

    def _change_qty(self, code, delta):
        for e in self._cart:
            if e["code"] == code:
                new_qty = e["qty"] + delta
                if new_qty <= 0:
                    self._cart.remove(e)
                elif new_qty <= e["max_qty"]:
                    e["qty"]     = new_qty
                    e["subtotal"] = new_qty * e["price"]
                break
        self._render_cart()

    def _on_qty_change(self, code, entry_val):
        target_entry = None
        for e in self._cart:
            if e["code"] == code:
                target_entry = e
                break
        if not target_entry:
            return
            
        try:
            new_qty = int(entry_val)
        except ValueError:
            self._render_cart()
            return
            
        if new_qty == target_entry["qty"]:
            return
            
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

        # Konfirmasi dialog
        dlg = ctk.CTkToplevel(self)
        dlg.title("Konfirmasi Penjualan")
        dlg.geometry("400x300")
        dlg.resizable(False,False)
        dlg.grab_set()
        dlg.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dlg, text="✅ Konfirmasi Penjualan",
                     font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(20,10), sticky="w")

        body = ctk.CTkScrollableFrame(dlg, height=140)
        body.grid(row=1, column=0, sticky="ew", padx=20)
        body.grid_columnconfigure(1, weight=1)
        for e in self._cart:
            ctk.CTkLabel(body, text=f"{e['name']} x{e['qty']}",
                         font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w")

        ctk.CTkLabel(dlg,
                     text=f"Total: Rp {total:,.0f}".replace(",","."),
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=PRIMARY).grid(row=2, column=0, padx=20, pady=8, sticky="w")

        br = ctk.CTkFrame(dlg, fg_color="transparent")
        br.grid(row=3, column=0, padx=20, pady=(0,20), sticky="e")

        def confirm():
            for entry in self._cart:
                item = self.inventory_manager.get_item(entry["code"])
                if item:
                    self.sales_manager.record_sale(item, entry["qty"])
                    new_qty = max(0, item.get("qty",0) - entry["qty"])
                    updated = dict(item)
                    updated["qty"]    = new_qty
                    updated["jumlah"] = new_qty
                    self.inventory_manager.update_item(entry["code"], updated)
                    self.inventory_manager.autosave()
            dlg.destroy()
            self._cart = []
            self._render_cart()
            self._pos_search_items()
            self._toast(f"✅ Penjualan berhasil! Total: Rp {total:,.0f}".replace(",","."))

        ctk.CTkButton(br, text="Batal", width=90, height=34,
                      fg_color="transparent", border_width=1,
                      text_color=TEXT_PRI, corner_radius=8,
                      command=dlg.destroy).pack(side="left", padx=(0,8))
        ctk.CTkButton(br, text="✅ Konfirmasi", width=130, height=34,
                      fg_color=GREEN, hover_color="#157A38", text_color="#FFFFFF",
                      corner_radius=8, command=confirm).pack(side="left")

    # ═══════════════════════════════════════════════════════════════════════
    # TAB 2: RIWAYAT & STATISTIK
    # ═══════════════════════════════════════════════════════════════════════
    def _build_history_page(self):
        page = ctk.CTkFrame(self._content, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_rowconfigure(1, weight=1)
        page.grid_columnconfigure(0, weight=1)
        self._pages["history"] = page

        # Summary cards
        self._summary_frame = ctk.CTkFrame(page, fg_color="transparent")
        self._summary_frame.grid(row=0, column=0, sticky="ew", padx=24, pady=(8,8))
        for i in range(4): self._summary_frame.grid_columnconfigure(i, weight=1)

        # Table
        tbl_wrap = ctk.CTkFrame(page, fg_color="transparent")
        tbl_wrap.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0,4))
        tbl_wrap.grid_rowconfigure(1, weight=1)
        tbl_wrap.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(tbl_wrap, fg_color=PRIMARY, corner_radius=8, height=32)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0,2))
        hdr.pack_propagate(False)
        for col, w in [("TRX ID",90),("TANGGAL",95),("WAKTU",75),
                       ("ITEM",0),("QTY",50),("TOTAL",120)]:
            kw = dict(text=col, fg_color="transparent", text_color="#FFFFFF",
                      font=ctk.CTkFont(size=10, weight="bold"), anchor="center")
            if w: kw["width"] = w
            lbl = ctk.CTkLabel(hdr, **kw)
            if w: lbl.pack(side="left", padx=3, pady=5)
            else: lbl.pack(side="left", fill="x", expand=True, padx=3, pady=5)

        self._hist_body = ctk.CTkScrollableFrame(tbl_wrap, corner_radius=8)
        self._hist_body.grid(row=1, column=0, sticky="nsew")
        self._hist_body.grid_columnconfigure(0, weight=1)

    def _load_history(self):
        # Summary
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
            ctk.CTkLabel(c, text=icon, font=ctk.CTkFont(size=24),
                         text_color=col).grid(row=0, column=0, rowspan=2, padx=(12,6))
            ctk.CTkLabel(c, text=val, font=ctk.CTkFont(size=15, weight="bold"),
                         text_color=col, anchor="w").grid(row=0, column=1, sticky="sw", padx=(0,10))
            ctk.CTkLabel(c, text=label, font=ctk.CTkFont(size=10),
                         text_color=TEXT_SEC, anchor="w").grid(row=1, column=1, sticky="nw", padx=(0,10))

        # History rows
        for w in self._hist_body.winfo_children(): w.destroy()
        sales = self.sales_manager.get_recent(100)
        if not sales:
            ctk.CTkLabel(self._hist_body, text="Belum ada transaksi.",
                         font=ctk.CTkFont(size=13), text_color=TEXT_SEC).pack(pady=30)
            return
        for i, s in enumerate(sales):
            bg_row = ("#1E2A3E" if i%2==0 else "#172030") if _is_dark() else \
                     ("#F0F5FF" if i%2==0 else "#FFFFFF")
            row = ctk.CTkFrame(self._hist_body, fg_color=bg_row, corner_radius=6)
            row.pack(fill="x", pady=1)
            sub_fmt = f"Rp {float(s.get('subtotal',0)):,.0f}".replace(",",".")
            for text, w in [
                (s.get("sale_id",""),90), (s.get("date",""),95),
                (s.get("time","")[:5],75), (s.get("item_name",""),0),
                (str(s.get("qty_sold","")),50), (sub_fmt,120)
            ]:
                kw = dict(text=text, fg_color="transparent",
                          font=ctk.CTkFont(size=11), anchor="w" if w==0 else "center")
                if w: kw["width"] = w
                lbl = ctk.CTkLabel(row, **kw)
                if w: lbl.pack(side="left", padx=3, pady=5)
                else: lbl.pack(side="left", fill="x", expand=True, padx=3, pady=5)

    def on_show(self):
        self._pos_search_items()

    def _toast(self, msg, error=False):
        color = RED if error else GREEN
        t = ctk.CTkToplevel(self)
        t.overrideredirect(True); t.attributes("-topmost", True)
        ctk.CTkLabel(t, text=msg, fg_color=color, text_color="#FFFFFF",
                     font=ctk.CTkFont(size=12), corner_radius=8,
                     padx=16, pady=10).pack()
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width()//2 - 200
        y = self.winfo_rooty() + self.winfo_height() - 60
        t.geometry(f"+{x}+{y}"); t.after(3000, t.destroy)