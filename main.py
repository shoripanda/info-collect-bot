import feedparser
from config import RSS_URLS, KEYWORDS
from storage import load_seen, save_seen
from notifier import send_discord_message


def is_relevant(title: str, summary: str) -> bool:
    """
    キーワードに一致する記事だけ通知する。
    KEYWORDSが空の場合は、すべての記事を通知する。
    """
    if not KEYWORDS:
        return True

    text = f"{title} {summary}".lower()

    for keyword in KEYWORDS:
        if keyword.lower() in text:
            return True

    return False


def collect_from_rss():
    seen = load_seen()
    new_seen = set(seen)

    new_items = []

    for rss_url in RSS_URLS:
        print(f"Checking RSS: {rss_url}")

        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            title = entry.get("title", "No title")
            link = entry.get("link", "")
            summary = entry.get("summary", "")

            item_id = link or title

            if item_id in seen:
                continue

            if not is_relevant(title, summary):
                new_seen.add(item_id)
                continue

            new_items.append({
                "title": title,
                "link": link,
                "summary": summary,
                "source": rss_url
            })

            new_seen.add(item_id)

    return new_items, new_seen


def main():
    new_items, new_seen = collect_from_rss()

    if not new_items:
        print("No new items.")
        save_seen(new_seen)
        return

    for item in new_items:
        send_discord_message(
            title=item["title"],
            link=item["link"],
            summary=item["summary"],
            source=item["source"]
        )

    save_seen(new_seen)

    print(f"Sent {len(new_items)} new item(s).")


if __name__ == "__main__":
    main()
