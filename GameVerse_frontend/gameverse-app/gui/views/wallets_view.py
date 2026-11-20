"""Module 3: Wallet management."""

from .. import api, validators
from ..widgets import (MONEY, Col, DataTable, DetailsDialog, Field, FormDialog, TableDialog,
                       Toolbar, ask_value, confirm, fmt_active, fmt_default, fmt_money, fmt_pct,
                       humanize, info, run_action, safe_call)
from .base import BaseView


def show_wallet_details(parent, walletid: int, session) -> None:
    """Wallet row + getWalletSummary() in one dialog (used by several pages)."""
    w = safe_call(parent, api.get_wallet, walletid, session.actor)
    if not w:
        return
    summary = safe_call(parent, api.get_wallet_summary, walletid, session.actor) or {}
    rows = [
        ("Type", w["wallettype"]), ("Hub", w.get("hubname") or str(w["hubid"])),
        ("Status", fmt_active(w["isactive"])), ("Balance", fmt_money(w["balance"])),
        ("Minimum balance", fmt_money(w["minimumbalance"])),
        ("Spendable", fmt_money(max(w["balance"] - w["minimumbalance"], 0))),
        ("Bonus rate (annual)", fmt_pct(w["bonusrate"])),
        ("Opened", fmt_default(w["opendate"])), ("Description", w["walletdescription"] or "—"),
    ]
    # getWalletSummary keys are shown generically so the backend can name them freely
    extra = [(humanize(k), fmt_default(v)) for k, v in summary.items() if k != "balance"]
    if extra:
        rows.append(("", ""))
        rows.append(("ACTIVITY SUMMARY", ""))
        rows.extend(extra)
    DetailsDialog(parent, f"Wallet #{walletid}", rows)


