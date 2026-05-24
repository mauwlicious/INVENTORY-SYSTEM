# screens/login_screen.py
import customtkinter as ctk

PRIMARY   = "#1E61B8"
PRIMARY_D = "#1650A0"
BG_PANEL  = "#D9E8F7"
WHITE     = "#FFFFFF"
TEXT_SEC  = "#7A8A9A"
RED_ERR   = "#D92626"


class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, on_success, valid_email=None, valid_password=None, **kwargs):
        super().__init__(master, fg_color=WHITE, **kwargs)
        self._on_success    = on_success

        # TIDAK ada fallback hardcoded — wajib dari .env.txt via main.py
        # Jika .env.txt tidak ada atau kosong, login tidak akan pernah berhasil
        # sehingga kredensial tidak bisa ditebak dari source code.
        self._valid_email    = valid_email
        self._valid_password = valid_password

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=55)
        self.grid_columnconfigure(1, weight=45)

        self._build_branding()
        self._build_form()

    # ── Panel kiri (branding) ─────────────────────────────────────────────────
    def _build_branding(self):
        left = ctk.CTkFrame(self, fg_color=PRIMARY, corner_radius=16)
        left.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.grid_rowconfigure((0,1,2,3,4), weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="📦", font=ctk.CTkFont(size=64),
                     text_color="white").grid(row=0, column=0, pady=(32, 4))

        ctk.CTkLabel(left, text="PT ABC Inventory",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="white").grid(row=1, column=0)

        ctk.CTkLabel(left,
            text="Sistem manajemen inventaris\nberbasis struktur data efisien",
            font=ctk.CTkFont(size=14), text_color="#C0D8F5",
            justify="center").grid(row=2, column=0, pady=(4, 16))

        badge_row = ctk.CTkFrame(left, fg_color="transparent")
        badge_row.grid(row=3, column=0, pady=(0, 24))

        for icon, label in [("⚡", "O(1) Search"), ("↕", "MergeSort"), ("🏆", "Heap PQ")]:
            b = ctk.CTkFrame(badge_row, fg_color="#3A72B8", corner_radius=10)
            b.pack(side="left", padx=6, ipadx=10, ipady=6)
            ctk.CTkLabel(b, text=icon, font=ctk.CTkFont(size=20),
                         text_color="white").pack()
            ctk.CTkLabel(b, text=label, font=ctk.CTkFont(size=11),
                         text_color="#CCDFF5").pack()

    # ── Panel kanan (form) ────────────────────────────────────────────────────
    def _build_form(self):
        right = ctk.CTkFrame(self, fg_color=WHITE)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(right, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(inner, text="📦  Inventory",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=PRIMARY).grid(row=0, column=0, sticky="w", pady=(0, 4))

        ctk.CTkLabel(inner, text="Welcome back 👋",
                     font=ctk.CTkFont(size=24, weight="bold")).grid(row=1, column=0, sticky="w")
        ctk.CTkLabel(inner, text="Please login to continue",
                     font=ctk.CTkFont(size=13), text_color=TEXT_SEC).grid(
            row=2, column=0, sticky="w", pady=(0, 16))

        ctk.CTkLabel(inner, text="Email Address", font=ctk.CTkFont(size=12),
                     text_color=TEXT_SEC).grid(row=3, column=0, sticky="w")
        self._email_entry = ctk.CTkEntry(inner, width=320, height=42,
                                          placeholder_text="Enter email...",
                                          corner_radius=8)
        self._email_entry.grid(row=4, column=0, pady=(2, 10))

        ctk.CTkLabel(inner, text="Password", font=ctk.CTkFont(size=12),
                     text_color=TEXT_SEC).grid(row=5, column=0, sticky="w")
        self._pw_entry = ctk.CTkEntry(inner, width=320, height=42,
                                       placeholder_text="••••••••",
                                       show="•", corner_radius=8)
        self._pw_entry.grid(row=6, column=0, pady=(2, 6))

        self._remember = ctk.CTkCheckBox(inner, text="Remember Me",
                                          font=ctk.CTkFont(size=13),
                                          checkbox_height=20, checkbox_width=20)
        self._remember.select()
        self._remember.grid(row=7, column=0, sticky="w", pady=(0, 10))

        self._error_lbl = ctk.CTkLabel(inner, text="", font=ctk.CTkFont(size=12),
                                        text_color=RED_ERR, height=18)
        self._error_lbl.grid(row=8, column=0, sticky="w")

        self._login_btn = ctk.CTkButton(
            inner, text="Login", width=320, height=46,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=PRIMARY, hover_color=PRIMARY_D,
            corner_radius=10,
            command=self._login_action)
        self._login_btn.grid(row=9, column=0, pady=(8, 8))

        self._pw_entry.bind("<Return>", lambda e: self._login_action())
        self._email_entry.bind("<Return>", lambda e: self._pw_entry.focus())

        # Tampilkan hint hanya jika env tersedia (tidak expose password jika None)
        hint = "Credentials loaded from .env.txt" if self._valid_email else "⚠ .env.txt not found!"
        hint_color = TEXT_SEC if self._valid_email else RED_ERR
        ctk.CTkLabel(inner, text=hint,
                     font=ctk.CTkFont(size=11),
                     text_color=hint_color).grid(row=10, column=0)

    # ── Logic ─────────────────────────────────────────────────────────────────
    def _login_action(self):
        email = self._email_entry.get().strip()
        pw    = self._pw_entry.get().strip()
        self._error_lbl.configure(text="")

        # Jika .env.txt tidak terbaca, tampilkan pesan yang jelas
        if not self._valid_email or not self._valid_password:
            self._error_lbl.configure(text="❌ Credentials not loaded. Check .env.txt")
            return

        if email == self._valid_email and pw == self._valid_password:
            self._on_success()
        else:
            self._error_lbl.configure(text="❌ Invalid email or password.")