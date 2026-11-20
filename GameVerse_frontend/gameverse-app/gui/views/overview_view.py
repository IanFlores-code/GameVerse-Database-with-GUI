"""Landing page: headline numbers + a short table for each role."""
from decimal import Decimal
from tkinter import ttk

from .. import api
from ..widgets import MONEY, SIGNED, Card, Col, DataTable, StatCard, fmt_money, safe_call
from .base import BaseView

LOW_BALANCE_THRESHOLD = Decimal("1000")


class OverviewView(BaseView):
    title = "Overview"

    def subtitle_for(self, session):
        first = session.display_name.split(" ")[0]
        return ("Platform-wide snapshot of hubs, wallets and players." if session.is_admin
                else f"Welcome back, {first}. Here is where your wallets stand.")

    def __init__(self, parent, session):
        super().__init__(parent, session)
        stats = ttk.Frame(self)
        stats.pack(fill="x")
        labels = (["Active hubs", "Wallets", "Players", "Total balance held"] if session.is_admin
                  else ["Wallets held", "Total balance", "Spendable", "Reviews written"])
        self.cards = []
        for i, lbl in enumerate(labels):
            c = StatCard(stats, lbl)
            c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 12, 0))
            stats.columnconfigure(i, weight=1, uniform="stats")
            self.cards.append(c)

        box = Card(self)
        box.pack(fill="both", expand=True, pady=(18, 0))
        if session.is_admin:
            ttk.Label(box, text=f"Low-balance alerts (balance below {fmt_money(LOW_BALANCE_THRESHOLD)})",
                      style="CardTitle.TLabel").pack(anchor="w", pady=(0, 10))
            cols = [Col("walletid", "Wallet", 80), Col("wallettype", "Type", 100),
                    Col("hubname", "Hub", 180), Col("balance", "Balance", 120, **MONEY),
                    Col("minimumbalance", "Minimum", 120, **MONEY)]
            empty = "No active wallet is below the threshold."
        else:
            ttk.Label(box, text="Recent activity", style="CardTitle.TLabel").pack(anchor="w",
                                                                                 pady=(0, 10))
            cols = [Col("transactiondate", "Date", 110), Col("walletid", "Wallet", 80),
                    Col("transactiontype", "Type", 110), Col("amount", "Amount", 120, **SIGNED),
                    Col("recipient", "Recipient", 200), Col("paymentmethod", "Method", 120)]
            empty = "No transactions yet."
        self.table = DataTable(box, cols, height=10, empty_text=empty)
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        if self.session.is_admin:
            hubs = safe_call(self, api.list_hubs, True) or []
            wallets = safe_call(self, api.list_all_wallets) or []
            players = safe_call(self, api.list_players) or []
            total = sum((w["balance"] for w in wallets if w["isactive"]), Decimal(0))
            self.cards[0].set(str(len(hubs)))
            self.cards[1].set(str(len(wallets)), f"{sum(w['isactive'] for w in wallets)} active")
            self.cards[2].set(str(len(players)), f"{sum(p['isactive'] for p in players)} active")
            self.cards[3].set(fmt_money(total), "across active wallets")
            self.table.set_rows(safe_call(self, api.low_balance_alerts, LOW_BALANCE_THRESHOLD))
        else:
            pid = self.session.playerid
            wallets = safe_call(self, api.list_player_wallets, pid) or []
            reviews = safe_call(self, api.player_reviews, pid) or []
            total = sum((w["balance"] for w in wallets), Decimal(0))
            spendable = sum((max(w["balance"] - w["minimumbalance"], 0) for w in wallets
                             if w["isactive"] and w["holderrole"] in ("Owner", "Co-Owner")),
                            Decimal(0))
            self.cards[0].set(str(len(wallets)))
            self.cards[1].set(fmt_money(total))
            self.cards[2].set(fmt_money(spendable), "above minimum, where you can transact")
            self.cards[3].set(str(len(reviews)))
            self.table.set_rows((safe_call(self, api.player_transactions, pid) or [])[:12])
