"""Colors, fonts and ttk styles for the whole application."""
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# ---- palette -----------------------------------------------------------
BG = "#f3f4f8"            # content background
SURFACE = "#ffffff"       # cards, tables
BORDER = "#dfe2ea"
TEXT = "#161823"
TEXT_MUTED = "#5d6275"
SIDEBAR = "#151826"
SIDEBAR_HOVER = "#232842"
SIDEBAR_ACTIVE = "#2e3557"
SIDEBAR_TEXT = "#c9cde0"
ACCENT = "#5b4fd6"        # primary buttons / highlights
ACCENT_HOVER = "#4a3fc0"
DANGER = "#c63b3b"
DANGER_HOVER = "#a92f2f"
SUCCESS = "#1a7f4b"
WARNING = "#a86a00"
ROW_ALT = "#f7f8fb"
SELECT = "#e4e1fb"

# chart series (validated categorical slots 1-2)
SERIES_1 = "#2a78d6"      # money in (top-ups)
SERIES_2 = "#eb6834"      # money out (cashouts + purchases)

FONT_FAMILY = "TkDefaultFont"


def _pick_family(root: tk.Misc) -> str:
    available = set(tkfont.families(root))
    for fam in ("Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue", "Ubuntu",
                "Noto Sans", "DejaVu Sans", "Arial"):
        if fam in available:
            return fam
    return "TkDefaultFont"


def font(size: int = 10, weight: str = "normal") -> tuple:
    return (FONT_FAMILY, size, weight)


def apply(root: tk.Tk) -> None:
    """Configure fonts and every ttk style used by the views."""
    global FONT_FAMILY
    FONT_FAMILY = _pick_family(root)
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        tkfont.nametofont(name).configure(family=FONT_FAMILY, size=10)

    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG, foreground=TEXT, font=font(10),
                    bordercolor=BORDER, focuscolor=ACCENT)
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=SURFACE)                    # inner, no border
    style.configure("Bordered.TFrame", background=SURFACE, relief="solid", borderwidth=1)
    style.configure("Sidebar.TFrame", background=SIDEBAR)

    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Card.TLabel", background=SURFACE)
    style.configure("Muted.TLabel", foreground=TEXT_MUTED)
    style.configure("CardMuted.TLabel", background=SURFACE, foreground=TEXT_MUTED)
    style.configure("Title.TLabel", font=font(18, "bold"))
    style.configure("Subtitle.TLabel", foreground=TEXT_MUTED, font=font(10))
    style.configure("CardTitle.TLabel", background=SURFACE, font=font(12, "bold"))
    style.configure("StatValue.TLabel", background=SURFACE, font=font(18, "bold"))
    style.configure("Error.TLabel", foreground=DANGER, background=SURFACE)
    style.configure("Hint.TLabel", foreground=TEXT_MUTED, background=SURFACE, font=font(9))

    # buttons
    style.configure("TButton", padding=(12, 6), background=SURFACE, bordercolor=BORDER,
                    lightcolor=SURFACE, darkcolor=SURFACE)
    style.map("TButton", background=[("active", "#eceef4"), ("disabled", BG)],
              foreground=[("disabled", "#a3a7b6")])
    style.configure("Primary.TButton", background=ACCENT, foreground="white",
                    bordercolor=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT,
                    font=font(10, "bold"))
    style.map("Primary.TButton", background=[("active", ACCENT_HOVER), ("disabled", "#b9b4ee")],
              foreground=[("disabled", "white")])
    style.configure("Danger.TButton", background=SURFACE, foreground=DANGER, bordercolor="#ecc5c5")
    style.map("Danger.TButton", background=[("active", "#fbeaea")])
    style.configure("Link.TButton", background=SURFACE, foreground=ACCENT, borderwidth=0,
                    padding=(0, 2), lightcolor=SURFACE, darkcolor=SURFACE, bordercolor=SURFACE)
    style.map("Link.TButton", background=[("active", SURFACE)],
              foreground=[("active", ACCENT_HOVER)])

    # inputs
    for w in ("TEntry", "TCombobox", "TSpinbox"):
        style.configure(w, padding=5, fieldbackground=SURFACE, bordercolor=BORDER,
                        lightcolor=BORDER, darkcolor=BORDER)
        style.map(w, bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)])
    style.map("TCombobox", fieldbackground=[("readonly", SURFACE)])
    style.configure("TCheckbutton", background=BG)
    style.configure("Card.TCheckbutton", background=SURFACE)

    # tables
    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE,
                    rowheight=28, bordercolor=BORDER, borderwidth=0)
    style.map("Treeview", background=[("selected", SELECT)], foreground=[("selected", TEXT)])
    style.configure("Treeview.Heading", background="#eef0f5", foreground=TEXT_MUTED,
                    font=font(9, "bold"), padding=(8, 6), relief="flat", bordercolor=BORDER)
    style.map("Treeview.Heading", background=[("active", "#e3e6ef")])

    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(14, 6))
    style.configure("TLabelframe", background=SURFACE, bordercolor=BORDER)
    style.configure("TLabelframe.Label", background=SURFACE, foreground=TEXT_MUTED,
                    font=font(9, "bold"))
