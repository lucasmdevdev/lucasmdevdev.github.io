#!/usr/bin/env python3
"""
Ajoute des sections "Lire aussi" entre articles liés pour améliorer le maillage interne SEO.
Ne modifie que les articles qui n'ont pas encore cette section.
"""

import subprocess
from pathlib import Path

BLOG_DIR = Path("/home/sax/projects/blog")

# Mapping des articles liés (slug -> liste de slugs liés)
RELATED = {
    "make-vs-zapier-vs-n8n-2026": [
        ("automatisations-no-code-gain-temps-2026", "5 automatisations no-code qui font gagner des heures"),
        ("premiere-automatisation-make-2026", "Créer votre première automatisation Make en 15 minutes"),
        ("free-tools-indie-hacker-2026", "Les meilleurs outils gratuits pour indie hackers"),
    ],
    "automatisations-no-code-gain-temps-2026": [
        ("make-vs-zapier-vs-n8n-2026", "Make vs Zapier vs n8n : lequel choisir en 2026 ?"),
        ("premiere-automatisation-make-2026", "Créer votre première automatisation Make en 15 minutes"),
        ("5-outils-ia-productivite-2026", "5 outils IA qui transforment votre productivité"),
    ],
    "premiere-automatisation-make-2026": [
        ("make-vs-zapier-vs-n8n-2026", "Make vs Zapier vs n8n : comparatif complet"),
        ("automatisations-no-code-gain-temps-2026", "5 automatisations no-code qui font gagner des heures"),
    ],
    "cursor-vs-copilot-2026": [
        ("replit-cursor-copilot-2026", "Replit Agent vs Cursor vs Copilot : le comparatif 2026"),
        ("meilleures-extensions-vscode-2026", "Les meilleures extensions VS Code en 2026"),
        ("claude-api-python-tutoriel-2026", "Claude API en Python : tutoriel complet"),
    ],
    "replit-cursor-copilot-2026": [
        ("cursor-vs-copilot-2026", "Cursor vs GitHub Copilot : lequel choisir ?"),
        ("meilleures-extensions-vscode-2026", "Les meilleures extensions VS Code en 2026"),
        ("python-automation-scripts-2026", "10 scripts Python pour automatiser votre workflow"),
    ],
    "meilleures-extensions-vscode-2026": [
        ("cursor-vs-copilot-2026", "Cursor vs GitHub Copilot : comparatif 2026"),
        ("python-automation-scripts-2026", "10 scripts Python pour développeurs"),
        ("replit-cursor-copilot-2026", "Replit Agent vs Cursor : le vrai comparatif"),
    ],
    "claude-api-python-tutoriel-2026": [
        ("alternative-chatgpt-gratuite-2026", "5 meilleures alternatives gratuites à ChatGPT"),
        ("python-automation-scripts-2026", "10 scripts Python pour automatiser votre vie"),
        ("llm-local-ollama-2026", "Faire tourner des LLM en local avec Ollama"),
    ],
    "python-automation-scripts-2026": [
        ("claude-api-python-tutoriel-2026", "Claude API Python : intégrer l'IA dans vos scripts"),
        ("automatisations-no-code-gain-temps-2026", "5 automatisations no-code pour gagner du temps"),
        ("meilleures-extensions-vscode-2026", "Les meilleures extensions VS Code pour Python"),
    ],
    "alternative-chatgpt-gratuite-2026": [
        ("5-outils-ia-productivite-2026", "5 outils IA qui transforment votre productivité"),
        ("claude-api-python-tutoriel-2026", "Utiliser Claude API gratuitement en Python"),
        ("llm-local-ollama-2026", "Faire tourner des LLM en local : guide complet"),
    ],
    "5-outils-ia-productivite-2026": [
        ("alternative-chatgpt-gratuite-2026", "5 meilleures alternatives gratuites à ChatGPT"),
        ("automatisations-no-code-gain-temps-2026", "5 automatisations no-code pour gagner du temps"),
        ("llm-local-ollama-2026", "LLM en local avec Ollama : guide 2026"),
    ],
    "llm-local-ollama-2026": [
        ("alternative-chatgpt-gratuite-2026", "5 alternatives gratuites à ChatGPT en 2026"),
        ("claude-api-python-tutoriel-2026", "Claude API Python : tutoriel complet"),
        ("5-outils-ia-productivite-2026", "5 outils IA pour la productivité"),
    ],
    "github-pages-blog-gratuit-2026": [
        ("free-tools-indie-hacker-2026", "Les meilleurs outils gratuits pour indie hackers"),
        ("creer-newsletter-rentable-2026", "Créer une newsletter rentable en 2026"),
        ("make-vs-zapier-vs-n8n-2026", "Automatiser votre workflow avec Make ou Zapier"),
    ],
    "free-tools-indie-hacker-2026": [
        ("github-pages-blog-gratuit-2026", "Créer un blog gratuit avec GitHub Pages"),
        ("creer-newsletter-rentable-2026", "Créer une newsletter rentable en 2026"),
        ("micro-saas-idees-rentables-2026", "10 idées de micro-SaaS rentables"),
    ],
    "creer-newsletter-rentable-2026": [
        ("free-tools-indie-hacker-2026", "Les meilleurs outils gratuits pour indie hackers"),
        ("github-pages-blog-gratuit-2026", "Créer un blog gratuit avec GitHub Pages"),
        ("5-outils-ia-productivite-2026", "5 outils IA pour booster votre productivité"),
    ],
    "meilleur-vpn-2026": [
        ("meilleur-gestionnaire-mots-de-passe-2026", "Meilleur gestionnaire de mots de passe 2026"),
        ("free-tools-indie-hacker-2026", "Les meilleurs outils gratuits pour indie hackers"),
    ],
}

