"""Sidebar navigation + content area. Menu items depend on the user's role."""
import tkinter as tk
from tkinter import ttk

from .. import theme
from ..session import Session
from ..widgets import confirm
from .analytics_view import AnalyticsView
from .hubs_view import HubsView
from .overview_view import OverviewView
from .players_view import PlayersView
from .profile_view import ProfileView
from .reviews_view import ReviewsView
from .transactions_view import TransactionsView
from .wallets_view import WalletsView

# (key, label, icon, view class, roles that can see it)
NAV = [
    ("overview", "Overview", "◈", OverviewView, {"admin", "player"}),
    ("wallets", "Wallets", "▣", WalletsView, {"admin", "player"}),
    ("transactions", "Transactions", "⇄", TransactionsView, {"admin", "player"}),
    ("hubs", "Hubs", "⌂", HubsView, {"admin", "player"}),
    ("players", "Players", "☰", PlayersView, {"admin"}),
    ("reviews", "Reviews", "★", ReviewsView, {"admin", "player"}),
    ("analytics", "Analytics", "▤", AnalyticsView, {"admin", "player"}),
    ("profile", "My profile", "◉", ProfileView, {"player"}),
]


class Shell(tk.Frame):
    def __init__(self, parent, session: Session, on_logout):
        super().__init__(parent, bg=theme.BG)
        self.session = session
        self._on_logout = on_logout
        self._views: dict[str, ttk.Frame] = {}
        self._buttons: dict[str, tk.Label] = {}
        self._active: str | None = None

        side = tk.Frame(self, bg=theme.SIDEBAR, width=230)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Label(side, text="◆ GameVerse", fg="white", bg=theme.SIDEBAR,
                 font=theme.font(15, "bold")).pack(anchor="w", padx=22, pady=(24, 2))
        tk.Label(side, text="ADMIN CONSOLE" if session.is_admin else "PLAYER PORTAL",
                 fg="#7d84a3", bg=theme.SIDEBAR, font=theme.font(8, "bold")).pack(
            anchor="w", padx=24, pady=(0, 22))

        for key, label, icon, _cls, roles in NAV:
            if session.role not in roles:
                continue
            btn = tk.Label(side, text=f"  {icon}   {label}", anchor="w", fg=theme.SIDEBAR_TEXT,
                           bg=theme.SIDEBAR, font=theme.font(10), padx=14, pady=9, cursor="hand2")
            btn.pack(fill="x", padx=10, pady=1)
            btn.bind("<Button-1>", lambda _e, k=key: self.show(k))
            btn.bind("<Enter>", lambda _e, k=key: self._hover(k, True))
            btn.bind("<Leave>", lambda _e, k=key: self._hover(k, False))
            self._buttons[key] = btn

        # user box at the bottom
        user = tk.Frame(side, bg=theme.SIDEBAR)
        user.pack(side="bottom", fill="x", padx=20, pady=20)
        tk.Frame(user, bg="#2a2f48", height=1).pack(fill="x", pady=(0, 14))
        tk.Label(user, text=session.display_name, fg="white", bg=theme.SIDEBAR,
                 font=theme.font(10, "bold")).pack(anchor="w")
        tk.Label(user, text="Administrator" if session.is_admin else f"Player #{session.playerid}",
                 fg="#7d84a3", bg=theme.SIDEBAR, font=theme.font(9)).pack(anchor="w")
        out = tk.Label(user, text="Sign out  →", fg=theme.SIDEBAR_TEXT, bg=theme.SIDEBAR,
                       font=theme.font(9, "bold"), cursor="hand2")
        out.pack(anchor="w", pady=(10, 0))
        out.bind("<Button-1>", lambda _e: self._logout())

        self.content = ttk.Frame(self, padding=(28, 24))
        self.content.pack(side="left", fill="both", expand=True)
        self.show("overview")

    # ------------------------------------------------------------------
    def show(self, key: str) -> None:
        if self._active == key:
            self._views[key].refresh()
            return
        if self._active:
            self._views[self._active].pack_forget()
        if key not in self._views:
            cls = next(c for k, _l, _i, c, _r in NAV if k == key)
            self._views[key] = cls(self.content, self.session)
            self._views[key].navigate = self.show       # let pages jump to each other
        self._active = key
        self._views[key].pack(fill="both", expand=True)
        self._views[key].refresh()
        for k, b in self._buttons.items():
            b.configure(bg=theme.SIDEBAR_ACTIVE if k == key else theme.SIDEBAR,
                        fg="white" if k == key else theme.SIDEBAR_TEXT)

    def _hover(self, key: str, entering: bool) -> None:
        if key == self._active:
            return
        self._buttons[key].configure(bg=theme.SIDEBAR_HOVER if entering else theme.SIDEBAR)

    def _logout(self) -> None:
        if confirm(self, "Sign out of GameVerse?"):
            self._on_logout()
