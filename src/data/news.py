import feedparser
import requests
from datetime import datetime
import pytz
from config import RSS_FEEDS, INJURY_KEYWORDS, \
    POSITIVE_KEYWORDS


class NewsCollector:
    """
    Collects football news from RSS feeds
    and Google News.
    No API key needed.
    """

    def __init__(self):
        self.tz = pytz.timezone("Europe/London")
        self._cache = []

    def get_all_news(self) -> list:
        """Fetch from all RSS sources."""
        if self._cache:
            return self._cache

        all_news = []
        for source, url in RSS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:15]:
                    all_news.append({
                        "source":    source,
                        "title":     entry.get("title", ""),
                        "summary":   entry.get(
                            "summary", ""
                        ),
                        "published": entry.get(
                            "published", ""
                        ),
                        "link":      entry.get("link", ""),
                    })
            except Exception as e:
                print(f"RSS {source} failed: {e}")

        self._cache = all_news
        return all_news

    def get_team_news(
        self, team_name: str, all_news: list = None
    ) -> list:
        """Find news items relevant to team."""
        if all_news is None:
            all_news = self.get_all_news()

        team_lower = team_name.lower()
        matched = []

        for item in all_news:
            text = (
                item["title"] + " " + item["summary"]
            ).lower()
            if team_lower in text:
                has_injury = any(
                    k in text for k in INJURY_KEYWORDS
                )
                has_positive = any(
                    k in text for k in POSITIVE_KEYWORDS
                )
                item["has_injury"]  = has_injury
                item["has_positive"] = has_positive
                matched.append(item)

        return matched

    def get_google_news(self, team_name: str) -> list:
        """Search Google News RSS for team."""
        query = team_name.replace(" ", "+")
        url = (
            f"https://news.google.com/rss/search"
            f"?q={query}+football"
            f"&hl=en-GB&gl=GB&ceid=GB:en"
        )
        try:
            feed = feedparser.parse(url)
            return [
                {
                    "source":  "google_news",
                    "title":   e.get("title", ""),
                    "summary": e.get("summary", ""),
                    "link":    e.get("link", ""),
                }
                for e in feed.entries[:5]
            ]
        except Exception as e:
            print(f"Google News failed for {team_name}: {e}")
            return []

    def get_news_impact(
        self, team_name: str, all_news: list = None
    ) -> tuple:
        """
        Returns (score, note) for team news.
        Score negative = bad news.
        Score positive = good news.
        """
        team_news = self.get_team_news(
            team_name, all_news
        )
        google = self.get_google_news(team_name)
        combined = team_news + google

        if not combined:
            return 0, "No significant news"

        score = 0
        notes = []

        for item in combined:
            title = item.get("title", "")
            has_injury = item.get(
                "has_injury",
                any(
                    k in title.lower()
                    for k in INJURY_KEYWORDS
                ),
            )
            has_positive = item.get(
                "has_positive",
                any(
                    k in title.lower()
                    for k in POSITIVE_KEYWORDS
                ),
            )

            if has_injury:
                score -= 5
                notes.append(f"⚠️ {title[:70]}")
            if has_positive:
                score += 3
                notes.append(f"✅ {title[:70]}")

        score = max(-15, min(15, score))
        note = notes[0] if notes else "Normal team news"
        return score, note

    def get_top_stories(self) -> list:
        """Get top football stories for media posts."""
        all_news = self.get_all_news()
        return all_news[:10]

    def detect_tragedy(self) -> bool:
        """
        Detect if a tragedy happened today.
        If yes, suppress opinion content.
        """
        tragedy_words = [
            "died", "death", "passed away",
            "fatal", "tragedy", "RIP",
            "collapsed", "serious injury",
            "critical condition",
        ]
        all_news = self.get_all_news()
        for item in all_news:
            text = (
                item["title"] + " " + item["summary"]
            ).lower()
            if any(w.lower() in text for w in tragedy_words):
                return True
        return False
