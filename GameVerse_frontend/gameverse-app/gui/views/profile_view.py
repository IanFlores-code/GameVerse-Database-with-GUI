"""Module 4 (player): view the personal profile and update phone / email."""
from tkinter import ttk

from .. import api, theme, validators
from ..widgets import Card, Field, FormDialog, fmt_active, fmt_default, info, safe_call
from .base import BaseView


class ProfileView(BaseView):
    title = "My profile"
    subtitle = "Your personal details. You can update your email and phone number."

    def __init__(self, parent, session):
        super().__init__(parent, session)
        self.card = Card(self, padding=24)
        self.card.pack(anchor="nw")
        self.values: dict[str, ttk.Label] = {}
        fields = [("name", "Name"), ("playerid", "Player ID"), ("email", "Email"),
                  ("phone", "Phone"), ("dateofbirth", "Date of birth"),
                  ("registrationdate", "Registered"), ("isactive", "Status")]
        for i, (key, label) in enumerate(fields):
            ttk.Label(self.card, text=label, style="CardMuted.TLabel").grid(
                row=i, column=0, sticky="w", pady=5, padx=(0, 40))
            self.values[key] = ttk.Label(self.card, text="", style="Card.TLabel",
                                         font=theme.font(11))
            self.values[key].grid(row=i, column=1, sticky="w", pady=5)
        ttk.Button(self.card, text="Edit contact details", style="Primary.TButton",
                   command=self._edit).grid(row=len(fields), column=0, columnspan=2, sticky="w",
                                            pady=(18, 0))
        self.player: dict | None = None

    def refresh(self):
        p = safe_call(self, api.get_player, self.session.playerid)
        if not p:
            return
        self.player = p
        shown = {"name": f"{p['firstname']} {p['lastname']}", "playerid": str(p["playerid"]),
                 "email": p["email"], "phone": p["phone"] or "—",
                 "dateofbirth": fmt_default(p["dateofbirth"]),
                 "registrationdate": fmt_default(p["registrationdate"]),
                 "isactive": fmt_active(p["isactive"])}
        for k, v in shown.items():
            self.values[k].configure(text=v)

    def _edit(self):
        p = self.player
        if not p:
            return
        fields = [Field("email", "Email", default=p["email"], parse=validators.email),
                  Field("phone", "Phone", default=p["phone"] or "", parse=validators.phone,
                        required=False)]

        def submit(v):
            api.update_player_contact(p["playerid"], v["email"], v["phone"])
            return True

        dlg = FormDialog(self, "Edit contact details", fields, submit,
                         intro="If you change your email, use the new one next time you sign in.")
        self.wait_window(dlg)
        if dlg.result:
            self.refresh()
            info(self, "Your contact details were updated.")
