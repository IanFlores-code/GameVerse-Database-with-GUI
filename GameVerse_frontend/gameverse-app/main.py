"""GameVerse Wallet Manager - entry point.

    python main.py

Reads DB settings from environment variables or .env (see .env.example),
tests the connection, then opens the login screen.
"""
from gui.app import GameVerseApp


def main() -> None:
    app = GameVerseApp()
    app.after(0, app.start)
    app.mainloop()


if __name__ == "__main__":
    main()
