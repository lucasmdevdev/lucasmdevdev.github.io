#!/usr/bin/env python3
"""
Génère un flux RSS pour le blog LucasMdev à partir de l'index.html.
À lancer après chaque publication d'article.
"""

import re
import datetime
from pathlib import Path
from html.parser import HTMLParser

BLOG_DIR = Path("/home/sax/projects/blog")
BASE_URL = "https://lucasmdevdev.github.io"


class IndexParser(HTMLParser):
    """Extrait les cards de l'index.html."""
    def __init__(self):
        super().__init__()
        self.articles = []
        self._in_card = False
        self._in_h2 = False
        self._in_p = False
        self._in_meta = False
        self._in_date = False
        self._current = {}
        self._card_href = None
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "a" and "card" in attrs_dict.get("class", ""):
            self._in_card = True
            self._current = {"href": attrs_dict.get("href", ""), "title": "", "desc": "", "date": "", "tags": []}
            return
        if self._in_card:
            if tag == "h2":
                self._in_h2 = True
            elif tag == "p" and not self._in_h2:
                self._in_p = True
            elif tag == "span" and not self._in_date:
                self._last_tag = "span"

    def handle_data(self, data):
        if not self._in_card:
            return
        data = data.strip()
        if not data:
            return
        if self._in_h2:
            self._current["title"] += data
        elif self._in_p:
            self._current["desc"] += data
        else:
            # Chercher la date dans le texte (format "28 mars 2026")
            if re.match(r'\d+ \w+ 20\d\d', data):
                self._current["date"] = data
            elif data and not self._current.get("tags_done"):
                if len(data) > 2 and not data.startswith("→"):
                    if len(self._current["tags"]) < 2:
                        self._current["tags"].append(data)

    def handle_endtag(self, tag):
        if not self._in_card:
            return
        if tag == "h2":
            self._in_h2 = False
        elif tag == "p":
            self._in_p = False
        elif tag == "a" and self._in_card:
            if self._current.get("title"):
                self.articles.append(self._current)
            self._in_card = False
            self._current = {}


def date_to_rfc822(date_fr: str) -> str:
    """Convertit '28 mars 2026' en RFC 822 pour RSS."""
    months = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
    }
    try:
        parts = date_fr.split()
        day = int(parts[0])
        month = months.get(parts[1].lower(), 1)
        year = int(parts[2])
        dt = datetime.datetime(year, month, day, 9, 0, 0)
        # RFC 822 format
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        months_abbr = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return f"{days[dt.weekday()]}, {day:02d} {months_abbr[month-1]} {year} 09:00:00 +0200"
    except Exception:
        return datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0200")


def gen_rss(articles):
    now = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0200")
    items = []
    for a in articles:
        url = f"{BASE_URL}/{a['href']}"
        title = a["title"]
        desc = a["desc"][:300] + "..." if len(a["desc"]) > 300 else a["desc"]
        pub_date = date_to_rfc822(a["date"]) if a["date"] else now
        cats = "".join(f"    <category>{t}</category>\n" for t in a["tags"])
        items.append(f"""  <item>
    <title><![CDATA[{title}]]></title>
    <link>{url}</link>
    <guid isPermaLink="true">{url}</guid>
    <description><![CDATA[{desc}]]></description>
    <pubDate>{pub_date}</pubDate>
{cats}  </item>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>LucasMdev — IA, Automatisation &amp; Productivité</title>
    <link>{BASE_URL}</link>
    <description>Guides pratiques sur l'IA, l'automatisation no-code et la productivité tech. Testez les meilleurs outils avant de payer.</description>
    <language>fr</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{BASE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>{BASE_URL}/favicon.ico</url>
      <title>LucasMdev</title>
      <link>{BASE_URL}</link>
    </image>
{chr(10).join(items)}
  </channel>
</rss>"""


if __name__ == "__main__":
    index_path = BLOG_DIR / "index.html"
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    parser = IndexParser()
    parser.feed(content)
    articles = parser.articles

    print(f"{len(articles)} articles trouvés dans l'index")

    rss = gen_rss(articles)
    out_path = BLOG_DIR / "feed.xml"
    out_path.write_text(rss, encoding="utf-8")
    print(f"RSS généré : {out_path}")
    print(f"URL : {BASE_URL}/feed.xml")
