import requests
import argparse
import sqlite3
import json
import os
import pandas as pd


API_KEY = "...."  
BASE_URL = "https://newsapi.org/v2/top-headlines"
DATA_DIR = "data"
DB_PATH = os.path.join(DATA_DIR, "news.db")
JSON_PATH = os.path.join(DATA_DIR, "news.json")

os.makedirs(DATA_DIR, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            source TEXT,
            url TEXT,
            published TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_articles(articles):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for a in articles:
        try:
            cur.execute(
                "INSERT INTO news (title, source, url, published) VALUES (?, ?, ?, ?)",
                (a["title"], a["source"], a["url"], a["published"])
            )
        except sqlite3.IntegrityError:
            pass  
    conn.commit()
    conn.close()

def fetch_all():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT title, source, url, published FROM news")
    data = cur.fetchall()
    conn.close()
    return data


def fetch_news(source=None, keyword=None, date=None):
    params = {
        "apiKey": API_KEY,
        "language": "en",
        "pageSize": 100
    }
    if source:
        params["sources"] = source
    if keyword:
        params["q"] = keyword
    if date:
        params["from"] = date

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    articles = []
    for a in data.get("articles", []):
        articles.append({
            "title": a["title"],
            "source": a["source"]["name"],
            "url": a["url"],
            "published": a["publishedAt"][:10]
        })
    return articles


def export_csv(data):
    df = pd.DataFrame(data, columns=["Title", "Source", "URL", "Date"])
    df.to_csv(os.path.join(DATA_DIR, "news.csv"), index=False)

def export_excel(data):
    df = pd.DataFrame(data, columns=["Title", "Source", "URL", "Date"])
    df.to_excel(os.path.join(DATA_DIR, "news.xlsx"), index=False)


def main():
    parser = argparse.ArgumentParser(description="News Aggregator CLI")
    parser.add_argument("--source", help="News source (example: bbc-news)")
    parser.add_argument("--keyword", help="Keyword filter")
    parser.add_argument("--date", help="Date YYYY-MM-DD")
    parser.add_argument("--export", choices=["csv", "excel"])
    args = parser.parse_args()

    init_db()

    print("Fetching news...")
    articles = fetch_news(args.source, args.keyword, args.date)

    insert_articles(articles)

  
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2)

    data = fetch_all()

    if args.export == "csv":
        export_csv(data)
        print("Exported to CSV")
    elif args.export == "excel":
        export_excel(data)
        print("Exported to Excel")

    print(f"Total unique articles stored: {len(data)}")

if __name__ == "__main__":
    main()
