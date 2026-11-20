"""Reusable widgets: tables, form dialogs, detail dialogs, page headers.

Every view is built from these, so screens look and behave the same way.
"""
import tkinter as tk
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from tkinter import messagebox, ttk
from typing import Any, Callable

from . import theme
from .api import AppError


# ======================================================================
# Formatting
# ======================================================================
def fmt_money(v) -> str:
    if v is None:
        return "—"
    return f"{Decimal(v):,.2f}"


def fmt_signed(v) -> str:
    if v is None:
        return "—"
    d = Decimal(v)
    return f"+{d:,.2f}" if d > 0 else f"{d:,.2f}"


def fmt_pct(v) -> str:
    return "—" if v is None else f"{Decimal(v):.2f}%"


def fmt_bool(v) -> str:
    return "—" if v is None else ("Yes" if v else "No")


def fmt_active(v) -> str:
    return "Active" if v else "Inactive"


def fmt_rating(v) -> str:
    return "—" if v is None else "★" * int(v) + "☆" * (5 - int(v))


def fmt_default(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return fmt_bool(v)
    if isinstance(v, Decimal):
        return f"{v:,.2f}"
    if isinstance(v, date):
        return v.isoformat()
    return str(v)


def humanize(key: str) -> str:
    """'total_topups' -> 'Total topups' (used for generic backend result keys)."""
    return key.replace("_", " ").strip().capitalize()


# ======================================================================
# Error handling
# ======================================================================
def safe_call(parent: tk.Misc, fn: Callable, *args, **kwargs):
    """Run an api call; show AppError messages in a dialog instead of crashing.
    Returns the result, or None if it failed."""
    try:
        return fn(*args, **kwargs)
    except AppError as exc:
        messagebox.showerror("GameVerse", str(exc), parent=parent.winfo_toplevel())
    except Exception as exc:          # never show a stack trace to the user
        messagebox.showerror("GameVerse", f"Something went wrong: {exc}",
                             parent=parent.winfo_toplevel())
    return None


def run_action(parent: tk.Misc, fn: Callable, *args, success: str | None = None) -> bool:
    """Like safe_call for actions that return nothing. True if it worked."""
    try:
        fn(*args)
    except AppError as exc:
        messagebox.showerror("GameVerse", str(exc), parent=parent.winfo_toplevel())
        return False
    except Exception as exc:
        messagebox.showerror("GameVerse", f"Something went wrong: {exc}",
                             parent=parent.winfo_toplevel())
        return False
    if success:
        info(parent, success)
    return True


def info(parent: tk.Misc, message: str, title: str = "GameVerse") -> None:
    messagebox.showinfo(title, message, parent=parent.winfo_toplevel())


def warn(parent: tk.Misc, message: str, title: str = "GameVerse") -> None:
    messagebox.showwarning(title, message, parent=parent.winfo_toplevel())


def confirm(parent: tk.Misc, message: str, title: str = "Please confirm") -> bool:
    return messagebox.askyesno(title, message, parent=parent.winfo_toplevel())


# ======================================================================
# Layout pieces
# ======================================================================
class PageHeader(ttk.Frame):
    def __init__(self, parent, title: str, subtitle: str = ""):
        super().__init__(parent)
        ttk.Label(self, text=title, style="Title.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(self, text=subtitle, style="Subtitle.TLabel").pack(anchor="w", pady=(2, 0))


class Toolbar(ttk.Frame):
    """A row of buttons. add() returns the button so views can enable/disable it."""

    def add(self, text: str, command: Callable, style: str = "TButton", side="left") -> ttk.Button:
        btn = ttk.Button(self, text=text, command=command, style=style)
        btn.pack(side=side, padx=(0, 8) if side == "left" else (8, 0))
        return btn


class Card(ttk.Frame):
    """White panel with a 1px border."""

    def __init__(self, parent, padding=16, **kw):
        super().__init__(parent, style="Bordered.TFrame", padding=padding, **kw)


class Segmented(tk.Frame):
    """Segmented toggle (e.g. Player | Admin) bound to a StringVar."""

    def __init__(self, parent, variable: tk.StringVar, options: list[tuple[str, str]],
                 command: Callable[[], None] | None = None):
        super().__init__(parent, bg=theme.BORDER)
        self.variable = variable
        self.command = command
        self.labels: dict[str, tk.Label] = {}
        for i, (value, text) in enumerate(options):
            lbl = tk.Label(self, text=text, font=theme.font(10), padx=8, pady=6, cursor="hand2")
            lbl.grid(row=0, column=i, sticky="nsew", padx=(1, 1 if i == len(options) - 1 else 0),
                     pady=1)
            lbl.bind("<Button-1>", lambda _e, v=value: self._pick(v))
            self.columnconfigure(i, weight=1, uniform="seg")
            self.labels[value] = lbl
        variable.trace_add("write", lambda *_: self._paint())
        self._paint()

    def _pick(self, value: str) -> None:
        self.variable.set(value)
        if self.command:
            self.command()

    def _paint(self) -> None:
        current = self.variable.get()
        for value, lbl in self.labels.items():
            on = value == current
            lbl.configure(bg=theme.ACCENT if on else theme.SURFACE,
                          fg="white" if on else theme.TEXT,
                          font=theme.font(10, "bold" if on else "normal"))


class StatCard(Card):
    def __init__(self, parent, label: str, value: str = "—", note: str = ""):
        super().__init__(parent, padding=(16, 12))
        ttk.Label(self, text=label.upper(), style="CardMuted.TLabel",
                  font=theme.font(8, "bold")).pack(anchor="w")
        self.value = ttk.Label(self, text=value, style="StatValue.TLabel")
        self.value.pack(anchor="w", pady=(4, 0))
        self.note = ttk.Label(self, text=note, style="CardMuted.TLabel", font=theme.font(9))
        self.note.pack(anchor="w")

    def set(self, value: str, note: str = "") -> None:
        self.value.configure(text=value)
        self.note.configure(text=note)


# ======================================================================
# DataTable
# ======================================================================
@dataclass
class Col:
    key: str
    heading: str
    width: int = 110
    anchor: str = "w"
    fmt: Callable[[Any], str] = fmt_default


MONEY = dict(anchor="e", fmt=fmt_money)
SIGNED = dict(anchor="e", fmt=fmt_signed)


class DataTable(ttk.Frame):
    """Treeview wrapper that takes a list of dicts, with sorting, zebra rows
    and an empty-state message."""

    def __init__(self, parent, columns: list[Col], height: int = 12,
                 on_select: Callable[[dict | None], None] | None = None,
                 on_activate: Callable[[dict], None] | None = None,
                 empty_text: str = "No records found."):
        super().__init__(parent, style="Bordered.TFrame", padding=1)
        self.columns = columns
        self.rows: list[dict] = []
        self._on_select = on_select
        self._on_activate = on_activate
        self._sort = (None, False)

        self.tree = ttk.Treeview(self, columns=[c.key for c in columns], show="headings",
                                 height=height, selectmode="browse")
        for c in columns:
            self.tree.heading(c.key, text=c.heading, anchor=c.anchor,
                              command=lambda k=c.key: self._sort_by(k))
            self.tree.column(c.key, width=c.width, anchor=c.anchor, stretch=True, minwidth=50)
        self.tree.tag_configure("alt", background=theme.ROW_ALT)
        self.tree.tag_configure("muted", foreground="#9095a6")

        ys = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ys.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.empty = tk.Label(self, text=empty_text, bg=theme.SURFACE, fg=theme.TEXT_MUTED,
                              font=theme.font(10))
        self.tree.bind("<<TreeviewSelect>>", self._selected)
        self.tree.bind("<Double-1>", self._activated)
        self.tree.bind("<Return>", self._activated)

    def set_rows(self, rows: list[dict] | None, muted: Callable[[dict], bool] | None = None):
        self.rows = list(rows or [])
        key, desc = self._sort
        if key:
            self.rows.sort(key=lambda r: _sort_key(r.get(key)), reverse=desc)
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(self.rows):
            tags = ["alt"] if i % 2 else []
            if muted and muted(row):
                tags.append("muted")
            self.tree.insert("", "end", iid=str(i), tags=tags,
                             values=[c.fmt(row.get(c.key)) for c in self.columns])
        if self.rows:
            self.empty.place_forget()
        else:
            self.empty.place(relx=0.5, rely=0.55, anchor="center")
        self._muted = muted
        if self._on_select:
            self._on_select(None)

    def selected(self) -> dict | None:
        sel = self.tree.selection()
        return self.rows[int(sel[0])] if sel else None

    def _selected(self, _e=None):
        if self._on_select:
            self._on_select(self.selected())

    def _activated(self, _e=None):
        row = self.selected()
        if row and self._on_activate:
            self._on_activate(row)

    def _sort_by(self, key: str):
        prev_key, desc = self._sort
        self._sort = (key, not desc if prev_key == key else False)
        for c in self.columns:
            arrow = ""
            if c.key == key:
                arrow = " ▼" if self._sort[1] else " ▲"
            self.tree.heading(c.key, text=c.heading + arrow)
        self.set_rows(self.rows, getattr(self, "_muted", None))


def _sort_key(v):
    if v is None:
        return (1, "")
    if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
        return (0, float(v))
    return (0, str(v).lower())


# ======================================================================
# Form dialog
# ======================================================================
@dataclass
class Field:
    name: str
    label: str
    kind: str = "entry"            # entry | password | combo | text | check | spin
    default: Any = ""
    options: list = field(default_factory=list)   # combo: [(value, label), ...] or [value, ...]
    parse: Callable[[str], Any] | None = None    # raises ValueError(msg)
    required: bool = True
    hint: str = ""
    readonly: bool = False
    width: int = 36


class FormDialog(tk.Toplevel):
    """Modal form. on_submit(values) runs the api call; if it raises AppError the
    message is shown inside the dialog and the user can fix the input."""

    def __init__(self, parent, title: str, fields: list[Field],
                 on_submit: Callable[[dict], Any], submit_text: str = "Save",
                 intro: str = ""):
        super().__init__(parent)
        self.withdraw()
        self.title(title)
        self.configure(bg=theme.SURFACE)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.result = None
        self._fields = fields
        self._on_submit = on_submit
        self._vars: dict[str, Any] = {}
        self._widgets: dict[str, tk.Widget] = {}

        body = ttk.Frame(self, style="Card.TFrame", padding=22)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text=title, style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2,
                                                                   sticky="w")
        r = 1
        if intro:
            ttk.Label(body, text=intro, style="CardMuted.TLabel", wraplength=380,
                      justify="left").grid(row=r, column=0, columnspan=2, sticky="w", pady=(4, 0))
            r += 1
        ttk.Frame(body, height=10, style="Card.TFrame").grid(row=r, column=0)
        r += 1

        first = None
        for f in fields:
            ttk.Label(body, text=f.label + ("" if f.required or f.kind == "check" else "  (optional)"),
                      style="Card.TLabel").grid(row=r, column=0, sticky="w", pady=(6, 2))
            r += 1
            w = self._build_widget(body, f)
            w.grid(row=r, column=0, columnspan=2, sticky="we")
            self._widgets[f.name] = w
            first = first or w
            r += 1
            if f.hint:
                ttk.Label(body, text=f.hint, style="Hint.TLabel").grid(row=r, column=0,
                                                                       columnspan=2, sticky="w")
                r += 1

        self.error = ttk.Label(body, text="", style="Error.TLabel", wraplength=380, justify="left")
        self.error.grid(row=r, column=0, columnspan=2, sticky="w", pady=(12, 0))
        r += 1
        btns = ttk.Frame(body, style="Card.TFrame")
        btns.grid(row=r, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="left", padx=(0, 8))
        self.submit_btn = ttk.Button(btns, text=submit_text, style="Primary.TButton",
                                     command=self._submit)
        self.submit_btn.pack(side="left")

        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Return>", self._on_return)
        _center(self, parent)
        self.deiconify()
        if first is not None:
            first.focus_set()
        _grab(self)

    # -- widgets ---------------------------------------------------------
    def _build_widget(self, parent, f: Field) -> tk.Widget:
        if f.kind == "check":
            var = tk.BooleanVar(value=bool(f.default))
            self._vars[f.name] = var
            return ttk.Checkbutton(parent, variable=var, text=f.hint or "", style="Card.TCheckbutton")
        if f.kind == "text":
            t = tk.Text(parent, width=f.width, height=4, wrap="word", relief="flat", bd=0,
                        highlightthickness=1, highlightbackground=theme.BORDER,
                        highlightcolor=theme.ACCENT, font=theme.font(10), padx=6, pady=4)
            if f.default:
                t.insert("1.0", str(f.default))
            self._vars[f.name] = t
            return t
        if f.kind == "combo":
            pairs = [o if isinstance(o, tuple) else (o, str(o)) for o in f.options]
            labels = [lbl for _v, lbl in pairs]
            var = tk.StringVar()
            default_label = next((lbl for v, lbl in pairs if v == f.default), "")
            var.set(default_label)
            cb = ttk.Combobox(parent, textvariable=var, values=labels, state="readonly",
                              width=f.width - 2)
            self._vars[f.name] = (var, dict((lbl, v) for v, lbl in pairs))
            return cb
        if f.kind == "spin":
            lo, hi = f.options or (1, 5)
            var = tk.StringVar(value=str(f.default or lo))
            self._vars[f.name] = var
            return ttk.Spinbox(parent, from_=lo, to=hi, textvariable=var, width=f.width - 2,
                               wrap=False)
        var = tk.StringVar(value="" if f.default is None else str(f.default))
        self._vars[f.name] = var
        e = ttk.Entry(parent, textvariable=var, width=f.width,
                      show="•" if f.kind == "password" else "")
        if f.readonly:
            e.state(["readonly"])
        return e

    def _raw(self, f: Field):
        v = self._vars[f.name]
        if f.kind == "check":
            return v.get()
        if f.kind == "text":
            return v.get("1.0", "end").strip()
        if f.kind == "combo":
            var, mapping = v
            return mapping.get(var.get())
        return v.get().strip() if f.kind != "password" else v.get()

    def values(self) -> dict:
        """Parse every field; raise ValueError with a readable message."""
        out = {}
        for f in self._fields:
            raw = self._raw(f)
            if f.kind == "check":
                out[f.name] = bool(raw)
                continue
            if raw in (None, ""):
                if f.required:
                    raise ValueError(f"{f.label} is required.")
                out[f.name] = None
                continue
            if f.parse and f.kind != "combo":
                try:
                    out[f.name] = f.parse(raw)
                except ValueError as exc:
                    raise ValueError(f"{f.label}: {exc}.") from None
            else:
                out[f.name] = raw
        return out

    def _on_return(self, event):
        if isinstance(event.widget, tk.Text):
            return
        self._submit()

    def _submit(self):
        self.error.configure(text="")
        try:
            values = self.values()
            self.result = self._on_submit(values)
        except ValueError as exc:
            self.error.configure(text=str(exc))
            return
        except AppError as exc:
            self.error.configure(text=str(exc))
            return
        except Exception as exc:       # never a stack trace
            self.error.configure(text=f"Something went wrong: {exc}")
            return
        self.destroy()


# ======================================================================
# Read-only dialogs
# ======================================================================
class DetailsDialog(tk.Toplevel):
    """Key/value card. `rows` = list of (label, value_str)."""

    def __init__(self, parent, title: str, rows: list[tuple[str, str]], subtitle: str = ""):
        super().__init__(parent)
        self.withdraw()
        self.title(title)
        self.configure(bg=theme.SURFACE)
        self.transient(parent.winfo_toplevel())
        body = ttk.Frame(self, style="Card.TFrame", padding=22)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text=title, style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2,
                                                                   sticky="w")
        if subtitle:
            ttk.Label(body, text=subtitle, style="CardMuted.TLabel").grid(row=1, column=0,
                                                                          columnspan=2, sticky="w")
        for i, (label, value) in enumerate(rows, start=2):
            ttk.Label(body, text=label, style="CardMuted.TLabel").grid(row=i, column=0, sticky="nw",
                                                                       pady=3, padx=(0, 24))
            ttk.Label(body, text=value, style="Card.TLabel", wraplength=320,
                      justify="left").grid(row=i, column=1, sticky="w", pady=3)
        ttk.Button(body, text="Close", command=self.destroy).grid(row=len(rows) + 2, column=1,
                                                                  sticky="e", pady=(16, 0))
        self.bind("<Escape>", lambda _e: self.destroy())
        _center(self, parent)
        self.deiconify()
        _grab(self)


