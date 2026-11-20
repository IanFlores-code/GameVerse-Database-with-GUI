"""Module 6: Reviews. Players write/view their own; admins verify and report."""
import tkinter as tk
from tkinter import ttk

from .. import api
from ..widgets import (Col, DataTable, Field, FormDialog, TableDialog, Toolbar, fmt_bool,
                       fmt_rating, info, run_action, safe_call)
from .base import BaseView, wallet_label

ALL = "All wallets"


class ReviewsView(BaseView):
    title = "Reviews"

    def subtitle_for(self, session):
        return ("Verify reviews and compare ratings across wallet types." if session.is_admin
                else "Rate the wallets you hold. One review per wallet.")

    def __init__(self, parent, session):
        super().__init__(parent, session)
        admin = session.is_admin
        self.wallets: list[dict] = []

        tools = Toolbar(self)
        tools.pack(fill="x", pady=(0, 10))
        if admin:
            ttk.Label(tools, text="Wallet").pack(side="left", padx=(0, 6))
            self.filter = tk.StringVar(value=ALL)
            self.cb_filter = ttk.Combobox(tools, textvariable=self.filter, state="readonly",
                                          width=34)
            self.cb_filter.pack(side="left", padx=(0, 12))
            self.cb_filter.bind("<<ComboboxSelected>>", lambda _e: self._load())
            self.btn_verify = tools.add("Verify", self._toggle_verify, style="Primary.TButton")
            tools.add("Average rating by wallet type", self._avg_by_type, side="right")
        else:
            tools.add("✎ Write a review", self._write, style="Primary.TButton")

        cols = [Col("reviewid", "ID", 55), Col("walletid", "Wallet", 65),
                Col("wallettype", "Type", 80)]
        if admin:
            cols.append(Col("player", "Player", 130))
        cols += [Col("rating", "Rating", 90, fmt=fmt_rating), Col("reviewtext", "Review", 380),
                 Col("reviewdate", "Date", 95), Col("isverified", "Verified", 70, fmt=fmt_bool)]
        self.table = DataTable(self, cols, height=17, on_select=self._on_select,
                               empty_text="No reviews yet." if admin else
                               "You have not written any reviews yet.")
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        if self.session.is_admin:
            self.wallets = self.my_wallets()
            self.cb_filter.configure(values=[ALL] + [wallet_label(w) for w in self.wallets])
        self._load()

    def _load(self):
        if self.session.is_admin:
            idx = self.cb_filter.current()
            walletid = self.wallets[idx - 1]["walletid"] if idx > 0 else None
            self.table.set_rows(safe_call(self, api.list_reviews, walletid))
        else:
            self.table.set_rows(safe_call(self, api.player_reviews, self.session.playerid))

    def _on_select(self, row):
        if self.session.is_admin:
            self.btn_verify.state(["!disabled"] if row else ["disabled"])
            if row:
                self.btn_verify.configure(text="Unverify" if row["isverified"] else "Verify")

    # ------------------------------------------------------------------
    def _write(self):
        wallets = self.my_wallets()
        if not wallets:
            return info(self, "You need to hold a wallet before you can review it.")
        fields = [
            Field("walletid", "Wallet", kind="combo",
                  options=[(w["walletid"], wallet_label(w)) for w in wallets]),
            Field("rating", "Rating (1 = poor, 5 = excellent)", kind="spin", options=(1, 5),
                  default=5, parse=_rating),
            Field("reviewtext", "Your review", kind="text"),
        ]

        def submit(v):
            return api.add_review(self.session.playerid, v["walletid"], v["rating"],
                                  v["reviewtext"])

        dlg = FormDialog(self, "Write a review", fields, submit, submit_text="Post review")
        self.wait_window(dlg)
        if dlg.result:
            self._load()
            info(self, "Thanks! Your review was posted and is waiting for verification.")

    def _toggle_verify(self):
        row = self.table.selected()
        if row and run_action(self, api.set_review_verified, row["reviewid"],
                              not row["isverified"]):
            self._load()

    def _avg_by_type(self):
        rows = safe_call(self, api.avg_rating_by_wallet_type)
        if rows is not None:
            TableDialog(self, "Average rating by wallet type", [
                Col("wallettype", "Wallet type", 140),
                Col("review_count", "Reviews", 90, anchor="e"),
                Col("avg_rating", "Average rating", 130, anchor="e"),
            ], rows, width=480, height=4)


def _rating(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError:
        raise ValueError("choose a whole number from 1 to 5") from None
    if not 1 <= value <= 5:
        raise ValueError("must be between 1 and 5")
    return value
