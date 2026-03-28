#!/bin/bash
# Script de déploiement GitHub Pages
# Usage: ./deploy.sh

set -e

BLOG_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="lucasmdevdev/lucasmdevdev.github.io"

echo "[deploy] Vérification de l'auth GitHub..."
if ! ~/bin/gh auth status 2>/dev/null; then
    echo "[deploy] ERREUR: Non authentifié. Lance 'gh auth login' d'abord."
    exit 1
fi

echo "[deploy] Auth OK. Vérification du repo..."

# Créer le repo s'il n'existe pas
if ! ~/bin/gh repo view "$REPO" 2>/dev/null; then
    echo "[deploy] Création du repo $REPO..."
    ~/bin/gh repo create "$REPO" --public --description "IA, automatisation & productivité tech"
    echo "[deploy] Repo créé."
else
    echo "[deploy] Repo existant trouvé."
fi

# Configurer le remote avec token
TOKEN=$(~/bin/gh auth token)
git -C "$BLOG_DIR" remote set-url origin "https://lucasmdevdev:${TOKEN}@github.com/${REPO}.git"

# Push
echo "[deploy] Push vers GitHub..."
git -C "$BLOG_DIR" push -u origin main

echo "[deploy] Push OK!"

# Activer GitHub Pages via API
echo "[deploy] Activation de GitHub Pages..."
~/bin/gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  "/repos/${REPO}/pages" \
  -f source='{"branch":"main","path":"/"}' 2>/dev/null || \
~/bin/gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${REPO}/pages" \
  -f source='{"branch":"main","path":"/"}' 2>/dev/null || \
echo "[deploy] Pages déjà configuré ou erreur (vérifier manuellement)"

echo ""
echo "=========================================="
echo "DEPLOY TERMINÉ !"
echo "URL: https://lucasmdevdev.github.io"
echo "Attendre 1-2 min pour que GitHub Pages compile"
echo "=========================================="
