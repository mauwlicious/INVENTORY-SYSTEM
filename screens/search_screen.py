# screens/search_screen.py
import customtkinter as ctk

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
        search_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(16,12))
        search_frame.grid_propagate(False)
        search_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=20),
                     text_color=PRIMARY).grid(row=0, column=0, padx=(16,4))
        self._search_entry = ctk.CTkEntry(
            search_frame, height=40,
            placeholder_text="Enter item code (e.g. ELC-0001)...",
            fg_color="transparent", border_width=0,
            font=ctk.CTkFont(size=14), corner_radius=0)
        self._search_entry.grid(row=0, column=1, sticky="ew", padx=(0,16))
        self._search_entry.bind("<KeyRelease>", lambda e: self._do_search())

        ctk.CTkLabel(self, text='💡 Tip: type any part of the code — e.g. "ELC", "MED-0"',
                     font=ctk.CTkFont(size=11), text_color=TEXT_SEC).grid(
            row=2, column=0, sticky="w", padx=28, pady=(0,6))

        self._result = ctk.CTkScrollableFrame(self, corner_radius=12)
        self._result.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0,16))
        self._result.grid_columnconfigure(0, weight=1)
        self._show_placeholder()

    def on_show(self):
        pass

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
                     font=ctk.CTkFont(size=14), text_color=TEXT_SEC).pack(pady=40, padx=20)

    def _show_not_found(self, text):
        ctk.CTkLabel(self._result, text=f'❌ No item found with code "{text}"',
                     font=ctk.CTkFont(size=14), text_color=RED).pack(pady=40)

    def _show_item(self, item, exact=False):
        ctk.CTkLabel(self._result,
                     text="✅ Item Found (Exact Match)" if exact else "✅ Item Found",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=GREEN).pack(anchor="w", padx=20, pady=(16,8))
        fields = [
            ("Code",        item.get("code", "")),
            ("Name",        item.get("name", "")),
            ("Category",    item.get("category", "")),
            ("Quantity",    str(item.get("qty", 0))),
            ("Price",       f"Rp {item.get('price', 0):,.0f}".replace(",", ".")),
            ("Expiry Date", item.get("expiry_date", "") or "—"),
            ("Store",       item.get("lokasi", item.get("store", "—"))),
        ]
        for label, value in fields:
            row = ctk.CTkFrame(self._result, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=3)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=f"{label}:",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=TEXT_SEC, width=120, anchor="w").grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(row, text=value,
                         font=ctk.CTkFont(size=13), anchor="w").grid(row=0, column=1, sticky="w", padx=8)

    def _show_multi(self, results):
        ctk.CTkLabel(self._result, text=f"🔍 Found {len(results)} matching items",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=PRIMARY).pack(anchor="w", padx=20, pady=(16,8))
        
        for i, item in enumerate(results[:50]):
            row = ctk.CTkFrame(self._result, corner_radius=8)
            row.pack(fill="x", padx=12, pady=2, ipady=6)
            
            # --- PERBAIKAN UTAMA: Kunci ukuran lebar setiap kolom ---
            row.grid_columnconfigure(0, minsize=110, weight=0)  # Kolom CODE
            row.grid_columnconfigure(1, weight=1)               # Kolom NAME (Dibuat fleksibel mengisi sisa ruang)
            row.grid_columnconfigure(2, minsize=140, weight=0)  # Kolom CATEGORY (Dikunci lebar 140px)
            row.grid_columnconfigure(3, minsize=120, weight=0)  # Kolom PRICE (Dikunci lebar 120px)

            # Kolom 0: Code (Ditambahkan sticky="ew" & anchor="w")
            ctk.CTkLabel(row, text=item.get("code",""),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=PRIMARY, anchor="w").grid(row=0, column=0, padx=12, pady=4, sticky="ew")
            
            # Kolom 1: Name
            ctk.CTkLabel(row, text=item.get("name",""),
                         font=ctk.CTkFont(size=12), anchor="w").grid(row=0, column=1, padx=4, sticky="ew")
            
            # Kolom 2: Category (Ditambahkan sticky="ew" & anchor="w")
            ctk.CTkLabel(row, text=item.get("category",""),
                         font=ctk.CTkFont(size=11), text_color=TEXT_SEC, anchor="w").grid(row=0, column=2, padx=12, sticky="ew")
            
            # Kolom 3: Price (Ditambahkan sticky="ew" & anchor="e" agar nominal rata kanan lebih rapi)
            price_fmt = f"Rp {item.get('price',0):,.0f}".replace(",",".")
            ctk.CTkLabel(row, text=price_fmt,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=PRIMARY, anchor="e").grid(row=0, column=3, padx=12, sticky="ew")