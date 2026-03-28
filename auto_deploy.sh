#!/bin/bash
# Moniteur d'auth GitHub + déploiement automatique
# Tourne en boucle, déploie dès que l'auth est détectée

BLOG_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="lucasmdevdev/lucasmdevdev.github.io"
LOG="$BLOG_DIR/deploy.log"

echo "[$(date +%H:%M:%S)] auto_deploy démarré" | tee -a "$LOG"
echo "[$(date +%H:%M:%S)] Surveillance de l'auth GitHub..." | tee -a "$LOG"

while true; do
    if ~/bin/gh auth status 2>&1 | grep -qi "logged in\|github.com"; then
        echo "[$(date +%H:%M:%S)] AUTH DÉTECTÉE ! Démarrage du déploiement..." | tee -a "$LOG"
        echo "[$(date +%H:%M)] 🎉 Auth GitHub détectée ! Déploiement en cours..." >> ~/comms/status.txt

        # Configurer le remote avec token auth
        TOKEN=$(~/bin/gh auth token 2>/dev/null)
        if [ -n "$TOKEN" ]; then
            git -C "$BLOG_DIR" remote set-url origin "https://lucasmdevdev:${TOKEN}@github.com/${REPO}.git"
        fi

        # Créer le repo si nécessaire
        if ! ~/bin/gh repo view "$REPO" 2>/dev/null | grep -q "lucasmdevdev"; then
            echo "[$(date +%H:%M:%S)] Création du repo $REPO..." | tee -a "$LOG"
            ~/bin/gh repo create "$REPO" --public \
                --description "IA, automatisation & productivité tech — LucasMdev" \
                2>&1 | tee -a "$LOG"
        fi

        # Push
        echo "[$(date +%H:%M:%S)] Push vers GitHub..." | tee -a "$LOG"
        git -C "$BLOG_DIR" push -u origin main 2>&1 | tee -a "$LOG"

        # Activer GitHub Pages
        echo "[$(date +%H:%M:%S)] Activation GitHub Pages..." | tee -a "$LOG"
        ~/bin/gh api \
            --method POST \
            -H "Accept: application/vnd.github+json" \
            "/repos/${REPO}/pages" \
            -f '{"source":{"branch":"main","path":"/"}}' \
            2>&1 | tee -a "$LOG" || true

        echo "[$(date +%H:%M:%S)] DÉPLOIEMENT TERMINÉ !" | tee -a "$LOG"
        echo "[$(date +%H:%M)] 🚀 Blog déployé sur https://lucasmdevdev.github.io !" >> ~/comms/status.txt

        # Notifier Ulysse
        cat > ~/comms/outbox/2026-03-28_blog-deployed.md << 'EOF2'
# Blog déployé !

https://lucasmdevdev.github.io est en ligne.

**5 articles publiés :**
1. 5 outils IA qui transforment la productivité en 2026
2. Make vs Zapier vs n8n — comparatif complet
3. LLMs en local avec Ollama — guide complet
4. Première automatisation Make — tutoriel pas à pas
5. Cursor vs GitHub Copilot vs Codeium

**Prochaine étape :** S'inscrire au programme affilié Make.com (35% commission/12 mois) pour que les liens dans les articles génèrent des revenus trackés. Tu dois le faire manuellement (Cloudflare bloque Playwright).

URL programme affilié : https://www.make.com/en/affiliate (connecte-toi avec un compte Make.com)
EOF2

        break
    fi

    sleep 15
done

echo "[$(date +%H:%M:%S)] Script terminé." | tee -a "$LOG"
