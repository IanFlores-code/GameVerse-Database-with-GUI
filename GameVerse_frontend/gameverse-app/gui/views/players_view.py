"""Module 4 (admin view): list players and drill into their wallets, history and reviews."""
import tkinter as tk
from tkinter import ttk

from .. import api
from ..widgets import (MONEY, SIGNED, Col, DataTable, DetailsDialog, TableDialog, Toolbar,
                       confirm, fmt_active, fmt_bool, fmt_default, fmt_pct, fmt_rating,
                       run_action, safe_call)
from .base import BaseView

WALLET_COLS = [Col("walletid", "Wallet", 70), Col("wallettype", "Type", 90),
               Col("holderrole", "Role", 90), Col("hubname", "Hub", 150),
               Col("balance", "Balance", 120, **MONEY),
               Col("bonusrate", "Bonus", 70, anchor="e", fmt=fmt_pct),
               Col("isactive", "Status", 80, fmt=fmt_active)]
TXN_COLS = [Col("transactionid", "ID", 60), Col("transactiondate", "Date", 95),
            Col("walletid", "Wallet", 65), Col("transactiontype", "Type", 85),
            Col("amount", "Amount", 110, **SIGNED), Col("recipient", "Recipient", 170),
            Col("paymentmethod", "Method", 105)]
REVIEW_COLS = [Col("reviewid", "ID", 60), Col("walletid", "Wallet", 65),
               Col("wallettype", "Type", 80), Col("rating", "Rating", 90, fmt=fmt_rating),
               Col("reviewtext", "Review", 320), Col("reviewdate", "Date", 95),
               Col("isverified", "Verified", 70, fmt=fmt_bool)]


class PlayersView(BaseView):
    title = "Players"
    subtitle = "Every registered player. Select one to see their wallets, history and reviews."

    def __init__(self, parent, session):
        super().__init__(parent, session)
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 10))
        self.term = tk.StringVar()
        self.term.trace_add("write", lambda *_: self._apply_filter())
        ttk.Entry(bar, textvariable=self.term, width=34).pack(side="left")
        ttk.Label(bar, text="Filter by name or email", style="Muted.TLabel").pack(side="left",
                                                                                padx=(10, 0))

        tools = Toolbar(self)
        tools.pack(fill="x", pady=(0, 10))
        self.btns = [tools.add("Profile", self._profile),
                     tools.add("Wallet memberships", self._wallets),
                     tools.add("Transaction history", self._transactions),
                     tools.add("Review history", self._reviews)]
        self.btn_toggle = tools.add("Deactivate", self._toggle, style="Danger.TButton")
        self.btns.append(self.btn_toggle)

        self.all_rows: list[dict] = []
        self.table = DataTable(self, [
            Col("playerid", "ID", 60), Col("name", "Name", 160), Col("email", "Email", 230),
            Col("phone", "Phone", 120), Col("registrationdate", "Registered", 100),
            Col("isactive", "Status", 80, fmt=fmt_active),
        ], height=17, on_select=self._on_select, on_activate=lambda _r: self._profile())
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        rows = safe_call(self, api.list_players) or []
        for r in rows:
            r["name"] = f"{r['firstname']} {r['lastname']}"
        self.all_rows = rows
        self._apply_filter()

    def _apply_filter(self):
        term = self.term.get().strip().lower()
        rows = [r for r in self.all_rows
                if not term or term in r["name"].lower() or term in r["email"].lower()]
        self.table.set_rows(rows, muted=lambda r: not r["isactive"])

    def _on_select(self, row):
        for b in self.btns:
            b.state(["!disabled"] if row else ["disabled"])
        if row:
            self.btn_toggle.configure(text="Deactivate" if row["isactive"] else "Reactivate")

    # ------------------------------------------------------------------
    def _profile(self):
        r = self.table.selected()
        if r:
            DetailsDialog(self, r["name"], [
                ("Player ID", str(r["playerid"])), ("Email", r["email"]),
                ("Phone", r["phone"] or "—"), ("Date of birth", fmt_default(r["dateofbirth"])),
                ("Registered", fmt_default(r["registrationdate"])),
                ("Status", fmt_active(r["isactive"]))])

    def _wallets(self):
        r = self.table.selected()
        rows = r and safe_call(self, api.player_memberships, r["playerid"])
        if rows is not None and r:
            TableDialog(self, f"Wallet memberships · {r['name']}", WALLET_COLS, rows, width=760)

    def _transactions(self):
        r = self.table.selected()
        rows = r and safe_call(self, api.player_transactions, r["playerid"])
        if rows is not None and r:
            TableDialog(self, f"Transaction history · {r['name']}", TXN_COLS, rows,
                        subtitle="Across every wallet this player holds.", width=820, height=14)

    def _reviews(self):
        r = self.table.selected()
        rows = r and safe_call(self, api.player_reviews, r["playerid"])
        if rows is not None and r:
            TableDialog(self, f"Review history · {r['name']}", REVIEW_COLS, rows, width=860)

    def _toggle(self):
        r = self.table.selected()
        if not r:
            return
        activate = not r["isactive"]
        verb = "Reactivate" if activate else "Deactivate"
        note = "" if activate else "\nThey will no longer be able to sign in."
        if confirm(self, f"{verb} {r['name']}?{note}") and \
                run_action(self, api.set_player_active, r["playerid"], activate):
            self.refresh()
