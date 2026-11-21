"""Shared base class and helpers for the content pages."""
from tkinter import ttk

from .. import api
from ..session import Session
from ..widgets import PageHeader, fmt_money, safe_call


class BaseView(ttk.Frame):
    title = ""
    subtitle = ""

    def __init__(self, parent, session: Session):
        super().__init__(parent)
        self.session = session
        self.header = PageHeader(self, self.title, self.subtitle_for(session))
        self.header.pack(fill="x", pady=(0, 16))

    def subtitle_for(self, session: Session) -> str:
        return self.subtitle

    def refresh(self) -> None:
        """Reload data from the database. Called each time the page is shown."""

    # -- shared helpers ----------------------------------------------------
    def my_wallets(self) -> list[dict]:
        """Wallets visible to the current user (held wallets, or all for admins)."""
        if self.session.is_admin:
            return safe_call(self, api.list_all_wallets) or []
        return safe_call(self, api.list_player_wallets, self.session.playerid) or []


def wallet_label(w: dict) -> str:
    role = f" · {w['holderrole']}" if w.get("holderrole") else ""
    inactive = " · inactive" if w.get("isactive") is False else ""
    return f"#{w['walletid']}  {w['wallettype']}  ({fmt_money(w['balance'])}){role}{inactive}"
