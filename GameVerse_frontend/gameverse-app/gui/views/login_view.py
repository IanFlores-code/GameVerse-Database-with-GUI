"""Login screen (Module 1): player login by email, admin login by username."""
import tkinter as tk
from tkinter import ttk

from .. import api, theme, validators
from ..session import Session
from ..widgets import Field, FormDialog, Segmented, info


class LoginView(tk.Frame):
    def __init__(self, parent, on_login):
        super().__init__(parent, bg=theme.BG)
        self._on_login = on_login
        self.role = tk.StringVar(value="player")
        self.ident = tk.StringVar()
        self.password = tk.StringVar()

        card = tk.Frame(self, bg=theme.SURFACE, highlightbackground=theme.BORDER,
                        highlightcolor=theme.BORDER, highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # ---- brand panel ------------------------------------------------
        brand = tk.Frame(card, bg=theme.SIDEBAR, width=340, height=440)
        brand.grid(row=0, column=0, sticky="nsew")
        brand.grid_propagate(False)
        tk.Label(brand, text="◆", fg=theme.ACCENT, bg=theme.SIDEBAR,
                 font=theme.font(28, "bold")).place(x=36, y=48)
        tk.Label(brand, text="GameVerse", fg="white", bg=theme.SIDEBAR,
                 font=theme.font(24, "bold")).place(x=36, y=100)
        tk.Label(brand, text="Wallet Manager", fg=theme.SIDEBAR_TEXT, bg=theme.SIDEBAR,
                 font=theme.font(13)).place(x=38, y=142)
        tk.Label(brand, text="Hubs, wallets, transactions and reviews\nfor the GameVerse "
                             "platform, in one place.", fg="#8a90ab", bg=theme.SIDEBAR,
                 justify="left", font=theme.font(10)).place(x=38, y=340)

        # ---- form panel -------------------------------------------------
        form = ttk.Frame(card, style="Card.TFrame", padding=(40, 36))
        form.grid(row=0, column=1, sticky="nsew")
        ttk.Label(form, text="Sign in", style="CardTitle.TLabel",
                  font=theme.font(18, "bold")).pack(anchor="w")
        ttk.Label(form, text="Choose how you are signing in.", style="CardMuted.TLabel").pack(
            anchor="w", pady=(2, 16))

        Segmented(form, self.role, [("player", "Player"), ("admin", "Admin")],
                  command=self._role_changed).pack(fill="x")

        self.ident_label = ttk.Label(form, text="Email", style="Card.TLabel")
        self.ident_label.pack(anchor="w", pady=(18, 2))
        self.ident_entry = ttk.Entry(form, textvariable=self.ident, width=34)
        self.ident_entry.pack(fill="x")
        ttk.Label(form, text="Password", style="Card.TLabel").pack(anchor="w", pady=(12, 2))
        ttk.Entry(form, textvariable=self.password, show="•", width=34).pack(fill="x")

        self.error = ttk.Label(form, text="", style="Error.TLabel", wraplength=300)
        self.error.pack(anchor="w", pady=(10, 0))
        ttk.Button(form, text="Sign in", style="Primary.TButton", command=self._login).pack(
            fill="x", pady=(8, 0))

        self.register_row = ttk.Frame(form, style="Card.TFrame")
        self.register_row.pack(anchor="w", pady=(18, 0))
        ttk.Label(self.register_row, text="New player?", style="CardMuted.TLabel").pack(side="left")
        ttk.Button(self.register_row, text="Create an account", style="Link.TButton",
                   command=self._open_register).pack(side="left", padx=(6, 0))

        self.bind_all("<Return>", self._enter, add="+")
        self.ident_entry.focus_set()

    def destroy(self):
        self.unbind_all("<Return>")
        super().destroy()

    # ------------------------------------------------------------------
    def _enter(self, event):
        if event.widget.winfo_toplevel() is self.winfo_toplevel():
            self._login()

    def _role_changed(self):
        is_admin = self.role.get() == "admin"
        self.ident_label.configure(text="Username" if is_admin else "Email")
        self.error.configure(text="")
        if is_admin:
            self.register_row.pack_forget()
        else:
            self.register_row.pack(anchor="w", pady=(18, 0))

    def _login(self):
        ident, pw = self.ident.get().strip(), self.password.get()
        if not ident or not pw:
            self.error.configure(text="Enter your " + (
                "username" if self.role.get() == "admin" else "email") + " and password.")
            return
        try:
            if self.role.get() == "admin":
                data = api.login_admin(ident, pw)
            else:
                data = api.login_player(ident, pw)
        except api.AppError as exc:
            self.error.configure(text=str(exc))
            return
        self._on_login(Session.from_login(data))

    def _open_register(self):
        fields = [
            Field("firstname", "First name", parse=validators.text(100)),
            Field("lastname", "Last name", parse=validators.text(100)),
            Field("email", "Email", parse=validators.email),
            Field("phone", "Phone", parse=validators.phone, required=False),
            Field("dateofbirth", "Date of birth", parse=validators.iso_date,
                  hint="YYYY-MM-DD · players must be at least 13"),
            Field("password", "Password", kind="password", parse=validators.password,
                  hint="At least 6 characters"),
            Field("confirm", "Confirm password", kind="password"),
        ]

        def submit(v):
            if v["password"] != v["confirm"]:
                raise ValueError("Passwords do not match.")
            self.ident.set(v["email"])
            return api.register_player(v["firstname"], v["lastname"], v["email"], v["phone"],
                                       v["dateofbirth"], v["password"])

        dlg = FormDialog(self, "Create a player account", fields, submit,
                         submit_text="Create account")
        self.wait_window(dlg)
        if dlg.result:
            self.role.set("player")
            self._role_changed()
            info(self, f"Welcome to GameVerse! Your player ID is {dlg.result}.\n"
                       "You can sign in with your email now.")
