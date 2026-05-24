# main.py — Entry point PT ABC Inventory System (CustomTkinter)
import os
import customtkinter as ctk
from inventory_manager import InventoryManager
from screens.login_screen import LoginScreen
from screens.index_screen import IndexScreen

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

VALID_EMAIL    = None
VALID_PASSWORD = None

def load_env():
    global VALID_EMAIL, VALID_PASSWORD
    for fname in [".env.txt", "_env.txt"]:
        if os.path.exists(fname):
            with open(fname) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip()
                        if k == "USER_EMAIL":
                            VALID_EMAIL = v
                        elif k == "USER_PASSWORD":
                            VALID_PASSWORD = v
            break


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PT ABC — Inventory System")
        self.geometry("1100x680")
        self.minsize(900, 600)
        self.resizable(True, True)

        # ── Inisialisasi backend ──────────────────────────────────
        self.inventory_manager = InventoryManager()

        # ── Container utama ──────────────────────────────────────
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self._frames = {}
        self._show_login()

    # ─── Screen management ───────────────────────────────────────
    def _show_login(self):
        if "login" not in self._frames:
            frame = LoginScreen(
                self.container,
                on_success=self._show_main,
                valid_email=VALID_EMAIL,
                valid_password=VALID_PASSWORD,
            )
            frame.grid(row=0, column=0, sticky="nsew")
            self._frames["login"] = frame
        self._frames["login"].tkraise()

    def _show_main(self):
        if "main" not in self._frames:
            frame = IndexScreen(
                self.container,
                inventory_manager=self.inventory_manager,
                on_logout=self._do_logout,
            )
            frame.grid(row=0, column=0, sticky="nsew")
            self._frames["main"] = frame
        self._frames["main"].tkraise()

    def _do_logout(self):
        self._show_login()


if __name__ == "__main__":
    load_env()
    app = App()
    app.mainloop()
