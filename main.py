# main.py — Entry point PT ABC Inventory System
import os, json
import customtkinter as ctk
from inventory_manager import InventoryManager
from sales_manager      import SalesManager
from screens.login_screen import LoginScreen
from screens.index_screen  import IndexScreen

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

USERS_DB      = {}   # {email: password}
REMEMBER_DATA = {"email": "", "password": "", "remember": False}


def load_env():
    """Baca semua user dari _env.txt (format USER_EMAIL / USER_PASSWORD berpasangan)."""
    global USERS_DB
    for fname in ["_env.txt", ".env.txt"]:
        if os.path.exists(fname):
            with open(fname, encoding="utf-8") as f:
                current_email = None
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"): continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip()
                        if k == "USER_EMAIL":
                            current_email = v
                            USERS_DB[v]   = ""
                        elif k == "USER_PASSWORD" and current_email:
                            USERS_DB[current_email] = v
            break
    if not USERS_DB:
        print("[WARN] Tidak ada user di _env.txt — gunakan fallback")
        USERS_DB["admin@mail.com"] = "rahasia123"


def load_remember_me():
    global REMEMBER_DATA
    try:
        if os.path.exists(".remember.json"):
            with open(".remember.json", "r", encoding="utf-8") as f:
                REMEMBER_DATA = json.load(f)
    except Exception as e:
        print(f"[WARN] Gagal baca remember: {e}")
        REMEMBER_DATA = {"email":"","password":"","remember":False}


def save_remember_me(email: str, password: str, remember: bool):
    global REMEMBER_DATA
    REMEMBER_DATA = {
        "email":    email    if remember else "",
        "password": password if remember else "",
        "remember": remember,
    }
    try:
        with open(".remember.json", "w", encoding="utf-8") as f:
            json.dump(REMEMBER_DATA, f)
    except Exception as e:
        print(f"[WARN] Gagal simpan remember: {e}")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PT ABC — Inventory System")
        self.geometry("1100x680")
        self.minsize(920, 600)
        self.resizable(True, True)

        self.inventory_manager = InventoryManager()
        self.sales_manager     = SalesManager()

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self._frames = {}
        self._show_login()

    def _show_login(self):
        if "login" not in self._frames:
            frame = LoginScreen(
                self.container,
                on_success=self._show_main,
                users_db=USERS_DB,
                remember_data=REMEMBER_DATA,
                on_remember_save=save_remember_me,
            )
            frame.grid(row=0, column=0, sticky="nsew")
            self._frames["login"] = frame
        self._frames["login"].tkraise()

    def _show_main(self):
        if "main" not in self._frames:
            frame = IndexScreen(
                self.container,
                inventory_manager=self.inventory_manager,
                sales_manager=self.sales_manager,
                on_logout=self._do_logout,
            )
            frame.grid(row=0, column=0, sticky="nsew")
            self._frames["main"] = frame
        self._frames["main"].tkraise()

    def _do_logout(self):
        if not REMEMBER_DATA.get("remember"):
            save_remember_me("", "", False)
        self._show_login()


if __name__ == "__main__":
    load_env()
    load_remember_me()
    app = App()
    app.mainloop()