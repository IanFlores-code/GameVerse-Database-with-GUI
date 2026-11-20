"""Module 2: Hub management (browse/search for everyone, CRUD for admins)."""
import tkinter as tk
from tkinter import ttk

from .. import api, validators
from ..widgets import (MONEY, Col, DataTable, DetailsDialog, Field, FormDialog, TableDialog,
                       Toolbar, confirm, fmt_active, fmt_money, fmt_pct, info, run_action,
                       safe_call)
from .base import BaseView


class HubsView(BaseView):
    title = "Gaming hubs"

    def subtitle_for(self, session):
        return ("Add, edit, deactivate and report on hubs." if session.is_admin
                else "Browse the active GameVerse hubs.")

    def __init__(self, parent, session):
        super().__init__(parent, session)
        admin = session.is_admin

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 10))
        self.term = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.term, width=34)
        entry.pack(side="left")
        entry.bind("<Return>", lambda _e: self.refresh())
        ttk.Button(bar, text="Search", command=self.refresh).pack(side="left", padx=(8, 0))
        ttk.Button(bar, text="Clear", command=self._clear).pack(side="left", padx=(8, 0))
        self.include_inactive = tk.BooleanVar(value=admin)
        if admin:
            ttk.Checkbutton(bar, text="Include inactive hubs", variable=self.include_inactive,
                            command=self.refresh).pack(side="left", padx=(16, 0))
        ttk.Label(bar, text="Search by name or location", style="Muted.TLabel").pack(side="right")

        tools = Toolbar(self)
        tools.pack(fill="x", pady=(0, 10))
        self.btn_details = tools.add("View details", self._details)
        if admin:
            tools.add("+ Add hub", self._add, style="Primary.TButton")
            self.btn_edit = tools.add("Edit", self._edit)
            self.btn_toggle = tools.add("Deactivate", self._toggle, style="Danger.TButton")
            tools.add("Hub summary report", self._report, side="right")

        self.table = DataTable(self, [
            Col("hubid", "ID", 60), Col("hubname", "Hub name", 220),
            Col("location", "Location", 320), Col("isactive", "Status", 100, fmt=fmt_active),
        ], height=16, on_select=self._on_select, on_activate=lambda _r: self._details(),
            empty_text="No hubs match your search.")
        self.table.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    def refresh(self):
        active_only = not self.include_inactive.get()
        term = self.term.get().strip()
        rows = (safe_call(self, api.search_hubs, term, active_only) if term
                else safe_call(self, api.list_hubs, active_only))
        self.table.set_rows(rows, muted=lambda r: not r["isactive"])

    def _clear(self):
        self.term.set("")
        self.refresh()

    def _on_select(self, row):
        state = ["!disabled"] if row else ["disabled"]
        self.btn_details.state(state)
        if self.session.is_admin:
            self.btn_edit.state(state)
            self.btn_toggle.state(state)
            if row:
                self.btn_toggle.configure(text="Deactivate" if row["isactive"] else "Reactivate")

    def _details(self):
        row = self.table.selected()
        if not row:
            return
        d = safe_call(self, api.get_hub_details, row["hubid"])
        if d:
            DetailsDialog(self, d["hubname"], [
                ("Hub ID", str(d["hubid"])), ("Location", d["location"] or "—"),
                ("Status", fmt_active(d["isactive"])),
                ("Total wallets", f"{d['total_wallets']}  ({d.get('active_wallets', '—')} active)"),
                ("Total balance held", fmt_money(d["total_balance"])),
            ])

    def _hub_fields(self, row=None):
        return [Field("hubname", "Hub name", default=row["hubname"] if row else "",
                      parse=validators.text(100)),
                Field("location", "Location", default=(row or {}).get("location") or "",
                      parse=validators.text(255), required=False)]

    def _add(self):
        dlg = FormDialog(self, "Add a hub", self._hub_fields(),
                         lambda v: api.add_hub(v["hubname"], v["location"]), submit_text="Add hub")
        self.wait_window(dlg)
        if dlg.result:
            self.refresh()
            info(self, f"Hub #{dlg.result} created.")

    def _edit(self):
        row = self.table.selected()
        if not row:
            return

        def submit(v):
            api.update_hub(row["hubid"], v["hubname"], v["location"])
            return True

        dlg = FormDialog(self, f"Edit hub #{row['hubid']}", self._hub_fields(row), submit)
        self.wait_window(dlg)
        if dlg.result:
            self.refresh()

    def _toggle(self):
        row = self.table.selected()
        if not row:
            return
        activate = not row["isactive"]
        verb = "Reactivate" if activate else "Deactivate"
        if not confirm(self, f"{verb} hub '{row['hubname']}'?"):
            return
        if run_action(self, api.set_hub_active, row["hubid"], activate):
            self.refresh()

    def _report(self):
        rows = safe_call(self, api.hub_summary_report)
        if rows is not None:
            TableDialog(self, "Hub summary report", [
                Col("hubid", "ID", 50), Col("hubname", "Hub", 180),
                Col("isactive", "Status", 90, fmt=fmt_active),
                Col("wallet_count", "Wallets", 80, anchor="e"),
                Col("total_balance", "Total balance", 140, **MONEY),
                Col("avg_bonus_rate", "Avg bonus rate", 120, anchor="e", fmt=fmt_pct),
            ], rows, subtitle="Wallets per hub, total balance and average bonus rate.")
