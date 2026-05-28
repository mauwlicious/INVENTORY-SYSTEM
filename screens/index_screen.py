# screens/index_screen.py
import customtkinter as ctk

PRIMARY         = "#1E61B8"
SIDEBAR_BG      = "#D9E8F7"
SIDEBAR_BG_DARK = "#1C2B40"
NAV_ACTIVE      = "#B3D4EF"
NAV_ACTIVE_DARK = "#2A4A6A"
TEXT_PRI        = "#1A2A3A"
TEXT_SEC        = "#7A8A9A"
TEXT_SEC_DARK   = "#8A9AAA"
WHITE           = "#FFFFFF"


class DialogTambahUser(ctk.CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Tambah User Baru")
        self.geometry("400x290")
        
        # Mengatur agar jendela ini selalu berada di atas layar utama
        self.transient(master)
        # Menahan klik di layar utama sampai dialog ini ditutup
        self.grab_set()

        # Menambahkan teks judul di bagian atas dialog
        judul = ctk.CTkLabel(self, text="Form Tambah User", font=ctk.CTkFont(size=20, weight="bold"))
        judul.pack(pady=(20, 10))

        # Kolom isian untuk nama pengguna
        self.input_username = ctk.CTkEntry(self, placeholder_text="Masukkan Username", width=300)
        self.input_username.pack(pady=10)

        # Kolom isian untuk kata sandi
        self.input_password = ctk.CTkEntry(self, placeholder_text="Masukkan Password", show="*", width=300)
        self.input_password.pack(pady=10)

        # Tombol untuk menyimpan data
        tombol_simpan = ctk.CTkButton(self, text="Simpan", command=self.simpan_data)
        tombol_simpan.pack(pady=(20, 5))

        # Tombol untuk membatalkan dan menutup dialog
        tombol_batal = ctk.CTkButton(self, text="Batal", fg_color="transparent", border_width=1, text_color=TEXT_PRI, command=self.destroy)
        tombol_batal.pack(pady=5)

    def simpan_data(self):
        # Mengambil teks yang diketikkan di dalam form
        username = self.input_username.get()
        password = self.input_password.get()
        
        # Mencegah penyimpanan jika ada kolom yang masih kosong
        if username == "" or password == "":
            print("Gagal: Username dan password harus diisi terlebih dahulu!")
            return
            
        # Menyimpan data langsung ke dalam file .env.txt
        try:
            with open(".env.txt", mode="a", encoding="utf-8") as file:
                # Menambahkan baris baru dengan format yang sesuai
                file.write(f"\nUSER_EMAIL={username}")
                file.write(f"\nUSER_PASSWORD={password}")
                
            print(f"Berhasil: User '{username}' sudah ditambahkan ke .env.txt!")
            
            # Menutup jendela secara otomatis setelah berhasil disimpan
            self.destroy()
            
        except Exception as e:
            print(f"Terjadi masalah saat menyimpan data: {e}")

class SidebarBtn(ctk.CTkFrame):
    def __init__(self, master, text, icon, command, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=10,
                         cursor="hand2", **kwargs)
        self._command = command
        self._active  = False
        self._icon_lbl = ctk.CTkLabel(self, text=icon, font=ctk.CTkFont(size=18), width=28)
        self._icon_lbl.pack(side="left", padx=(14,6))
        self._text_lbl = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=13), anchor="w")
        self._text_lbl.pack(side="left", fill="x", expand=True, pady=10)
        self.set_active(False)
        for w in (self, self._icon_lbl, self._text_lbl):
            w.bind("<Button-1>", lambda e: self._command())

    def set_active(self, active: bool):
        self._active = active
        dark = ctk.get_appearance_mode() == "Dark"
        if active:
            self.configure(fg_color=NAV_ACTIVE_DARK if dark else NAV_ACTIVE)
            self._icon_lbl.configure(text_color=PRIMARY)
            self._text_lbl.configure(text_color=PRIMARY,
                                     font=ctk.CTkFont(size=13, weight="bold"))
        else:
            self.configure(fg_color="transparent")
            col = TEXT_SEC_DARK if dark else TEXT_SEC
            self._icon_lbl.configure(text_color=col)
            self._text_lbl.configure(text_color=col, font=ctk.CTkFont(size=13))


