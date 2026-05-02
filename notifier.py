import os
import time
import requests


DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("<b>", "")
    text = text.replace("</b>", "")
    text = text.replace("<br>", "\n")
    text = text.replace("<br/>", "\n")
    text = text.replace("&nbsp;", " ")

    return text.strip()


def send_discord_message(title: str, link: str, summary: str = "", source: str = ""):
    if not DISCORD_WEBHOOK_URL:
        raise ValueError("DISCORD_WEBHOOK_URL is not set.")

    title = clean_text(title)
    summary = clean_text(summary)

    if len(summary) > 400:
        summary = summary[:400] + "..."

    message = f"""
📰 **新着情報**

**タイトル**
{title}

**URL**
{link}

**概要**
{summary}

**情報源**
{source}
"""

    response = requests.post(
        DISCORD_WEBHOOK_URL,
        json={"content": message}
    )

    if response.status_code == 429:
        data = response.json()
        retry_after = data.get("retry_after", 1)
        print(f"Discord rate limited. Waiting {retry_after} seconds...")
        time.sleep(float(retry_after) + 1)

        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json={"content": message}
        )

    if response.status_code >= 400:
        raise Exception(
            f"Discord notification failed: {response.status_code} {response.text}"
        )

    time.sleep(1.5)
