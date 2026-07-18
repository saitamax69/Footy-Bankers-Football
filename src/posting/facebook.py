import os
import requests
from datetime import datetime


class FacebookPoster:
    """Posts to Facebook Page via Graph API."""

    GRAPH = "https://graph.facebook.com/v18.0"
    WARN_DAYS = 7

    def __init__(self):
        self.token      = os.environ.get(
            "FACEBOOK_PAGE_TOKEN", ""
        )
        self.page_id    = os.environ.get(
            "FACEBOOK_PAGE_ID", ""
        )
        self.token_date = os.environ.get(
            "FACEBOOK_TOKEN_DATE", ""
        )

    def post(self, text: str) -> bool:
        if not self.token or not self.page_id:
            print("❌ Facebook: Not configured")
            return False
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
                print(
                    f"✅ Facebook: Posted (id:{pid})"
                )
                return True
            else:
                err = r.json().get("error", {})
                print(
                    f"❌ Facebook failed: "
                    f"{err.get('message', r.text[:100])}"
                )
                return False
        except Exception as e:
            print(f"❌ Facebook error: {e}")
            return False

    def token_warning(self) -> str:
        if not self.token_date:
            return ""
        try:
            created  = datetime.fromisoformat(
                self.token_date
            )
            age_days = (datetime.now() - created).days
            days_left = max(0, 60 - age_days)
            if days_left <= self.WARN_DAYS:
                return (
                    f"⚠️ Facebook token expires "
                    f"in {days_left} days. "
                    f"Refresh at developers.facebook.com"
                )
        except Exception:
            pass
        return ""