class IndexScreen(ctk.CTkFrame):
    def __init__(self, master, inventory_manager, on_logout,
                 sales_manager=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.inventory_manager = inventory_manager
        self.sales_manager     = sales_manager
        self._on_logout        = on_logout
        self._nav_btns         = {}
        self._active_page      = None
        self._pages            = {}
        self._dark_mode        = False

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content_area()
        self.navigate("dashboard")

    def _build_sidebar(self):
        self._sidebar = ctk.CTkFrame(self, fg_color=SIDEBAR_BG, width=220, corner_radius=0)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)
        # Baris kosong digeser ke angka 6 karena kita menambahkan tombol baru
        self._sidebar.grid_rowconfigure(6, weight=1)
        self._sidebar.grid_columnconfigure(0, weight=1)

        logo = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        logo.grid(row=0, column=0, sticky="ew", padx=16, pady=(24,8))
        ctk.CTkLabel(logo, text="📦", font=ctk.CTkFont(size=26)).pack(side="left")
        ctk.CTkLabel(logo, text=" Inventory",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TEXT_PRI).pack(side="left")

        ctk.CTkFrame(self._sidebar, height=1, fg_color="#C5D8EA").grid(
            row=1, column=0, sticky="ew", padx=12, pady=4)

        nav_items = [
            ("dashboard", "🏠", "Dashboard"),
            ("items",     "📦", "Items"),
            ("sales",     "💳", "Sales"),
            ("priority",  "🔢", "Priority Queue"),
            ("search",    "🔍", "Search"),
        ]
        nf = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        nf.grid(row=2, column=0, sticky="ew", padx=8, pady=4)
        nf.grid_columnconfigure(0, weight=1)
        for key, icon, label in nav_items:
            btn = SidebarBtn(nf, text=label, icon=icon,
                             command=lambda k=key: self.navigate(k))
            btn.grid(sticky="ew", pady=2)
            self._nav_btns[key] = btn

        ctk.CTkFrame(self._sidebar, height=1, fg_color="#C5D8EA").grid(
            row=3, column=0, sticky="ew", padx=12, pady=4)
        
        SidebarBtn(self._sidebar, text="Logout", icon="🚪",
                   command=self._on_logout).grid(
            row=4, column=0, sticky="ew", padx=8, pady=2)
        
        # Tombol Tambah User yang memanggil fungsi memunculkan dialog
        SidebarBtn(self._sidebar, text="Tambah User", icon="👤",
                   command=self._on_tambah_user).grid(
            row=5, column=0, sticky="ew", padx=8, pady=2)

        ctk.CTkFrame(self._sidebar, fg_color="transparent").grid(
            row=6, column=0, sticky="nsew")

        # Theme toggle digeser ke baris 7
        tgl = ctk.CTkFrame(self._sidebar, fg_color="#C5D8EA", corner_radius=10)
        tgl.grid(row=7, column=0, sticky="ew", padx=12, pady=(0,16))
        tgl.grid_columnconfigure((0,1), weight=1)
        self._light_btn = ctk.CTkButton(
            tgl, text="☀ Light", height=34,
            fg_color=PRIMARY, text_color=WHITE, hover_color="#1650A0",
            corner_radius=8, font=ctk.CTkFont(size=12),
            command=lambda: self._set_theme("Light"))
        self._light_btn.grid(row=0, column=0, padx=(4,2), pady=4, sticky="ew")
        self._dark_btn = ctk.CTkButton(
            tgl, text="🌙 Dark", height=34,
            fg_color="transparent", text_color=TEXT_SEC,
            hover_color="#B3D4EF", corner_radius=8, font=ctk.CTkFont(size=12),
            command=lambda: self._set_theme("Dark"))
        self._dark_btn.grid(row=0, column=1, padx=(2,4), pady=4, sticky="ew")

    def _build_content_area(self):
        self._content_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self._content_frame.grid(row=0, column=1, sticky="nsew")
        self._content_frame.grid_rowconfigure(0, weight=1)
        self._content_frame.grid_columnconfigure(0, weight=1)

    def _get_page(self, key):
        if key not in self._pages:
            if key == "dashboard":
                from screens.dashboard_screen import DashboardScreen
                page = DashboardScreen(self._content_frame, self.inventory_manager)
            elif key == "items":
                from screens.items_screen import ItemsScreen
                page = ItemsScreen(self._content_frame, self.inventory_manager)
            elif key == "sales":
                from screens.sales_screen import SalesScreen
                page = SalesScreen(self._content_frame,
                                   self.inventory_manager, self.sales_manager)
            elif key == "priority":
                from screens.priority_screen import PriorityScreen
                page = PriorityScreen(self._content_frame, self.inventory_manager)
            elif key == "search":
                from screens.search_screen import SearchScreen
                page = SearchScreen(self._content_frame, self.inventory_manager)
            else:
                return None
            page.grid(row=0, column=0, sticky="nsew")
            self._pages[key] = page
        return self._pages[key]

    def navigate(self, target):
        page = self._get_page(target)
        if page is None: return
        page.tkraise()
        for key, btn in self._nav_btns.items():
            btn.set_active(key == target)
        self._active_page = target
        if hasattr(page, "on_show"):
            page.on_show()

    def _set_theme(self, mode: str):
        self._dark_mode = (mode == "Dark")
        ctk.set_appearance_mode(mode.lower())
        dark = self._dark_mode
        self._sidebar.configure(fg_color=SIDEBAR_BG_DARK if dark else SIDEBAR_BG)
        if dark:
            self._dark_btn.configure(fg_color=PRIMARY, text_color=WHITE)
            self._light_btn.configure(fg_color="transparent", text_color=TEXT_SEC_DARK)
        else:
            self._light_btn.configure(fg_color=PRIMARY, text_color=WHITE)
            self._dark_btn.configure(fg_color="transparent", text_color=TEXT_SEC)
        for btn in self._nav_btns.values():
            btn.set_active(btn._active)
        for page in self._pages.values():
            page.destroy()
        self._pages.clear()
        if self._active_page:
            self.navigate(self._active_page)

    def _on_tambah_user(self):
        # Membuka form dialog yang sudah kita buat di atas
        dialog = DialogTambahUser(self)
        # Memastikan jendela dialog langsung aktif dan siap diketik
        dialog.focus()