SECTION_MARKER = "<!-- lire-aussi -->"

SECTION_TEMPLATE = """
    </div><!-- end article-content -->

    <!-- lire-aussi -->
    <div class="related-articles">
      <h3>Lire aussi</h3>
      <ul>
{links}      </ul>
    </div>

  </article>"""

LINK_TEMPLATE = '        <li><a href="{slug}.html">{title}</a></li>\n'


def process_article(slug, related_list):
    path = BLOG_DIR / f"{slug}.html"
    if not path.exists():
        print(f"⚠️  {slug}.html non trouvé, skip")
        return False

    content = path.read_text(encoding="utf-8")

    if SECTION_MARKER in content:
        print(f"  ↩️  {slug}: déjà traité")
        return False

    links_html = "".join(
        LINK_TEMPLATE.format(slug=r_slug, title=r_title)
        for r_slug, r_title in related_list
    )
    section = SECTION_TEMPLATE.format(links=links_html)

    # Remplacer </article> (premier occurrence) par notre section
    # On cherche le pattern "</div>\n\n  </article>" ou similaire
    # Plus robuste : on remplace la fermeture article-content + </article>
    if '    </div>\n\n  </article>' in content:
        new_content = content.replace(
            '    </div>\n\n  </article>',
            section,
            1
        )
    elif '    </div>\n  </article>' in content:
        new_content = content.replace(
            '    </div>\n  </article>',
            section,
            1
        )
    else:
        # Fallback: chercher </article> tout seul
        if '</article>' not in content:
            print(f"  ❌ {slug}: impossible de trouver </article>")
            return False
        # Remplacer la première occurrence de </article>
        # On veut garder le bon </div> avant
        # On va juste insérer notre section avant </article>
        new_content = content.replace('  </article>', section.replace('  </article>', '') + '\n  </article>', 1)

    path.write_text(new_content, encoding="utf-8")
    print(f"  ✅ {slug}: {len(related_list)} liens internes ajoutés")
    return True


def git_push_all():
    """Push tous les changements en un seul commit."""
    token_result = subprocess.run(
        ["/home/sax/bin/gh", "auth", "token"],
        capture_output=True, text=True
    )
    token = token_result.stdout.strip()
    if not token:
        print("❌ Pas de token GitHub")
        return

    subprocess.run(
        ["git", "remote", "set-url", "origin",
         f"https://lucasmdevdev:{token}@github.com/lucasmdevdev/lucasmdevdev.github.io.git"],
        cwd=BLOG_DIR, capture_output=True
    )

    subprocess.run(["git", "add", "-A"], cwd=BLOG_DIR)
    result = subprocess.run(
        ["git", "commit", "-m", "SEO: ajout maillage interne (liens Lire aussi) sur tous les articles"],
        cwd=BLOG_DIR, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Commit: {result.stderr}")
        return

    result = subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=BLOG_DIR, capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✅ Push GitHub réussi")
    else:
        print(f"❌ Push échoué: {result.stderr}")


if __name__ == "__main__":
    modified = 0
    for slug, related in RELATED.items():
        if process_article(slug, related):
            modified += 1

    print(f"\n{modified} articles modifiés")

    if modified > 0:
        print("Push vers GitHub...")
        git_push_all()
