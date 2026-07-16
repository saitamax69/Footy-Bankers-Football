import os
import requests
from datetime import datetime, timezone


class FacebookPoster:
    """
    Posts to Facebook Page.
    Uses Graph API free tier.
    Monitors token age.
    """

    GRAPH = "https://graph.facebook.com/v18.0"
    TOKEN_WARN_DAYS = 7

    def __init__(self):
        self.token   = os.environ.get(
            "FACEBOOK_PAGE_TOKEN", ""
        )
        self.page_id = os.environ.get(
            "FACEBOOK_PAGE_ID", ""
        )
        self.token_date = os.environ.get(
            "FACEBOOK_TOKEN_DATE", ""
        )

    def post(self, text: str) -> bool:
        """Post text to Facebook page."""
        try:
            r = requests.post(
                f"{self.GRAPH}/{self.page_id}/feed",
                data={
                    "message":      text,
                    "access_token": self.token,
                },
                timeout=30,
            )

            if r.status_code == 200:
                pid = r.json().get("id", "")
                print(f"✅ Facebook: posted (id:{pid})")
                return True
            else:
                err = r.json().get("error", {})
                print(
                    f"❌ Facebook failed: "
                    f"{err.get('message', r.text)}"
                )
                return False

        except Exception as e:
            print(f"❌ Facebook error: {e}")
            return False

    def days_until_expiry(self) -> int:
        """
        Estimate days until token expires.
        Returns -1 if unknown.
        """
        if not self.token_date:
            return -1
        try:
            created = datetime.fromisoformat(
                self.token_date
            )
            now = datetime.now()
            age = (now - created).days
            return max(0, 60 - age)
        except Exception:
            return -1

    def token_warning(self) -> str:
        """
        Return warning message if
        token expires soon.
        """
        days = self.days_until_expiry()
        if days == -1:
            return ""
        if days <= self.TOKEN_WARN_DAYS:
            return (
                f"⚠️ Facebook token expires "
                f"in {days} days. "
                f"Please refresh at: "
                f"developers.facebook.com"
            )
        return ""
