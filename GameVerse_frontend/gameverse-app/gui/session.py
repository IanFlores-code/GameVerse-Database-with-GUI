"""Who is logged in. Views use this to decide what to show."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Session:
    role: str                  # "admin" or "player"
    display_name: str
    playerid: int | None = None
    username: str | None = None

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def actor(self) -> int | None:
        """playerid to pass to api calls (None for admins = no holder restriction)."""
        return None if self.is_admin else self.playerid

    @classmethod
    def from_login(cls, data: dict) -> "Session":
        return cls(role=data["role"], display_name=data.get("display_name", ""),
                   playerid=data.get("playerid"), username=data.get("username"))
