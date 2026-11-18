"""Optional Task 4 (bonus):
  * option 2 - monthly top-ups vs cash-outs + purchases, as a bar chart
  * option 1 - bonus projection over 1, 6 and 12 months
"""
import tkinter as tk
from decimal import Decimal
from tkinter import ttk

from .. import api, theme
from ..widgets import MONEY, Card, Col, DataTable, fmt_money, fmt_pct, safe_call
from .base import BaseView, wallet_label

ALL_LABEL = "All my wallets"
ALL_LABEL_ADMIN = "All wallets"


def project_bonus(balance: Decimal, annual_rate_pct: Decimal, months: int) -> Decimal:
    """Bonus earned after `months`, compounding monthly on an annual % rate."""
    monthly = Decimal(annual_rate_pct) / Decimal(100) / Decimal(12)
    return (Decimal(balance) * ((1 + monthly) ** months - 1)).quantize(Decimal("0.01"))


class AnalyticsView(BaseView):
    title = "Analytics"
    subtitle = "Money in vs money out by month, and the bonus each wallet is on track to earn."

    def __init__(self, parent, session):
        super().__init__(parent, session)
        self.wallets: list[dict] = []
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 10))
        ttk.Label(bar, text="Show").pack(side="left", padx=(0, 6))
        self.choice = tk.StringVar()
        self.cb = ttk.Combobox(bar, textvariable=self.choice, state="readonly", width=40)
        self.cb.pack(side="left")
        self.cb.bind("<<ComboboxSelected>>", lambda _e: self._load())

        chart_card = Card(self, padding=(18, 14))
        chart_card.pack(fill="both", expand=True)
        ttk.Label(chart_card, text="Monthly top-ups vs spending", style="CardTitle.TLabel").pack(
            anchor="w")
        ttk.Label(chart_card, text="Spending = cash-outs + purchases. Transfers are excluded.",
                  style="CardMuted.TLabel").pack(anchor="w")
        self.chart = BarChart(chart_card)
        self.chart.pack(fill="both", expand=True, pady=(8, 0))

        proj_card = Card(self, padding=(18, 14))
        proj_card.pack(fill="x", pady=(14, 0))
        ttk.Label(proj_card, text="Bonus projection", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(proj_card, text="Bonus earned from the current balance at the wallet's annual "
                                  "bonus rate, compounded monthly.",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(0, 8))
        self.proj = DataTable(proj_card, [
            Col("walletid", "Wallet", 70), Col("wallettype", "Type", 90),
            Col("balance", "Balance", 120, **MONEY),
            Col("bonusrate", "Rate / yr", 80, anchor="e", fmt=fmt_pct),
            Col("m1", "+1 month", 110, **MONEY), Col("m6", "+6 months", 110, **MONEY),
            Col("m12", "+12 months", 110, **MONEY),
        ], height=5)
        self.proj.pack(fill="x")

    def refresh(self):
        self.wallets = self.my_wallets()
        all_label = ALL_LABEL_ADMIN if self.session.is_admin else ALL_LABEL
        self.cb.configure(values=[all_label] + [wallet_label(w) for w in self.wallets])
        if self.cb.current() < 0:
            self.cb.current(0)
        self._load()

    def _selected(self) -> dict | None:
        idx = self.cb.current()
        return self.wallets[idx - 1] if idx > 0 else None

    def _load(self):
        w = self._selected()
        rows = safe_call(self, api.monthly_flows, w["walletid"] if w else None,
                         self.session.actor) or []
        self.chart.set_data([(r["month"], Decimal(r["topups"]),
                              Decimal(r["cashouts"]) + Decimal(r["purchases"])) for r in rows])
        targets = [w] if w else self.wallets
        proj = []
        for x in targets:
            if not x["isactive"]:
                continue
            proj.append({**x, **{f"m{m}": project_bonus(x["balance"], x["bonusrate"], m)
                                 for m in (1, 6, 12)}})
        self.proj.set_rows(proj)


class BarChart(tk.Canvas):
    """Grouped bar chart drawn on a Canvas (no extra dependencies).

    Two series, fixed colors (validated categorical slots 1 and 2), a legend,
    a recessive grid and a hover tooltip per month.
    """
    SERIES = (("Top-ups", theme.SERIES_1), ("Spending", theme.SERIES_2))
    PAD_L, PAD_R, PAD_T, PAD_B = 64, 16, 34, 30

    def __init__(self, parent):
        super().__init__(parent, bg=theme.SURFACE, highlightthickness=0, height=260)
        self.data: list[tuple[str, Decimal, Decimal]] = []
        self._bands: list[tuple[float, float, tuple]] = []
        self.bind("<Configure>", lambda _e: self.draw())
        self.bind("<Motion>", self._hover)
        self.bind("<Leave>", lambda _e: self.delete("tip"))

    def set_data(self, data):
        self.data = data
        self.draw()

    def draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 50 or h < 50:
            return
        f_small = theme.font(9)
        # legend (top-left)
        x = self.PAD_L
        for name, color in self.SERIES:
            self.create_rectangle(x, 10, x + 12, 22, fill=color, outline="")
            self.create_text(x + 18, 16, text=name, anchor="w", font=f_small, fill=theme.TEXT)
            x += 100
        if not self.data:
            self.create_text(w / 2, h / 2, text="No top-ups, cash-outs or purchases yet.",
                             fill=theme.TEXT_MUTED, font=theme.font(10))
            return

        top = max(max(a, b) for _m, a, b in self.data) or Decimal(1)
        step = _nice_step(float(top) / 4)
        ymax = step * max(1, -(-float(top) // step))
        plot_h = h - self.PAD_T - self.PAD_B
        plot_w = w - self.PAD_L - self.PAD_R

        def y_of(v):
            return self.PAD_T + plot_h * (1 - float(v) / ymax)

        # grid + y labels
        v = 0.0
        while v <= ymax + 1e-9:
            y = y_of(v)
            self.create_line(self.PAD_L, y, w - self.PAD_R, y,
                             fill="#e9ebf1" if v else "#c7cbd6")
            self.create_text(self.PAD_L - 8, y, text=_compact(v), anchor="e", font=f_small,
                             fill=theme.TEXT_MUTED)
            v += step

        n = len(self.data)
        band = plot_w / n
        bar_w = max(4, min(28, band * 0.32))
        gap = 2
        self._bands = []
        for i, (month, a, b) in enumerate(self.data):
            cx = self.PAD_L + band * (i + 0.5)
            for j, val in enumerate((a, b)):
                x0 = cx - bar_w - gap / 2 if j == 0 else cx + gap / 2
                if val > 0:
                    self.create_rectangle(x0, y_of(val), x0 + bar_w, y_of(0),
                                          fill=self.SERIES[j][1], outline="")
            label_every = max(1, int(60 // band) + 1)
            if i % label_every == 0:
                self.create_text(cx, h - self.PAD_B + 14, text=month, font=f_small,
                                 fill=theme.TEXT_MUTED)
            self._bands.append((cx - band / 2, cx + band / 2, (month, a, b)))

    def _hover(self, event):
        self.delete("tip")
        for x0, x1, (month, a, b) in self._bands:
            if x0 <= event.x < x1 and self.PAD_T <= event.y <= self.winfo_height() - self.PAD_B:
                self.create_rectangle(x0, self.PAD_T, x1, self.winfo_height() - self.PAD_B,
                                      fill="", outline="#d5d8e2", dash=(2, 2), tags="tip")
                lines = [month, f"Top-ups   {fmt_money(a)}", f"Spending  {fmt_money(b)}"]
                tx = min(event.x + 14, self.winfo_width() - 170)
                ty = max(event.y - 60, 4)
                self.create_rectangle(tx, ty, tx + 160, ty + 58, fill=theme.SIDEBAR, outline="",
                                      tags="tip")
                for k, line in enumerate(lines):
                    self.create_text(tx + 10, ty + 12 + k * 17, text=line, anchor="w",
                                     fill="white" if k == 0 else theme.SIDEBAR_TEXT,
                                     font=theme.font(9, "bold" if k == 0 else "normal"),
                                     tags="tip")
                break


def _nice_step(raw: float) -> float:
    if raw <= 0:
        return 1.0
    mag = 10 ** len(str(int(raw))) / 10
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


def _compact(v: float) -> str:
    if v >= 1_000_000:
        return f"{v / 1_000_000:g}M"
    if v >= 1000:
        return f"{v / 1000:g}k"
    return f"{v:g}"
