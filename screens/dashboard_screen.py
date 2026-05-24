# screens/dashboard_screen.py
import customtkinter as ctk
from datetime import datetime, date

PRIMARY  = "#1E61B8"
TEXT_SEC = "#7A8A9A"
TEXT_PRI = "#1A2A3A"


def _card_bg():
    """Kembalikan warna kartu sesuai mode aktif."""
    return "#2A3448" if ctk.get_appearance_mode() == "Dark" else "#FFFFFF"

def _page_bg():
    return "#1A2233" if ctk.get_appearance_mode() == "Dark" else "#F7F9FC"

def _kpi_palettes(dark):
    if dark:
        return [
            ("#1E3560", PRIMARY),
            ("#1A3828", "#2AC76A"),
            ("#2D1F50", "#9B7AEE"),
            ("#3D2800", "#FFAA33"),
        ]
    return [
        ("#EBF2FF", PRIMARY),
        ("#EAF7EC", "#1A9A4A"),
        ("#F4EEFF", "#6B3FC0"),
        ("#FFF5E6", "#D97800"),
    ]


class KpiCard(ctk.CTkFrame):
    def __init__(self, master, icon, value, label, bg, icon_color, **kwargs):
        super().__init__(master, fg_color=bg, corner_radius=12, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text=icon, font=ctk.CTkFont(size=28),
                     text_color=icon_color).grid(row=0, column=0, rowspan=2, padx=(14,8), pady=10)
        ctk.CTkLabel(self, text=value, font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=icon_color, anchor="w").grid(row=0, column=1, sticky="sw", padx=(0,14))
        ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=11),
                     text_color=TEXT_SEC, anchor="w").grid(row=1, column=1, sticky="nw", padx=(0,14))


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, master, inventory_manager, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=0, **kwargs)
        self.inventory_manager = inventory_manager
        self._build_layout()
        self.on_show()

    def _build_layout(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Top bar
        top = ctk.CTkFrame(self, fg_color="transparent", height=60)
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(16, 0))
        top.grid_propagate(False)
        top.grid_columnconfigure(1, weight=1)

        self._greeting_lbl = ctk.CTkLabel(top, text="",
                                           font=ctk.CTkFont(size=22, weight="bold"))
        self._greeting_lbl.grid(row=0, column=0, sticky="w")
        self._date_lbl = ctk.CTkLabel(top, text="",
                                       font=ctk.CTkFont(size=13), text_color=TEXT_SEC)
        self._date_lbl.grid(row=1, column=0, sticky="w")
        ctk.CTkLabel(top, text="👤", font=ctk.CTkFont(size=34)).grid(
            row=0, column=2, rowspan=2, padx=(0, 4))

        # Scrollable area
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=(12,12))
        self._scroll.grid_columnconfigure(0, weight=1)

        # KPI
        self._kpi_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._kpi_frame.grid(row=0, column=0, sticky="ew", pady=(0,14))
        for i in range(4):
            self._kpi_frame.grid_columnconfigure(i, weight=1)

        # Divider
        ctk.CTkFrame(self._scroll, height=1, fg_color="#DDE5EE").grid(
            row=1, column=0, sticky="ew", pady=(0,14))

        # Mid row
        mid = ctk.CTkFrame(self._scroll, fg_color="transparent")
        mid.grid(row=2, column=0, sticky="ew", pady=(0,14))
        mid.grid_columnconfigure(0, weight=1)
        mid.grid_columnconfigure(1, weight=1)

        self._top5_card   = ctk.CTkFrame(mid, corner_radius=12)
        self._top5_card.grid(row=0, column=0, sticky="nsew", padx=(0,7))
        self._expiry_card = ctk.CTkFrame(mid, corner_radius=12)
        self._expiry_card.grid(row=0, column=1, sticky="nsew", padx=(7,0))

        # Category
        self._cat_card = ctk.CTkFrame(self._scroll, corner_radius=12)
        self._cat_card.grid(row=3, column=0, sticky="ew")

    def on_show(self):
        now   = datetime.now()
        hour  = now.hour
        greet = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 17 else "Good Evening")
        self._greeting_lbl.configure(text=f"{greet}, Admin 👋")
        self._date_lbl.configure(text=now.strftime("%A, %d %B %Y"))
        self._build_kpi()
        self._build_top5()
        self._build_expiring()
        self._build_categories()

    def _clear(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    def _build_kpi(self):
        self._clear(self._kpi_frame)
        stats  = self.inventory_manager.get_stats()
        dark   = ctk.get_appearance_mode() == "Dark"
        pals   = _kpi_palettes(dark)
        total_val_fmt = f"Rp {stats['total_value']:,.0f}".replace(",", ".")

        kpis = [
            ("📦", str(stats["total_items"]),                    "Total Items"),
            ("🗂",  f"{stats['total_qty']:,}".replace(",","."),  "Total Stock"),
            ("💰", total_val_fmt,                                 "Inventory Value"),
            ("⚠",  str(stats["near_expiry"]),                    "Near Expiry"),
        ]
        for i, (icon, val, label) in enumerate(kpis):
            bg, col = pals[i]
            card = KpiCard(self._kpi_frame, icon, val, label, bg, col)
            card.grid(row=0, column=i, sticky="ew",
                      padx=(0 if i == 0 else 6, 0), ipady=4)

    def _build_top5(self):
        card = self._top5_card
        self._clear(card)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Top 5 Most Expensive",
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14,6))

        stats = self.inventory_manager.get_stats()
        for i, item in enumerate(stats.get("top5_expensive", [])):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.grid(row=i+1, column=0, sticky="ew", padx=16, pady=2)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=f"#{i+1}",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=PRIMARY, width=28).grid(row=0, column=0)
            ctk.CTkLabel(row, text=item.get("name", ""),
                         font=ctk.CTkFont(size=12), anchor="w").grid(
                row=0, column=1, sticky="ew", padx=6)
            ctk.CTkLabel(row, text=f"Rp {item.get('price',0):,.0f}".replace(",","."),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=PRIMARY).grid(row=0, column=2)
        ctk.CTkFrame(card, height=12, fg_color="transparent").grid(row=99, column=0)

    def _build_expiring(self):
        card = self._expiry_card
        self._clear(card)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="⚠ Expiring Items",
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14,6))

        items = self.inventory_manager.pq_expiry.to_sorted_list()[:5]
        today = date.today()

        for i, item in enumerate(items):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.grid(row=i+1, column=0, sticky="ew", padx=16, pady=2)
            row.grid_columnconfigure(0, weight=1)
            exp_str = item.get("expiry_date", "")
            try:
                exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
                delta    = (exp_date - today).days
                if delta < 0:
                    col, badge = "#D92626", "Expired"
                elif delta <= 90:
                    col, badge = "#D97800", f"{delta}d"
                else:
                    col, badge = "#A06000", f"{delta}d"
            except Exception:
                col, badge = TEXT_SEC, "?"

            ctk.CTkLabel(row, text=item.get("name",""),
                         font=ctk.CTkFont(size=12), anchor="w").grid(
                row=0, column=0, sticky="ew")
            ctk.CTkLabel(row, text=exp_str,
                         font=ctk.CTkFont(size=11), text_color=col).grid(
                row=0, column=1, padx=4)
            ctk.CTkLabel(row, text=badge,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=col, width=52).grid(row=0, column=2)
        ctk.CTkFrame(card, height=12, fg_color="transparent").grid(row=99, column=0)

    def _build_categories(self):
        card = self._cat_card
        self._clear(card)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Items by Category",
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14,10))

        stats = self.inventory_manager.get_stats()
        cats  = sorted(stats.get("categories", {}).items(), key=lambda x: -x[1])
        dark  = ctk.get_appearance_mode() == "Dark"

        if dark:
            colors     = ["#1E3560","#1A3828","#2D1F50","#3D2800","#0F3030","#3A1A14"]
            icon_colors= [PRIMARY, "#2AC76A", "#9B7AEE", "#FFAA33", "#33BBBB", "#FF6655"]
        else:
            colors     = ["#EBF2FF","#EAF7EC","#F4EEFF","#FFF5E6","#E8F7F7","#FBF0EE"]
            icon_colors= [PRIMARY, "#1A9A4A", "#6B3FC0", "#D97800", "#0A7878", "#B03020"]

        scroll_row = ctk.CTkFrame(card, fg_color="transparent")
        scroll_row.grid(row=1, column=0, sticky="ew", padx=16, pady=(0,14))

        for i, (cat, count) in enumerate(cats[:8]):
            bg  = colors[i % len(colors)]
            col = icon_colors[i % len(icon_colors)]
            c   = ctk.CTkFrame(scroll_row, fg_color=bg, corner_radius=10, width=110, height=80)
            c.pack(side="left", padx=6)
            c.pack_propagate(False)
            ctk.CTkLabel(c, text=str(count),
                         font=ctk.CTkFont(size=22, weight="bold"),
                         text_color=col).pack(pady=(12,0))
            ctk.CTkLabel(c, text=cat, font=ctk.CTkFont(size=10),
                         text_color=TEXT_SEC, wraplength=95).pack()