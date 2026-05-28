# screens/priority_screen.py
import customtkinter as ctk
from datetime import datetime, date

PRIMARY      = "#1E61B8"
TEXT_SEC     = "#7A8A9A"
TEXT_PRI     = "#1A2A3A"
RED          = "#D92626"
GREEN        = "#1A9A4A"

BADGE_COLORS = ["#D93333", "#E68010", "#3399D9", "#2DA65C", "#7B55CC",
                "#C44D8A", "#1A8C6A", "#B05010"]

# Konfigurasi dasar tabel yang dibagikan secara konsisten
COL_HEADERS  = ["#", "CODE", "NAME", "PRIORITY", "CATEGORY", "QTY", "ACTION"]
COL_WIDTHS   = [50, 100, 150, 150, 130, 55, 100]
COL_ALIGNS   = ["center", "w", "w", "center", "w", "center", "center"]

ROWS_PER_PAGE = 10


def _is_dark():
    return ctk.get_appearance_mode() == "Dark"

def _row_bg(even: bool):
    if _is_dark():
        return "#1E2A3E" if even else "#172030"
    return "#F0F5FF" if even else "#FFFFFF"

def _table_bg():
    return "#172030" if _is_dark() else "#FFFFFF"


class PriorityScreen(ctk.CTkFrame):
    def __init__(self, master, inventory_manager, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=0, **kwargs)
        self.inventory_manager = inventory_manager
        self.mode              = "price_min"
        self._current_page     = 0
        self._all_items        = []

        self.grid_rowconfigure(2, weight=1) # Diubah ke indeks 2 karena layout disatukan
        self.grid_columnconfigure(0, weight=1)
        self._build_layout()
        self.on_show()

    # ── Build Layout ──────────────────────────────────────────────────────────
    def _build_layout(self):
        # Header Aplikasi
        hdr = ctk.CTkFrame(self, fg_color="transparent", height=50)
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 0))
        hdr.grid_propagate(False)
        ctk.CTkLabel(hdr, text="Priority Queue",
                     font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, sticky="w")
        self._subtitle = ctk.CTkLabel(hdr, text="Mode: Min Price",
                                       font=ctk.CTkFont(size=12), text_color=TEXT_SEC)
        self._subtitle.grid(row=1, column=0, sticky="w")

        # Controls (Tombol-tombol pilihan mode)
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.grid(row=1, column=0, sticky="ew", padx=24, pady=(10, 8))
        ctrl.grid_columnconfigure(2, weight=1)

        tab_bg = ctk.CTkFrame(ctrl, fg_color="#E4EDF7", corner_radius=10)
        tab_bg.grid(row=0, column=0)

        self._mode_btns = {}
        for key, label in [("price_min", "🏷 Cheapest"),
                            ("price_max", "💎 Costliest"),
                            ("expiry_min", "📅 Soonest Expiry")]:
            btn = ctk.CTkButton(tab_bg, text=label, height=36, width=140,
                                 fg_color="transparent", text_color=TEXT_SEC,
                                 hover_color="#C8DDEF", corner_radius=8,
                                 font=ctk.CTkFont(size=12),
                                 command=lambda k=key: self.set_mode(k))
            btn.pack(side="left", padx=3, pady=3)
            self._mode_btns[key] = btn

        # Stat pills
        stat_f = ctk.CTkFrame(ctrl, fg_color="transparent")
        stat_f.grid(row=0, column=1, padx=(12, 0))
        self._queue_lbl = ctk.CTkLabel(stat_f, text="",
                                        font=ctk.CTkFont(size=12),
                                        fg_color="#EBF2FF", corner_radius=8,
                                        text_color=PRIMARY, padx=10, pady=4)
        self._queue_lbl.pack(side="left", padx=(0, 6))
        self._near_lbl = ctk.CTkLabel(stat_f, text="",
                                       font=ctk.CTkFont(size=12),
                                       fg_color="#FFF5E6", corner_radius=8,
                                        text_color="#D97800", padx=10, pady=4)
        self._near_lbl.pack(side="left")

        ctk.CTkButton(ctrl, text="⬆ Pop Top", width=110, height=36,
                      fg_color=GREEN, hover_color="#157A38",
                      font=ctk.CTkFont(size=12), corner_radius=8,
                      command=self.pop_top).grid(row=0, column=3, padx=(8, 0))

        # FIX UTAMA: Wadah besar Table Outer menampung Header sekaligus Body
        self._table_outer = ctk.CTkFrame(self, fg_color=_table_bg(), corner_radius=8)
        self._table_outer.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 4))
        self._table_outer.grid_columnconfigure(0, weight=1)
        self._table_outer.grid_rowconfigure(1, weight=1) # Row 0 untuk Header, Row 1 untuk isi tabel

        # Build Table Header di dalam table_outer
        self._build_table_header()

        # Build Table Body di dalam table_outer (Row 1)
        self._table = ctk.CTkFrame(self._table_outer, fg_color="transparent")
        self._table.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self._table.grid_columnconfigure(0, weight=1)

        self._build_pagination_bar()

    def _build_table_header(self):
        # Header diletakkan di row=0 dalam table_outer dengan padding internal yang presisi
        self._tbl_hdr = ctk.CTkFrame(self._table_outer, fg_color=PRIMARY, corner_radius=8, height=34)
        self._tbl_hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        self._tbl_hdr.grid_propagate(False)
        self._priority_hdr_lbl = None
        
        for i, (col, w, align) in enumerate(zip(COL_HEADERS, COL_WIDTHS, COL_ALIGNS)):
            # FIX: Ditambahkan uniform="table_col" untuk mengunci perhitungan pembagian piksel grid
            self._tbl_hdr.grid_columnconfigure(i, minsize=w, weight=w, uniform="table_col")
            
            lbl = ctk.CTkLabel(self._tbl_hdr, text=col,
                                font=ctk.CTkFont(size=11, weight="bold"),
                                text_color="#FFFFFF", anchor=align)
            # Menggunakan sticky="nsew" agar sel label melebar sempurna mengikuti grid uniform
            lbl.grid(row=0, column=i, sticky="nsew", padx=6, pady=4)
            
            if col == "PRIORITY":
                self._priority_hdr_lbl = lbl

    def _build_pagination_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent", height=40)
        bar.grid(row=3, column=0, sticky="ew", padx=24, pady=(2, 12))
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

    # ── Data & Render ─────────────────────────────────────────────────────────
    def on_show(self):
        self._table_outer.configure(fg_color=_table_bg())
        self.set_mode(self.mode)

    def set_mode(self, mode):
        self.mode          = mode
        self._current_page = 0

        for k, btn in self._mode_btns.items():
            btn.configure(fg_color=PRIMARY if k == mode else "transparent",
                          text_color="#FFFFFF" if k == mode else TEXT_SEC)

        if mode.startswith("price"):
            label = "Min Price" if mode == "price_min" else "Max Price"
            if self._priority_hdr_lbl:
                self._priority_hdr_lbl.configure(text="PRICE (Rp)")
        else:
            label = "Soonest Expiry"
            if self._priority_hdr_lbl:
                self._priority_hdr_lbl.configure(text="EXPIRY DATE")

        self._subtitle.configure(text=f"Mode: {label} Priority")
        self._load_items()
        self._render_page()

    def _get_pq(self):
        if self.mode == "price_min": return self.inventory_manager.pq_price_min
        if self.mode == "price_max": return self.inventory_manager.pq_price_max
        return self.inventory_manager.pq_expiry

    def _load_items(self):
        pq = self._get_pq()
        self._all_items = pq.to_sorted_list()
        self._queue_lbl.configure(text=f"🔢 {len(self._all_items)} in queue")

        today = date.today()
        near  = sum(
            1 for item in self.inventory_manager.hash_map.all_values()
            if item.get("expiry_date") and
            (lambda s: (datetime.strptime(s, "%Y-%m-%d").date() - today).days <= 180
             if s else False)(item.get("expiry_date", ""))
        )
        self._near_lbl.configure(text=f"⚠ {near} near expiry")

    def _total_pages(self):
        return max(1, -(-len(self._all_items) // ROWS_PER_PAGE))

    def _render_page(self):
        for w in self._table.winfo_children():
            w.destroy()

        n_pages    = self._total_pages()
        start      = self._current_page * ROWS_PER_PAGE
        end        = min(start + ROWS_PER_PAGE, len(self._all_items))
        page_items = self._all_items[start:end]

        self._page_lbl.configure(text=f"Page {self._current_page + 1} / {n_pages}")
        self._prev_btn.configure(state="normal" if self._current_page > 0 else "disabled")
        self._next_btn.configure(state="normal" if self._current_page < n_pages - 1 else "disabled")

        for i, item in enumerate(page_items):
            self._add_row(i, item, start + i)

    def _add_row(self, row_idx, item, absolute_idx):
        bg = _row_bg(row_idx % 2 == 0)

        row_frame = ctk.CTkFrame(self._table, fg_color=bg, corner_radius=6)
        row_frame.grid(row=row_idx, column=0, sticky="ew", pady=2)

        for i, w in enumerate(COL_WIDTHS):
            # FIX: Ditambahkan uniform="table_col" agar pembagian rasio lebar identik dengan Header
            row_frame.grid_columnconfigure(i, minsize=w, weight=w, uniform="table_col")

        # Col 0: Rank badge (Bentuk lingkaran/kotak fix -> Gunakan sticky="")
        badge_col = BADGE_COLORS[row_idx % len(BADGE_COLORS)]
        badge = ctk.CTkFrame(row_frame, fg_color=badge_col, corner_radius=14,
                              width=28, height=28)
        badge.grid(row=0, column=0, sticky="", padx=6, pady=6) 
        badge.grid_propagate(False)
        ctk.CTkLabel(badge, text=str(absolute_idx + 1),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")

        # Col 1: Code (Text -> Gunakan sticky="nsew")
        ctk.CTkLabel(row_frame, text=item.get("code", ""),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=PRIMARY, anchor=COL_ALIGNS[1]).grid(
            row=0, column=1, sticky="nsew", padx=6, pady=6)

        # Col 2: Name (Text -> Gunakan sticky="nsew")
        ctk.CTkLabel(row_frame, text=item.get("name", ""),
                     font=ctk.CTkFont(size=11), anchor=COL_ALIGNS[2]).grid(
            row=0, column=2, sticky="nsew", padx=6, pady=6)

        # Col 3: PRIORITY value (Text -> Gunakan sticky="nsew")
        if self.mode.startswith("price"):
            pval = f"Rp {item.get('price', 0):,.0f}".replace(",", ".")
            pcol = PRIMARY
        else:
            pval  = item.get("expiry_date", "") or "—"
            exp_s = item.get("expiry_date", "")
            try:
                delta = (datetime.strptime(exp_s, "%Y-%m-%d").date() - date.today()).days
                pcol = RED if delta < 0 else ("#D97800" if delta <= 180 else GREEN)
            except Exception:
                pcol = TEXT_SEC

        ctk.CTkLabel(row_frame, text=pval,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=pcol, anchor=COL_ALIGNS[3]).grid(
            row=0, column=3, sticky="nsew", padx=6, pady=6)

        # Col 4: Category (Text -> Gunakan sticky="nsew")
        ctk.CTkLabel(row_frame, text=item.get("category", ""),
                     font=ctk.CTkFont(size=11), text_color=TEXT_SEC,
                     anchor=COL_ALIGNS[4]).grid(
            row=0, column=4, sticky="nsew", padx=6, pady=6)

        # Col 5: QTY (Text -> Gunakan sticky="nsew")
        ctk.CTkLabel(row_frame, text=str(item.get("qty", 0)),
                     font=ctk.CTkFont(size=11),
                     anchor=COL_ALIGNS[5]).grid(row=0, column=5, sticky="nsew", padx=6, pady=6)

        # Col 6: Action Button (Tombol ukuran fix -> Gunakan sticky="")
        code = item.get("code", "")
        btn = ctk.CTkButton(row_frame, text="Pop ✕", width=62, height=26,
                             fg_color="#FFECEC", text_color=RED,
                             hover_color="#FFD5D5", corner_radius=6,
                             font=ctk.CTkFont(size=11),
                             command=lambda c=code: self._pop_item(c))
        btn.grid(row=0, column=6, sticky="", padx=6, pady=6)

    # ── Pagination & Actions ──────────────────────────────────────────────────
    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_page()

    def _next_page(self):
        if self._current_page < self._total_pages() - 1:
            self._current_page += 1
            self._render_page()

    def pop_top(self):
        pq = self._get_pq()
        try:
            # Mengeluarkan item teratas dari antrean saat ini
            item = pq.pop()
            if item:
                # Mengambil kode barang untuk dihapus dari semua sistem
                code = item.get("code", "")
                
                # Memerintahkan pengelola inventaris untuk menghapus permanen
                self.inventory_manager.remove_item(code)
                # Menyimpan perubahan agar hilang dari file CSV
                self.inventory_manager.autosave()
                
                self._show_toast(f"⬆ Popped & Removed: {code} — {item.get('name')}")
                self._current_page = 0
                self._load_items()
                self._render_page()
        except IndexError:
            self._show_toast("Queue is empty!", error=True)

    def _pop_item(self, code):
        # Memerintahkan pengelola inventaris untuk menghapus barang secara keseluruhan
        sukses = self.inventory_manager.remove_item(code)
        
        if sukses:
            # Menyimpan perubahan agar hilang dari file CSV
            self.inventory_manager.autosave()
            self._show_toast(f"Permanently removed {code}")
        else:
            self._show_toast(f"Gagal menghapus {code}", error=True)
            
        self._load_items()
        
        # Memastikan halaman tidak kosong jika data di halaman terakhir habis terhapus
        if self._current_page >= self._total_pages():
            self._current_page = max(0, self._total_pages() - 1)
        self._render_page()

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