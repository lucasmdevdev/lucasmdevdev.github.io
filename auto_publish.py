#!/usr/bin/env python3
"""
Auto-publish pipeline — prend un article de la queue et le publie sur GitHub Pages
Met à jour l'index.html automatiquement et le sitemap.xml
"""

import os
import re
import sys
import subprocess
import datetime
from pathlib import Path
from html.parser import HTMLParser

BLOG_DIR = Path("/home/sax/projects/blog")
QUEUE_DIR = Path("/home/sax/projects/content-engine/queue")
PUBLISHED_DIR = QUEUE_DIR / "published"
LOG_FILE = BLOG_DIR / "publish.log"
GH_BIN = Path("/home/sax/bin/gh")


def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


class ArticleMetaParser(HTMLParser):
    """Extrait title, description, date, tags depuis le <head> d'un article HTML."""
    def __init__(self):
        super().__init__()
        self.meta = {"title": "", "description": "", "date": "", "tags": []}
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attrs_dict.get("name", "")
            content = attrs_dict.get("content", "")
            if name == "description":
                self.meta["description"] = content
            elif name == "date":
                self.meta["date"] = content
            elif name == "tags":
                self.meta["tags"] = [t.strip() for t in content.split(",")]

    def handle_data(self, data):
        if self._in_title:
            self.meta["title"] = data.strip()
            self._in_title = False

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False


def get_article_intro(html_content):
    """Extrait le premier <p> dans article-intro ou le premier <p> du contenu."""
    match = re.search(r'class="article-intro"[^>]*>(.*?)</p>', html_content, re.DOTALL)
    if match:
        text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        return text[:200] + "..." if len(text) > 200 else text
    # Fallback: premier <p> dans l'article
    match = re.search(r'<article[^>]*>.*?<p>(.*?)</p>', html_content, re.DOTALL)
    if match:
        text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        return text[:200] + "..." if len(text) > 200 else text
    return ""


def format_date_fr(date_str):
    """Convertit 2026-03-29 en '29 mars 2026'."""
    months = {
        "01": "janvier", "02": "février", "03": "mars", "04": "avril",
        "05": "mai", "06": "juin", "07": "juillet", "08": "août",
        "09": "septembre", "10": "octobre", "11": "novembre", "12": "décembre"
    }
    try:
        parts = date_str.split("-")
        return f"{int(parts[2])} {months[parts[1]]} {parts[0]}"
    except Exception:
        return date_str


def build_card_html(filename, meta, intro):
    """Génère le HTML d'une card pour l'index."""
    date_fr = format_date_fr(meta["date"])
    tags_html = "".join(f"          <span>{t}</span>\n" for t in meta["tags"][:2])
    return f"""
      <a class="card" href="{filename}">
        <div class="card-meta">
{tags_html}          {date_fr}
        </div>
        <h2>{meta['title']}</h2>
        <p>{intro}</p>
        <span class="card-arrow">Lire l'article →</span>
      </a>
"""


def insert_card_in_index(card_html):
    """Insère la card en tête de la grille dans index.html."""
    index_path = BLOG_DIR / "index.html"
    with open(index_path, "r") as f:
        content = f.read()

    marker = '<div class="articles-grid">'
    if marker not in content:
        log("ERREUR: marqueur articles-grid non trouvé dans index.html")
        return False

    new_content = content.replace(marker, marker + "\n" + card_html, 1)
    with open(index_path, "w") as f:
        f.write(new_content)
    return True


def update_sitemap(filename, date_str):
    """Ajoute l'URL de l'article au sitemap.xml."""
    sitemap_path = BLOG_DIR / "sitemap.xml"
    if not sitemap_path.exists():
        return
    with open(sitemap_path, "r") as f:
        content = f.read()

    url = f"https://lucasmdevdev.github.io/{filename}"
    if url in content:
        return  # Déjà présent

    new_entry = f"""  <url>
    <loc>{url}</loc>
    <lastmod>{date_str}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
"""
    content = content.replace("</urlset>", new_entry + "</urlset>")
    with open(sitemap_path, "w") as f:
        f.write(content)


def get_gh_token():
    result = subprocess.run(
        [str(GH_BIN), "auth", "token"],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def git_push(files_added, commit_message):
    token = get_gh_token()
    if not token:
        log("ERREUR: impossible d'obtenir le token GitHub")
        return False

    # Set remote URL with token
    subprocess.run(
        ["git", "remote", "set-url", "origin",
         f"https://lucasmdevdev:{token}@github.com/lucasmdevdev/lucasmdevdev.github.io.git"],
        cwd=BLOG_DIR, capture_output=True
    )

    # Git add
    for f in files_added:
        subprocess.run(["git", "add", f], cwd=BLOG_DIR)

    # Git commit
    result = subprocess.run(
        ["git", "commit", "-m", commit_message],
        cwd=BLOG_DIR, capture_output=True, text=True
    )
    if result.returncode != 0:
        log(f"Erreur git commit: {result.stderr}")
        return False

    # Git push
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=BLOG_DIR, capture_output=True, text=True
    )
    if result.returncode != 0:
        log(f"Erreur git push: {result.stderr}")
        return False

    return True


def main():
    log("=== Auto-publish démarré ===")

    # Lister les articles en queue
    pending = sorted(QUEUE_DIR.glob("*.html"))
    if not pending:
        log("Aucun article en attente dans la queue")
        return 0

    log(f"{len(pending)} article(s) en attente")

    # Prendre le premier
    article_path = pending[0]
    filename = article_path.name
    log(f"Publication de: {filename}")

    # Lire le contenu
    with open(article_path, "r") as f:
        html_content = f.read()

    # Parser les métadonnées
    parser = ArticleMetaParser()
    parser.feed(html_content)
    meta = parser.meta

    if not meta["title"]:
        log("ERREUR: impossible d'extraire le titre de l'article")
        return 1

    log(f"Titre: {meta['title']}")
    log(f"Date: {meta['date']}, Tags: {meta['tags']}")

    # Extraire l'intro
    intro = get_article_intro(html_content)

    # Copier l'article vers le blog
    dest = BLOG_DIR / filename
    with open(dest, "w") as f:
        f.write(html_content)
    log(f"Article copié vers {dest}")

    # Mettre à jour l'index
    card_html = build_card_html(filename, meta, intro)
    if insert_card_in_index(card_html):
        log("Index.html mis à jour")
    else:
        log("AVERTISSEMENT: index.html non mis à jour")

    # Mettre à jour le sitemap
    date_str = meta["date"] if meta["date"] else datetime.date.today().isoformat()
    update_sitemap(filename, date_str)
    log("Sitemap mis à jour")

    # Git push
    files_to_add = [filename, "index.html", "sitemap.xml"]
    commit_msg = f"Auto-publish: {meta['title'][:60]}"
    if git_push(files_to_add, commit_msg):
        log(f"SUCCÈS: {filename} publié sur GitHub Pages")
    else:
        log("ERREUR: git push échoué")
        return 1

    # Déplacer l'article vers published/
    PUBLISHED_DIR.mkdir(exist_ok=True)
    article_path.rename(PUBLISHED_DIR / filename)
    log(f"Article déplacé vers queue/published/")

    # Status update
    time_str = datetime.datetime.now().strftime("%H:%M")
    title_short = meta["title"][:50]
    subprocess.run(
        ["bash", "-c", f'echo "[{time_str}] Article publié: {filename} — {title_short}" >> ~/comms/status.txt']
    )

    log("=== Auto-publish terminé ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
