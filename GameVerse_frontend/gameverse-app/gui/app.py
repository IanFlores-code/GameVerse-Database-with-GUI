"""Main window: tests the DB connection, then switches between login and the app shell."""
import tkinter as tk
from tkinter import messagebox

from . import api, theme
from .session import Session
from .views.login_view import LoginView
from .views.shell import Shell


class GameVerseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GameVerse · Wallet Manager")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        theme.apply(self)
        self._screen: tk.Widget | None = None
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Test the connection before showing anything (assignment Task 1)."""
        self.withdraw()
        while True:
            try:
                api.test_connection()
                break
            except api.AppError as exc:
                retry = messagebox.askretrycancel(
                    "Database connection", f"{exc}\n\nRetry the connection?", parent=self)
                if not retry:
                    self.destroy()
                    return
        self.deiconify()
        self.show_login()

    def _swap(self, widget: tk.Widget) -> None:
        if self._screen is not None:
            self._screen.destroy()
        self._screen = widget
        widget.pack(fill="both", expand=True)

    def show_login(self) -> None:
        self._swap(LoginView(self, on_login=self.show_shell))

    def show_shell(self, session: Session) -> None:
        self._swap(Shell(self, session, on_logout=self.show_login))
