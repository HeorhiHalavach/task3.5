from pathlib import Path 
import json
import re
import sqlite3

raw = Path("task1_d.json").read_text(encoding="utf-8")

json_text = re.sub(r'(?<=[{,])\s*:([a-z_]+)\s*=>', r'"\1":', raw)
books = json.loads(json_text)

with sqlite3.connect("books.db") as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            genre TEXT,
            publisher TEXT,
            year INTEGER,
            price TEXT
        )
    """)

    db.executemany("""
        INSERT OR REPLACE INTO books
        (id, title, author, genre, publisher, year, price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, [
        (
            str(book["id"]),
            book["title"],
            book["author"],
            book["genre"],
            book["publisher"],
            book["year"],
            book["price"],
        )
        for book in books
    ])

    count = db.execute("SELECT COUNT(*) FROM books").fetchone()[0]



with sqlite3.connect("books.db") as db:
    db.execute("DROP TABLE IF EXISTS yearly_summary")

    db.execute("""
        CREATE TABLE yearly_summary AS SELECT year AS publication_year,
            COUNT(*) AS book_count,
            ROUND(AVG(CASE substr(price, 1, 1) WHEN '€' THEN CAST(substr(price, 2) AS REAL) * 1.2
            WHEN '$' THEN CAST(substr(price, 2) AS REAL) END), 2) AS average_price_usd
        FROM books
        GROUP BY year
    """)

    rows = db.execute("""
        SELECT publication_year, book_count, average_price_usd FROM yearly_summary
        ORDER BY publication_year
    """).fetchall()



if sum(book_count for _, book_count, _ in rows) != count:
    raise ValueError("Yearly book counts do not match the books table")


lines = [
    f"Books: {count} rows",
    f"Yearly summary: {len(rows)} rows",
    "",
    "publication_year | book_count | average_price_usd",
]


for year, book_count, average in rows:
    lines.append(f"{year} | {book_count} | ${average:.2f}")

report = "\n".join(lines)
print(report)
Path("summary_for_email.txt").write_text(report, encoding="utf-8")

