#!/bin/bash
# Auto-publish script — publie les articles en attente sur le blog GitHub Pages
# À lancer via cron : 0 9 * * * /home/sax/projects/blog/publish_scheduled.sh

BLOG_DIR="/home/sax/projects/blog"
QUEUE_DIR="/home/sax/projects/content-engine/queue"
LOG="/home/sax/projects/blog/publish.log"

echo "[$(date +%Y-%m-%d\ %H:%M:%S)] === Auto-publish démarré ===" >> "$LOG"

# Vérifier l'auth GitHub
if ! ~/bin/gh auth status 2>/dev/null | grep -qi "github.com"; then
    echo "[$(date +%H:%M:%S)] ERREUR: Non authentifié sur GitHub" >> "$LOG"
    exit 1
fi

# Vérifier s'il y a des articles en queue
mkdir -p "$QUEUE_DIR"
PENDING=$(ls "$QUEUE_DIR"/*.html 2>/dev/null | wc -l)

if [ "$PENDING" -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Aucun article en attente" >> "$LOG"
    exit 0
fi

# Prendre le premier article de la queue
NEXT=$(ls "$QUEUE_DIR"/*.html 2>/dev/null | head -1)
FILENAME=$(basename "$NEXT")

echo "[$(date +%H:%M:%S)] Publication de: $FILENAME" >> "$LOG"

# Copier vers le blog
cp "$NEXT" "$BLOG_DIR/$FILENAME"

# Mettre à jour l'index (ajout de la card)
# TODO: générer la card automatiquement

# Git commit et push
cd "$BLOG_DIR"
TOKEN=$(~/bin/gh auth token 2>/dev/null)
git remote set-url origin "https://lucasmdevdev:${TOKEN}@github.com/lucasmdevdev/lucasmdevdev.github.io.git"
git add "$FILENAME"
git commit -m "Auto-publish: $FILENAME"
git push origin main

# Déplacer l'article vers published/
mkdir -p "$QUEUE_DIR/published"
mv "$NEXT" "$QUEUE_DIR/published/"

echo "[$(date +%H:%M:%S)] DONE: $FILENAME publié" >> "$LOG"
echo "[$(date +%H:%M)] Article publié: $FILENAME" >> ~/comms/status.txt
