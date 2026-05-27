# screens/login_screen.py — Multi-user + Remember Me
import customtkinter as ctk

PRIMARY   = "#1E61B8"
PRIMARY_D = "#1650A0"
WHITE     = "#FFFFFF"
TEXT_SEC  = "#7A8A9A"
RED_ERR   = "#D92626"


class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, on_success,
                 users_db: dict,
                 remember_data: dict,
                 on_remember_save,
                 **kwargs):
        super().__init__(master, fg_color=WHITE, **kwargs)
        self._on_success      = on_success
        self._users_db        = users_db          # {email: password}
        self._remember_data   = remember_data     # {email, password, remember}
        self._on_remember_save = on_remember_save  # fn(email, pw, remember)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=55)
        self.grid_columnconfigure(1, weight=45)
        self._build_branding()
        self._build_form()

    def _build_branding(self):
        left = ctk.CTkFrame(self, fg_color=PRIMARY, corner_radius=16)
        left.grid(row=0, column=0, sticky="nsew", padx=(16,8), pady=16)
        left.grid_rowconfigure((0,1,2,3), weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="📦", font=ctk.CTkFont(size=64),
                     text_color=WHITE).grid(row=0, column=0, pady=(32,4))
        ctk.CTkLabel(left, text="PT ABC Inventory",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=WHITE).grid(row=1, column=0)
        ctk.CTkLabel(left,
            text="Sistem manajemen inventaris\nberbasis struktur data efisien",
            font=ctk.CTkFont(size=14), text_color="#C0D8F5",
            justify="center").grid(row=2, column=0, pady=(4,16))

        badge_row = ctk.CTkFrame(left, fg_color="transparent")
        badge_row.grid(row=3, column=0, pady=(0,24))
        for icon, label in [("⚡","O(1) Search"),("↕","MergeSort"),("🏆","Heap PQ")]:
            b = ctk.CTkFrame(badge_row, fg_color="#3A72B8", corner_radius=10)
            b.pack(side="left", padx=6, ipadx=10, ipady=6)
            ctk.CTkLabel(b, text=icon, font=ctk.CTkFont(size=20),
                         text_color=WHITE).pack()
            ctk.CTkLabel(b, text=label, font=ctk.CTkFont(size=11),
                         text_color="#CCDFF5").pack()

    def _build_form(self):
        right = ctk.CTkFrame(self, fg_color=WHITE)
        right.grid(row=0, column=1, sticky="nsew", padx=(8,16), pady=16)
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(right, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(inner, text="📦  Inventory",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=PRIMARY).grid(row=0, column=0, sticky="w", pady=(0,4))
        ctk.CTkLabel(inner, text="Welcome back 👋",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=1, column=0, sticky="w")
        ctk.CTkLabel(inner, text="Silahkan login untuk melanjutkan",
                     font=ctk.CTkFont(size=13), text_color=TEXT_SEC).grid(
            row=2, column=0, sticky="w", pady=(0,16))

        ctk.CTkLabel(inner, text="Email Address", font=ctk.CTkFont(size=12),
                     text_color=TEXT_SEC).grid(row=3, column=0, sticky="w")
        self._email_entry = ctk.CTkEntry(inner, width=320, height=42,
                                          placeholder_text="Masukkan email...",
                                          corner_radius=8)
        self._email_entry.grid(row=4, column=0, pady=(2,10))

        ctk.CTkLabel(inner, text="Password", font=ctk.CTkFont(size=12),
                     text_color=TEXT_SEC).grid(row=5, column=0, sticky="w")
        self._pw_entry = ctk.CTkEntry(inner, width=320, height=42,
                                       placeholder_text="••••••••",
                                       show="•", corner_radius=8)
        self._pw_entry.grid(row=6, column=0, pady=(2,8))

        # Remember me row + info jumlah user
        rm_row = ctk.CTkFrame(inner, fg_color="transparent")
        rm_row.grid(row=7, column=0, sticky="ew")
        rm_row.grid_columnconfigure(0, weight=1)
        self._remember = ctk.CTkCheckBox(rm_row, text="Remember Me",
                                          font=ctk.CTkFont(size=13),
                                          checkbox_height=20, checkbox_width=20)
        self._remember.grid(row=0, column=0, sticky="w")
        n = len(self._users_db)
        ctk.CTkLabel(rm_row, text=f"👥 {n} user{'s' if n>1 else ''} terdaftar",
                     font=ctk.CTkFont(size=11), text_color=TEXT_SEC).grid(
            row=0, column=1, sticky="e")

        self._error_lbl = ctk.CTkLabel(inner, text="", font=ctk.CTkFont(size=12),
                                        text_color=RED_ERR, height=18)
        self._error_lbl.grid(row=8, column=0, sticky="w", pady=(8,0))

        self._login_btn = ctk.CTkButton(
            inner, text="Login", width=320, height=46,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=PRIMARY, hover_color=PRIMARY_D, corner_radius=10,
            command=self._login_action)
        self._login_btn.grid(row=9, column=0, pady=(8,6))

        hint = "Kredensial dimuat dari _env.txt" if self._users_db else "⚠ _env.txt tidak ditemukan!"
        ctk.CTkLabel(inner, text=hint, font=ctk.CTkFont(size=11),
                     text_color=TEXT_SEC if self._users_db else RED_ERR).grid(
            row=10, column=0)

        # Pre-fill jika remember aktif
        if self._remember_data.get("remember") and self._remember_data.get("email"):
            self._email_entry.insert(0, self._remember_data["email"])
            self._pw_entry.insert(0, self._remember_data.get("password",""))
            self._remember.select()

        self._pw_entry.bind("<Return>", lambda e: self._login_action())
        self._email_entry.bind("<Return>", lambda e: self._pw_entry.focus())

    def _login_action(self):
        email = self._email_entry.get().strip()
        pw    = self._pw_entry.get().strip()
        self._error_lbl.configure(text="")

        if not self._users_db:
            self._error_lbl.configure(text="❌ Tidak ada user di _env.txt"); return

        expected = self._users_db.get(email)
        if expected is None:
            self._error_lbl.configure(text="❌ Email tidak terdaftar."); return
        if pw != expected:
            self._error_lbl.configure(text="❌ Password salah."); return

        remember = bool(self._remember.get())
        self._on_remember_save(email, pw, remember)
        self._on_success()