class TableDialog(tk.Toplevel):
    def __init__(self, parent, title: str, columns: list[Col], rows: list[dict],
                 subtitle: str = "", width: int = 760, height: int = 10):
        super().__init__(parent)
        self.withdraw()
        self.title(title)
        self.configure(bg=theme.BG)
        self.transient(parent.winfo_toplevel())
        body = ttk.Frame(self, padding=20)
        body.pack(fill="both", expand=True)
        PageHeader(body, title, subtitle).pack(fill="x", pady=(0, 12))
        table = DataTable(body, columns, height=height)
        table.pack(fill="both", expand=True)
        table.set_rows(rows)
        ttk.Button(body, text="Close", command=self.destroy).pack(anchor="e", pady=(12, 0))
        self.geometry(f"{width}x{min(160 + height * 28 + 60, 640)}")
        self.bind("<Escape>", lambda _e: self.destroy())
        _center(self, parent)
        self.deiconify()
        _grab(self)


def ask_value(parent, title: str, label: str, parse: Callable, default: str = "",
              hint: str = "", submit_text: str = "OK"):
    """Small one-field prompt. Returns the parsed value or None if cancelled."""
    holder = {}

    def submit(values):
        holder["v"] = values["v"]

    dlg = FormDialog(parent, title, [Field("v", label, default=default, parse=parse, hint=hint)],
                     submit, submit_text=submit_text)
    parent.wait_window(dlg)
    return holder.get("v")


# ======================================================================
# helpers
# ======================================================================
def _center(win: tk.Toplevel, parent: tk.Misc) -> None:
    win.update_idletasks()
    top = parent.winfo_toplevel()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    try:
        geo = win.geometry().split("+")[0]
        gw, gh = (int(x) for x in geo.split("x"))
        if gw > 1 and gh > 1:
            w, h = max(w, gw), max(h, gh)
    except ValueError:
        pass
    x = top.winfo_rootx() + (top.winfo_width() - w) // 2
    y = top.winfo_rooty() + (top.winfo_height() - h) // 3
    win.geometry(f"+{max(x, 0)}+{max(y, 0)}")


def _grab(win: tk.Toplevel) -> None:
    try:
        win.wait_visibility()
        win.grab_set()
    except tk.TclError:
        pass
