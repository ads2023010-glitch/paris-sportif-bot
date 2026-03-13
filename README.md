# 🤖 Bot Telegram — Alertes Paris Sportifs ±2€

Bot qui analyse les cotes de football en temps réel et envoie une alerte Telegram
quand des mises optimales permettent de viser **+2€** si "1" gagne et **-2€** si "X2" gagne.

---

## 📋 Prérequis

- Python 3.10+
- Un bot Telegram créé via [@BotFather](https://t.me/BotFather)
- Une clé API gratuite sur [The Odds API](https://the-odds-api.com)
- Un compte [GitHub](https://github.com) + [Railway](https://railway.app)

---

## 🚀 Installation locale (pour tester)

### 1. Cloner le repo
```bash
git clone https://github.com/TON_USERNAME/TON_REPO.git
cd TON_REPO
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement
```bash
cp .env.example .env
```
Puis éditer `.env` avec tes vraies valeurs :
```
TELEGRAM_TOKEN=ton_token_botfather
TELEGRAM_CHAT_ID=ton_chat_id
ODDS_API_KEY=ta_cle_odds_api
```

#### Obtenir ton TELEGRAM_CHAT_ID :
1. Envoie un message à [@userinfobot](https://t.me/userinfobot) sur Telegram
2. Il te renvoie ton ID numérique

#### Obtenir ta clé The Odds API :
1. Inscription gratuite sur [https://the-odds-api.com](https://the-odds-api.com)
2. Plan gratuit = 500 requêtes/mois (suffisant pour le mode prod à 10h/jour)

### 4. Lancer le bot
```bash
python bot.py
```

---

## ⚙️ Passer du mode test au mode prod

Dans `bot.py`, cherche la section `# Scheduler` :

```python
# MODE TEST : toutes les 2 minutes ← commenter cette ligne
scheduler.add_job(analyser_et_envoyer, "interval", minutes=2, id="test_job")

# MODE PROD : tous les jours à 10h00 ← décommenter cette ligne
# scheduler.add_job(analyser_et_envoyer, "cron", hour=10, minute=0, id="prod_job")
```

---

## ☁️ Déploiement sur Railway

### 1. Pousser le code sur GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TON_USERNAME/TON_REPO.git
git push -u origin main
```

### 2. Créer un projet sur Railway
1. Va sur [railway.app](https://railway.app) → **New Project**
2. Choisir **Deploy from GitHub repo**
3. Sélectionner ton repo

### 3. Ajouter les variables d'environnement sur Railway
Dans ton projet Railway → onglet **Variables** → ajouter :
```
TELEGRAM_TOKEN     = ton_token
TELEGRAM_CHAT_ID   = ton_chat_id
ODDS_API_KEY       = ta_cle_api
```

### 4. Vérifier le déploiement
Railway va lire le `Procfile` et lancer `python bot.py` automatiquement.
Vérifie les logs dans l'onglet **Deployments**.

---

## 📊 Ligues analysées

| Ligue | Clé API |
|-------|---------|
| Ligue 1 (France) | `soccer_france_ligue1` |
| Premier League (Angleterre) | `soccer_epl` |
| La Liga (Espagne) | `soccer_spain_la_liga` |
| Bundesliga (Allemagne) | `soccer_germany_bundesliga` |
| Serie A (Italie) | `soccer_italy_serie_a` |
| Champions League | `soccer_uefa_champs_league` |

Pour ajouter/retirer des ligues, édite la liste `SPORTS` dans `bot.py`.

---

## 📬 Exemple de message reçu

```
⚽ PSG vs Marseille
🏆 France Ligue 1
🕐 15/03 20:00 UTC
─────────────────
📊 Cotes :
  • Cote 1 (domicile) : 2.3
  • Cote X2 (nul/ext) : 1.7
─────────────────
💰 Mises optimales :
  • Mise sur 1  : 6.67 €
  • Mise sur X2 : 6.67 €
─────────────────
📈 Résultats attendus :
  • Si 1 gagne  : +2.0 € ✅
  • Si X2 gagne : -2.0 € ✅
```

---

## 🔧 Personnalisation

| Paramètre | Fichier | Variable |
|-----------|---------|----------|
| Gain cible (+2€) | `bot.py` | `TARGET_GAIN` |
| Perte max (-2€) | `bot.py` | `TARGET_LOSS` |
| Mise minimum | `bot.py` | `MIN_MISE` |
| Fréquence test | `bot.py` | `minutes=2` |
| Heure prod | `bot.py` | `hour=10` |
