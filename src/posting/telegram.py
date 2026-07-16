import os
import asyncio
from telegram import Bot
from telegram.constants import ParseMode


class TelegramPoster:
    """
    Posts to Telegram channel.
    Handles message splitting.
    Falls back to plain text.
    """

    MAX_LEN = 4096

    def __init__(self):
        self.token = os.environ.get(
            "TELEGRAM_BOT_TOKEN", ""
        )
        self.channel = os.environ.get(
            "TELEGRAM_CHANNEL_ID", ""
        )
        self.bot = Bot(token=self.token)

    def post(self, text: str) -> bool:
        """Synchronous post wrapper."""
        return asyncio.run(self._post(text))

    async def _post(self, text: str) -> bool:
        parts = self._split(text)

        try:
            for i, part in enumerate(parts):
                await self.bot.send_message(
                    chat_id=self.channel,
                    text=part,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    disable_web_page_preview=True,
                )
                if i < len(parts) - 1:
                    await asyncio.sleep(1)

            print(
                f"✅ Telegram: posted "
                f"({len(parts)} part(s))"
            )
            return True

        except Exception as e:
            print(f"⚠️ Telegram markdown failed: {e}")
            return await self._post_plain(text)

    async def _post_plain(self, text: str) -> bool:
        """Fallback: strip markdown and post plain."""
        clean = self._strip_md(text)
        parts = self._split(clean)

        try:
            for part in parts:
                await self.bot.send_message(
                    chat_id=self.channel,
                    text=part,
                    disable_web_page_preview=True,
                )
            print("✅ Telegram: posted (plain fallback)")
            return True
        except Exception as e:
            print(f"❌ Telegram failed: {e}")
            return False

    def _split(self, text: str) -> list:
        if len(text) <= self.MAX_LEN:
            return [text]

        parts = []
        while len(text) > self.MAX_LEN:
            idx = text.rfind("\n", 0, self.MAX_LEN)
            if idx == -1:
                idx = self.MAX_LEN
            parts.append(text[:idx])
            text = text[idx:].lstrip("\n")

        if text:
            parts.append(text)
        return parts

    def _strip_md(self, text: str) -> str:
        for c in [
            "*", "_", "`", "\\",
            "[", "]", "~", "|",
        ]:
            text = text.replace(c, "")
        return text
