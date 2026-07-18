import os
import requests
from datetime import datetime


class FacebookPoster:
    """
    Posts to Facebook Page.
    Uses Graph API v18.0.
    Handles token expiry warnings.
    Includes detailed error reporting.
    """

    GRAPH           = "https://graph.facebook.com/v18.0"
    TOKEN_WARN_DAYS = 7

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
        """Post text message to Facebook page."""

        if not self.token:
            print("❌ Facebook: No token configured")
            return False

        if not self.page_id:
            print("❌ Facebook: No page ID configured")
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
                pid = r.json().get("id", "unknown")
                print(
                    f"✅ Facebook: Posted successfully "
                    f"(id: {pid})"
                )
                return True

            else:
                error  = r.json().get("error", {})
                code   = error.get("code", "?")
                msg    = error.get("message", r.text[:200])
                subcode = error.get("error_subcode", "")

                print(f"❌ Facebook post failed:")
                print(f"   Code: {code}")
                print(f"   Message: {msg}")

                if code == 200 or code == 190:
                    print(
                        "   FIX: Token needs refreshing."
                        " Go to developers.facebook.com"
                        " and generate new page token."
                    )
                elif code == 100:
                    print(
                        "   FIX: Permission missing."
                        " Token needs pages_manage_posts"
                        " permission."
                    )
                elif code == 368:
                    print(
                        "   FIX: Account temporarily"
                        " restricted."
                    )

                return False

        except requests.Timeout:
            print("❌ Facebook: Request timed out")
            return False
        except Exception as e:
            print(f"❌ Facebook error: {e}")
            return False

    def test_connection(self) -> bool:
        """Test page connection without posting."""
        try:
            r = requests.get(
                f"{self.GRAPH}/{self.page_id}",
                params={
                    "fields":       "name,fan_count,category",
                    "access_token": self.token,
                },
                timeout=15,
            )

            if r.status_code == 200:
                data = r.json()
                print(
                    f"✅ Facebook connected: "
                    f"{data.get('name')}"
                )
                print(
                    f"   Followers: "
                    f"{data.get('fan_count', 0):,}"
                )
                return True
            else:
                err = r.json().get("error", {})
                print(
                    f"❌ Facebook connection failed: "
                    f"{err.get('message', 'unknown')}"
                )
                return False

        except Exception as e:
            print(f"❌ Facebook connection error: {e}")
            return False

    def validate_token(self) -> dict:
        """
        Check token validity and permissions.
        Returns dict with status info.
        """
        result = {
            "valid":       False,
            "expires_in":  -1,
            "permissions": [],
            "error":       "",
        }

        try:
            r = requests.get(
                f"{self.GRAPH}/debug_token",
                params={
                    "input_token":  self.token,
                    "access_token": self.token,
                },
                timeout=15,
            )

            if r.status_code == 200:
                data    = r.json().get("data", {})
                is_valid = data.get("is_valid", False)
                expires  = data.get("expires_at", 0)
                scopes   = data.get("scopes", [])

                result["valid"]       = is_valid
                result["permissions"] = scopes

                if expires and expires > 0:
                    exp_dt = datetime.fromtimestamp(expires)
                    days   = (exp_dt - datetime.now()).days
                    result["expires_in"] = days
                else:
                    result["expires_in"] = 999

            return result

        except Exception as e:
            result["error"] = str(e)
            return result

    def days_until_expiry(self) -> int:
        """Estimate days until token expires."""
        if not self.token_date:
            return -1
        try:
            created  = datetime.fromisoformat(self.token_date)
            now      = datetime.now()
            age_days = (now - created).days
            return max(0, 60 - age_days)
        except Exception:
            return -1

    def token_warning(self) -> str:
        """Return warning if token expires soon."""
        days = self.days_until_expiry()
        if days == -1:
            return ""
        if days <= self.TOKEN_WARN_DAYS:
            return (
                f"⚠️ Facebook token expires in {days} "
                f"days. Please refresh at: "
                f"developers.facebook.com"
            )
        return ""
