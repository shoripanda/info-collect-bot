from datetime import datetime, timezone, timedelta
import time
import feedparser

from config import RSS_URLS, KEYWORDS, MAX_ARTICLE_AGE_HOURS
from storage import load_seen, save_seen
from notifier import send_discord_message


# GitHub Actions用：1回だけ実行して終了する
# Macで常時監視したい場合は True にする
RUN_FOREVER = False

# RUN_FOREVER = True の場合だけ使う
CHECK_INTERVAL_SECONDS = 60


def is_relevant(title: str, summary: str) -> bool:
    """
    KEYWORDSが空ならすべて対象。
    KEYWORDSに単語が入っている場合は、title/summaryに含まれる記事だけ対象。
    """
    if not KEYWORDS:
        return True

    text = f"{title} {summary}".lower()

    for keyword in KEYWORDS:
        if keyword.lower() in text:
            return True

    return False


def get_entry_datetime(entry):
    """
    RSS記事の公開日時を取得する。
    Google News RSSでは published_parsed が入っていることが多い。
    取れない場合は None を返す。
    """
    date_struct = entry.get("published_parsed") or entry.get("updated_parsed")

    if not date_struct:
        return None

    return datetime(*date_struct[:6], tzinfo=timezone.utc)


def is_recent(entry) -> bool:
    """
    MAX_ARTICLE_AGE_HOURS時間以内の記事だけTrue。
    日時が取れない記事は除外する。
    """
    entry_datetime = get_entry_datetime(entry)

    if entry_datetime is None:
        return False

    now = datetime.now(timezone.utc)
    limit = now - timedelta(hours=MAX_ARTICLE_AGE_HOURS)

    return entry_datetime >= limit


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

            # すでに送信済みならスキップ
            if item_id in seen:
                continue

            # 1週間以内など、指定期間外の記事はスキップ
            if not is_recent(entry):
                print(f"Skipped old/no-date article: {title}")
                new_seen.add(item_id)
                continue

            # キーワードに合わない記事はスキップ
            if not is_relevant(title, summary):
                print(f"Skipped irrelevant article: {title}")
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


def run_once():
    new_items, new_seen = collect_from_rss()

    if not new_items:
        print("No new recent items.")
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
    print(f"Sent {len(new_items)} new recent item(s).")


def main():
    if RUN_FOREVER:
        print("Info Collect Bot started.")
        print(f"Checking every {CHECK_INTERVAL_SECONDS} seconds.")
        while True:
            try:
                run_once()
            except Exception as error:
                print(f"Error: {error}")

            print(f"Sleeping {CHECK_INTERVAL_SECONDS} seconds...")
            time.sleep(CHECK_INTERVAL_SECONDS)
    else:
        run_once()


if __name__ == "__main__":
    main()
