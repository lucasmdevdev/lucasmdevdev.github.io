#!/usr/bin/env python3
"""
Ajoute les métadonnées Schema.org (JSON-LD) à chaque article du blog.
Permet à Google d'afficher des rich snippets (date, auteur, etc.)
"""

import re
import json
import subprocess
from pathlib import Path
from html.parser import HTMLParser

BLOG_DIR = Path("/home/sax/projects/blog")
BASE_URL = "https://lucasmdevdev.github.io"
AUTHOR = "Lucas M."
ORG = "LucasMdev"


class ArticleMetaExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {
            "title": "", "description": "", "date": "", "tags": [], "canonical": ""
        }
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attrs_dict.get("name", "")
            prop = attrs_dict.get("property", "")
            content = attrs_dict.get("content", "")
            if name == "description":
                self.meta["description"] = content
            elif name == "date":
                self.meta["date"] = content
            elif name == "tags":
                self.meta["tags"] = [t.strip() for t in content.split(",")]
        elif tag == "link":
            if attrs_dict.get("rel") == "canonical":
                self.meta["canonical"] = attrs_dict.get("href", "")

    def handle_data(self, data):
        if self._in_title:
            t = data.strip()
            for suffix in [" — LucasMdev", " - LucasMdev"]:
                if t.endswith(suffix):
                    t = t[:-len(suffix)]
            self.meta["title"] = t
            self._in_title = False

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False


SCHEMA_MARKER = "<!-- schema-org -->"


def build_schema_json(slug, meta):
    """Génère le JSON-LD Schema.org pour un article."""
    url = meta.get("canonical") or f"{BASE_URL}/{slug}.html"
    date_published = meta.get("date", "2026-03-28")
    date_modified = date_published

    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta["title"],
        "description": meta["description"],
        "author": {
            "@type": "Person",
            "name": AUTHOR
        },
        "publisher": {
            "@type": "Organization",
            "name": ORG,
            "url": BASE_URL
        },
        "url": url,
        "datePublished": date_published,
        "dateModified": date_modified,
        "inLanguage": "fr-FR",
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": url
        }
    }

    if meta.get("tags"):
        schema["keywords"] = ", ".join(meta["tags"])

    return json.dumps(schema, ensure_ascii=False, indent=2)


def add_schema_to_article(path):
    slug = path.stem
    content = path.read_text(encoding="utf-8")

    if SCHEMA_MARKER in content:
        print(f"  ↩️  {slug}: déjà traité")
        return False

    # Extraire les métadonnées
    parser = ArticleMetaExtractor()
    parser.feed(content)
    meta = parser.meta

    if not meta["title"]:
        print(f"  ⚠️  {slug}: pas de titre trouvé, skip")
        return False

    schema_json = build_schema_json(slug, meta)
    schema_block = f"""<!-- schema-org -->
<script type="application/ld+json">
{schema_json}
</script>"""

    # Insérer juste avant </head>
    if "</head>" not in content:
        print(f"  ❌ {slug}: pas de </head>")
        return False

    new_content = content.replace("</head>", schema_block + "\n</head>", 1)
    path.write_text(new_content, encoding="utf-8")
    print(f"  ✅ {slug}")
    return True


def git_push_all():
    token_result = subprocess.run(
        ["/home/sax/bin/gh", "auth", "token"],
        capture_output=True, text=True
    )
    token = token_result.stdout.strip()
    if not token:
        print("❌ Pas de token")
        return

    subprocess.run(
        ["git", "remote", "set-url", "origin",
         f"https://lucasmdevdev:{token}@github.com/lucasmdevdev/lucasmdevdev.github.io.git"],
        cwd=BLOG_DIR, capture_output=True
    )
    subprocess.run(["git", "add", "-A"], cwd=BLOG_DIR)
    result = subprocess.run(
        ["git", "commit", "-m", "SEO: ajout Schema.org (JSON-LD) Article sur tous les articles"],
        cwd=BLOG_DIR, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Commit: {result.stderr.strip()}")
        return
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=BLOG_DIR, capture_output=True, text=True
    )
    print("✅ Push réussi" if result.returncode == 0 else f"❌ {result.stderr}")


if __name__ == "__main__":
    # Traiter tous les articles (pas index, ressources, a-propos, google*)
    exclude = {"index", "ressources", "a-propos", "google078e7cdcb18a7a75", "lucasmdev2026sandbox"}
    articles = [
        p for p in BLOG_DIR.glob("*.html")
        if p.stem not in exclude
    ]

    modified = 0
    for p in sorted(articles):
        if add_schema_to_article(p):
            modified += 1

    print(f"\n{modified} articles modifiés")
    if modified > 0:
        git_push_all()
