"""Module 5: Transaction processing and history.

Left: a form to perform a transaction (calls performTransaction / transferFunds).
Right: history for one wallet with date-range and type filters.

Balance rules are NOT re-implemented here: the database functions decide, and
their messages (e.g. "Insufficient funds. Spendable balance: ...") are shown
as-is. The live "funds check" hint calls checkSufficientBalance().
"""
import tkinter as tk
from decimal import Decimal
from tkinter import ttk

from .. import api, theme, validators
from ..widgets import (MONEY, SIGNED, Card, Col, DataTable, Segmented, TableDialog, Toolbar,
                       confirm, fmt_money, info, safe_call, warn)
from .base import BaseView, wallet_label
from .wallets_view import show_wallet_details

ALL = "All types"
NEAR_MINIMUM = Decimal("0.10")      # warn when within 10% of the minimum (Task 4, option 5)


class TransactionsView(BaseView):
    title = "Transactions"

    def subtitle_for(self, session):
        return ("Perform transactions, review history and reverse transactions." if session.is_admin
                else "Top up, cash out, buy and transfer between wallets.")

    def __init__(self, parent, session):
        super().__init__(parent, session)
        self.wallets: list[dict] = []
        self._check_job = None

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        self._build_form(body)
        self._build_history(body)

    # ================================================================ form
    def _build_form(self, parent):
        card = Card(parent, padding=20, width=340)
        card.grid(row=0, column=0, sticky="nsw", padx=(0, 18))
        card.pack_propagate(False)          # fixed width; long hints wrap instead of widening
        ttk.Label(card, text="New transaction", style="CardTitle.TLabel").pack(anchor="w")

        self.f_wallet = tk.StringVar()
        self.f_type = tk.StringVar(value="TopUp")
        self.f_amount = tk.StringVar()
        self.f_method = tk.StringVar(value=api.PAYMENT_METHODS[0])
        self.f_recipient = tk.StringVar()
        self.f_dest = tk.StringVar()

        def label(text):
            ttk.Label(card, text=text, style="Card.TLabel").pack(anchor="w", pady=(12, 2))

        label("From wallet")
        self.cb_wallet = ttk.Combobox(card, textvariable=self.f_wallet, state="readonly")
        self.cb_wallet.pack(fill="x")
        self.cb_wallet.bind("<<ComboboxSelected>>", lambda _e: self._form_changed())
        self.wallet_note = ttk.Label(card, text="", style="Hint.TLabel", wraplength=290)
        self.wallet_note.pack(anchor="w", pady=(4, 0))

        label("Type")
        Segmented(card, self.f_type, [(t, t) for t in api.TRANSACTION_TYPES],
                  command=self._form_changed).pack(fill="x")

        label("Amount")
        amount = ttk.Entry(card, textvariable=self.f_amount)
        amount.pack(fill="x")
        self.f_amount.trace_add("write", lambda *_: self._schedule_check())
        self.funds_note = ttk.Label(card, text="", style="Hint.TLabel", wraplength=290)
        self.funds_note.pack(anchor="w", pady=(4, 0))

        label("Payment method")
        ttk.Combobox(card, textvariable=self.f_method, values=api.PAYMENT_METHODS,
                     state="readonly").pack(fill="x")

        self.recipient_label = ttk.Label(card, text="Recipient", style="Card.TLabel")
        self.recipient_entry = ttk.Entry(card, textvariable=self.f_recipient)
        self.dest_label = ttk.Label(card, text="Destination wallet ID", style="Card.TLabel")
        self.dest_entry = ttk.Combobox(card, textvariable=self.f_dest)
        self.dest_hint = ttk.Label(card, text="Pick one of your wallets or type any wallet ID",
                                   style="Hint.TLabel")
        self.dynamic_anchor = ttk.Frame(card, style="Card.TFrame", height=0)
        self.dynamic_anchor.pack(fill="x")

        self.submit_btn = ttk.Button(card, text="Submit transaction", style="Primary.TButton",
                                     command=self._submit)
        self.submit_btn.pack(fill="x", pady=(20, 0))
        self._form_changed()

    def _selected_wallet(self) -> dict | None:
        idx = self.cb_wallet.current()
        return self.wallets[idx] if 0 <= idx < len(self.wallets) else None

    def _form_changed(self):
        t = self.f_type.get()
        for w in (self.recipient_label, self.recipient_entry, self.dest_label, self.dest_entry,
                  self.dest_hint):
            w.pack_forget()
        if t == "Purchase":
            self.recipient_label.pack(anchor="w", pady=(12, 2), before=self.dynamic_anchor)
            self.recipient_entry.pack(fill="x", before=self.dynamic_anchor)
            self.recipient_label.configure(text="Recipient (store / item)")
        elif t == "Transfer":
            self.dest_label.pack(anchor="w", pady=(12, 2), before=self.dynamic_anchor)
            self.dest_entry.pack(fill="x", before=self.dynamic_anchor)
            self.dest_hint.pack(anchor="w", pady=(4, 0), before=self.dynamic_anchor)

        w = self._selected_wallet()
        can_transact = True
        if w is None:
            note, can_transact = "No wallet selected.", False
        elif not w["isactive"]:
            note, can_transact = "This wallet is inactive. Transactions are blocked.", False
        elif not self.session.is_admin and w.get("holderrole") not in ("Owner", "Co-Owner"):
            note = (f"You are a {w.get('holderrole')} on this wallet: you can view it but "
                    "only an Owner or Co-Owner can transact.")
            can_transact = False
        else:
            spend = max(w["balance"] - w["minimumbalance"], 0)
            note = (f"Balance {fmt_money(w['balance'])} · minimum {fmt_money(w['minimumbalance'])}"
                    f" · spendable {fmt_money(spend)}")
        self.wallet_note.configure(text=note)
        self.submit_btn.state(["!disabled"] if can_transact else ["disabled"])
        self.dest_entry.configure(values=[str(x["walletid"]) for x in self.wallets
                                          if w is None or x["walletid"] != w["walletid"]])
        self._schedule_check()

    def _schedule_check(self):
        if self._check_job:
            self.after_cancel(self._check_job)
        self._check_job = self.after(350, self._funds_check)

    def _funds_check(self):
        """Live hint using checkSufficientBalance() (no rule duplicated in the UI)."""
        self._check_job = None
        w = self._selected_wallet()
        if not w or self.f_type.get() == "TopUp" or not self.f_amount.get().strip():
            self.funds_note.configure(text="")
            return
        try:
            amount = validators.money(self.f_amount.get())
            ok = api.check_sufficient_balance(w["walletid"], amount)
        except (ValueError, api.AppError):
            self.funds_note.configure(text="")
            return
        self.funds_note.configure(
            text="✓ Enough funds above the minimum balance" if ok
            else "✗ Not enough funds: would go below the minimum balance",
            foreground=theme.SUCCESS if ok else theme.DANGER)

    def _submit(self):
        w = self._selected_wallet()
        if not w:
            return warn(self, "Choose a wallet first.")
        try:
            amount = validators.money(self.f_amount.get())
        except ValueError as exc:
            return warn(self, f"Amount: {exc}.")
        t, method = self.f_type.get(), self.f_method.get()
        wid = w["walletid"]

        if t == "Transfer":
            try:
                dest = validators.integer(self.f_dest.get())
            except ValueError:
                return warn(self, "Enter the destination wallet ID (a number).")
            if not confirm(self, f"Transfer {fmt_money(amount)} from wallet #{wid} "
                                 f"to wallet #{dest}?"):
                return
            txn = safe_call(self, api.transfer_funds, wid, dest, amount, method, self.session.actor)
        else:
            recipient = self.f_recipient.get().strip() if t == "Purchase" else "Self"
            if t == "Purchase" and not recipient:
                return warn(self, "Enter who the purchase is from (recipient).")
            txn = safe_call(self, api.perform_transaction, wid, amount, t, method, recipient,
                            self.session.actor)
        if txn is None:
            return
        self.f_amount.set("")
        self.f_recipient.set("")
        self._after_success(wid, t, txn)

    def _after_success(self, walletid: int, txn_type: str, txn_id: int):
        """Confirmation + near-minimum warning (Task 4 option 5: notifications)."""
        self.refresh(keep_wallet=walletid)
        w = next((x for x in self.wallets if x["walletid"] == walletid), None)
        if not w:
            return info(self, f"Transaction #{txn_id} completed.")
        msg = f"Transaction #{txn_id} completed.\nNew balance of wallet #{walletid}: " \
              f"{fmt_money(w['balance'])}"
        if txn_type == "TopUp":
            info(self, msg, title="Top-up confirmed")
        else:
            info(self, msg)
            minimum = w["minimumbalance"]
            if w["balance"] <= minimum * (1 + NEAR_MINIMUM):
                warn(self, f"Heads up: wallet #{walletid} is within 10% of its minimum balance "
                           f"({fmt_money(w['balance'])} vs minimum {fmt_money(minimum)}).",
                     title="Low balance")

    # ============================================================= history
    def _build_history(self, parent):
        right = ttk.Frame(parent)
        right.grid(row=0, column=1, sticky="nsew")

        filt = ttk.Frame(right)
        filt.pack(fill="x", pady=(0, 10))
        self.h_wallet = tk.StringVar()
        self.h_from = tk.StringVar()
        self.h_to = tk.StringVar()
        self.h_type = tk.StringVar(value=ALL)
        ttk.Label(filt, text="History for wallet").pack(anchor="w")
        self.cb_hist = ttk.Combobox(filt, textvariable=self.h_wallet, state="readonly", width=40)
        self.cb_hist.pack(anchor="w", pady=(2, 8))
        self.cb_hist.bind("<<ComboboxSelected>>", lambda _e: self._load_history())

        row = ttk.Frame(filt)
        row.pack(fill="x")

        def labeled(text, widget_factory):
            box = ttk.Frame(row)
            box.pack(side="left", padx=(0, 8))
            ttk.Label(box, text=text).pack(anchor="w")
            widget_factory(box).pack(anchor="w")

        labeled("From (YYYY-MM-DD)", lambda b: ttk.Entry(b, textvariable=self.h_from, width=12))
        labeled("To (YYYY-MM-DD)", lambda b: ttk.Entry(b, textvariable=self.h_to, width=12))
        labeled("Type", lambda b: ttk.Combobox(
            b, textvariable=self.h_type, state="readonly", width=10,
            values=[ALL] + api.TRANSACTION_TYPES + ["Reversal"]))
        ttk.Button(row, text="Clear", width=6, command=self._clear_filters).pack(side="right", anchor="s")
        ttk.Button(row, text="Apply", width=6, command=self._load_history).pack(side="right", anchor="s",
                                                                      padx=(0, 6))

        tools = Toolbar(right)
        tools.pack(fill="x", pady=(0, 10))
        tools.add("Wallet summary", self._summary)
        tools.add("Totals by payment method", self._by_method)
        if self.session.is_admin:
            self.btn_reverse = tools.add("Reverse transaction", self._reverse,
                                         style="Danger.TButton")

        self.table = DataTable(right, [
            Col("transactionid", "ID", 55), Col("transactiondate", "Date", 90),
            Col("transactiontype", "Type", 80), Col("amount", "Amount", 100, **SIGNED),
            Col("recipient", "Recipient / source", 140), Col("paymentmethod", "Method", 95),
            Col("linkedtxnid", "Linked", 50),
        ], height=18, on_select=self._on_select, empty_text="No transactions match these filters.")
        self.table.pack(fill="both", expand=True)

    def _on_select(self, row):
        if self.session.is_admin:
            ok = row is not None and row["transactiontype"] != "Reversal"
            self.btn_reverse.state(["!disabled"] if ok else ["disabled"])

    def _hist_wallet(self) -> dict | None:
        idx = self.cb_hist.current()
        return self.wallets[idx] if 0 <= idx < len(self.wallets) else None

    def _clear_filters(self):
        self.h_from.set("")
        self.h_to.set("")
        self.h_type.set(ALL)
        self._load_history()

    def _load_history(self):
        w = self._hist_wallet()
        if not w:
            self.table.set_rows([])
            return
        try:
            d_from = validators.iso_date(self.h_from.get()) if self.h_from.get().strip() else None
            d_to = validators.iso_date(self.h_to.get()) if self.h_to.get().strip() else None
        except ValueError:
            return warn(self, "Dates must use the format YYYY-MM-DD.")
        if d_from and d_to and d_from > d_to:
            return warn(self, "The 'From' date must be on or before the 'To' date.")
        t = None if self.h_type.get() == ALL else self.h_type.get()
        rows = safe_call(self, api.wallet_transactions, w["walletid"], d_from, d_to, t,
                         self.session.actor)
        self.table.set_rows(rows or [], muted=lambda r: r["transactiontype"] == "Reversal")

    def _summary(self):
        w = self._hist_wallet()
        if w:
            show_wallet_details(self, w["walletid"], self.session)

    def _by_method(self):
        w = self._hist_wallet()
        rows = safe_call(self, api.totals_by_payment_method,
                         w["walletid"] if w else None, self.session.actor)
        if rows is not None:
            TableDialog(self, "Totals by payment method", [
                Col("paymentmethod", "Payment method", 150),
                Col("txn_count", "Transactions", 100, anchor="e"),
                Col("total_in", "Money in", 120, **MONEY),
                Col("total_out", "Money out", 120, **MONEY),
                Col("total_volume", "Total volume", 130, **MONEY),
            ], rows, subtitle=f"Wallet #{w['walletid']}" if w else "", width=700, height=6)

    def _reverse(self):
        row = self.table.selected()
        if not row:
            return
        extra = " Both legs of the transfer will be reversed." \
            if row["transactiontype"] == "Transfer" else ""
        if not confirm(self, f"Reverse transaction #{row['transactionid']} "
                             f"({row['transactiontype']} {fmt_money(row['amount'])})?{extra}\n"
                             "This restores the wallet balance."):
            return
        ids = safe_call(self, api.reverse_transaction, row["transactionid"])
        if ids:
            self.refresh(keep_wallet=row["walletid"])
            info(self, "Reversal recorded as transaction(s) " + ", ".join(f"#{i}" for i in ids) + ".")

    # ============================================================= refresh
    def refresh(self, keep_wallet: int | None = None):
        form_w, hist_w = self._selected_wallet(), self._hist_wallet()
        self.wallets = self.my_wallets()
        labels = [wallet_label(w) for w in self.wallets]
        self.cb_wallet.configure(values=labels)
        self.cb_hist.configure(values=labels)
        ids = [w["walletid"] for w in self.wallets]

        def reselect(cb, previous):
            target = keep_wallet or (previous["walletid"] if previous else None)
            if target in ids:
                cb.current(ids.index(target))
            elif ids:
                cb.current(0)
            else:
                cb.set("")

        reselect(self.cb_wallet, form_w)
        reselect(self.cb_hist, hist_w)
        self._form_changed()
        self._load_history()