class WalletsView(BaseView):
    title = "Wallets"

    def subtitle_for(self, session):
        return ("Open, edit and deactivate wallets; view the full inventory." if session.is_admin
                else "Wallets you hold and your role on each.")

    def __init__(self, parent, session):
        super().__init__(parent, session)
        admin = session.is_admin
        tools = Toolbar(self)
        tools.pack(fill="x", pady=(0, 10))
        self.btn_details = tools.add("View details", self._details)
        if admin:
            tools.add("+ Open wallet", self._open, style="Primary.TButton")
            self.btn_edit = tools.add("Edit", self._edit)
            self.btn_toggle = tools.add("Deactivate", self._toggle, style="Danger.TButton")
            tools.add("Inventory by type", self._inventory, side="right")
        else:
            self.btn_txn = tools.add("New transaction", lambda: self.navigate("transactions"),
                                     style="Primary.TButton")
        tools.add("Low-balance alert", self._low_balance, side="right")

        cols = [Col("walletid", "ID", 60), Col("wallettype", "Type", 90),
                Col("hubname", "Hub", 150)]
        cols.append(Col("owner", "Owner", 150) if admin else Col("holderrole", "Your role", 100))
        cols += [Col("balance", "Balance", 120, **MONEY),
                 Col("minimumbalance", "Minimum", 100, **MONEY),
                 Col("bonusrate", "Bonus", 70, anchor="e", fmt=fmt_pct),
                 Col("opendate", "Opened", 100), Col("isactive", "Status", 80, fmt=fmt_active)]
        self.table = DataTable(self, cols, height=16, on_select=self._on_select,
                               on_activate=lambda _r: self._details(),
                               empty_text="No wallets yet." if admin else
                               "You do not hold any wallets yet. Ask an admin to open one.")
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        self.table.set_rows(self.my_wallets(), muted=lambda r: not r["isactive"])

    def _on_select(self, row):
        state = ["!disabled"] if row else ["disabled"]
        self.btn_details.state(state)
        if self.session.is_admin:
            self.btn_edit.state(state)
            self.btn_toggle.state(state)
            if row:
                self.btn_toggle.configure(text="Deactivate" if row["isactive"] else "Reactivate")

    # ------------------------------------------------------------------
    def _details(self):
        row = self.table.selected()
        if row:
            show_wallet_details(self, row["walletid"], self.session)

    def _low_balance(self):
        threshold = ask_value(self, "Low-balance alert", "Show wallets with a balance below",
                              validators.money, default="1000.00", submit_text="Show")
        if threshold is None:
            return
        rows = safe_call(self, api.low_balance_alerts, threshold, self.session.actor)
        if rows is not None:
            TableDialog(self, "Low-balance alert", [
                Col("walletid", "Wallet", 70), Col("wallettype", "Type", 90),
                Col("hubname", "Hub", 170), Col("balance", "Balance", 120, **MONEY),
                Col("minimumbalance", "Minimum", 120, **MONEY),
            ], rows, subtitle=f"Active wallets with a balance below {fmt_money(threshold)}.",
                width=640)

    def _open(self):
        players = safe_call(self, api.list_players) or []
        hubs = safe_call(self, api.list_hubs, True) or []
        fields = [
            Field("playerid", "Owner (player)", kind="combo", options=[
                (p["playerid"], f"#{p['playerid']}  {p['firstname']} {p['lastname']}")
                for p in players if p["isactive"]]),
            Field("wallettype", "Wallet type", kind="combo", options=api.WALLET_TYPES,
                  default="Standard"),
            Field("hubid", "Hub", kind="combo",
                  options=[(h["hubid"], f"#{h['hubid']}  {h['hubname']}") for h in hubs]),
            Field("balance", "Initial balance", parse=validators.money_or_zero, default="100.00",
                  hint="Must be at least the minimum balance"),
            Field("minimumbalance", "Minimum balance", parse=validators.money_or_zero,
                  default="100.00"),
            Field("bonusrate", "Bonus rate (% per year)", parse=validators.rate_0_to_5,
                  default="0.10", hint="Between 0 and 5"),
            Field("description", "Description", kind="text", required=False),
        ]

        def submit(v):
            if v["balance"] < v["minimumbalance"]:
                raise ValueError("Initial balance must be at least the minimum balance.")
            return api.open_wallet(v["playerid"], v["wallettype"], v["hubid"], v["balance"],
                                   v["minimumbalance"], v["bonusrate"], v["description"])

        dlg = FormDialog(self, "Open a new wallet", fields, submit, submit_text="Open wallet",
                         intro="Creates the wallet and its Owner holder record in one "
                               "database transaction.")
        self.wait_window(dlg)
        if dlg.result:
            self.refresh()
            info(self, f"Wallet #{dlg.result} opened.")

    def _edit(self):
        row = self.table.selected()
        if not row:
            return
        fields = [Field("bonusrate", "Bonus rate (% per year)", parse=validators.rate_0_to_5,
                        default=str(row["bonusrate"]), hint="Between 0 and 5"),
                  Field("description", "Description", kind="text", required=False,
                        default=row.get("walletdescription") or "")]

        def submit(v):
            api.update_wallet(row["walletid"], v["bonusrate"], v["description"])
            return True

        dlg = FormDialog(self, f"Edit wallet #{row['walletid']}", fields, submit)
        self.wait_window(dlg)
        if dlg.result:
            self.refresh()

    def _toggle(self):
        row = self.table.selected()
        if not row:
            return
        activate = not row["isactive"]
        verb = "Reactivate" if activate else "Deactivate"
        extra = "" if activate else "\nNo transactions will be accepted while it is inactive."
        if confirm(self, f"{verb} wallet #{row['walletid']}?{extra}") and \
                run_action(self, api.set_wallet_active, row["walletid"], activate):
            self.refresh()

    def _inventory(self):
        rows = safe_call(self, api.wallet_inventory)
        if rows is not None:
            TableDialog(self, "Wallet inventory", [
                Col("wallettype", "Type", 110), Col("wallet_count", "Wallets", 80, anchor="e"),
                Col("active_count", "Active", 80, anchor="e"),
                Col("total_balance", "Total balance", 140, **MONEY),
                Col("avg_balance", "Average balance", 140, **MONEY),
            ], rows, subtitle="All wallets grouped by type.", width=640, height=5)
