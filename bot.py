import os
import logging
import requests
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ODDS_API_KEY    = os.getenv("ODDS_API_KEY")

TARGET_GAIN     = 2.0   # +2€ si "1" gagne
TARGET_LOSS     = 2.0   # -2€ si "X2" gagne
MIN_MISE        = 0.10  # mise minimum en €

SPORTS = [
    "soccer_france_ligue_one",       # Ligue 1 - France
    "soccer_france_ligue_two",       # Ligue 2 - France
    "soccer_france_coupe_de_france", # Coupe de France
    "soccer_epl",                    # Premier League - Angleterre
    "soccer_spain_la_liga",          # La Liga - Espagne
    "soccer_germany_bundesliga",     # Bundesliga - Allemagne
    "soccer_italy_serie_a",          # Serie A - Italie
    "soccer_uefa_champs_league",     # Champions League
    "soccer_uefa_europa_league",     # Europa League
    "soccer_netherlands_eredivisie", # Eredivisie - Pays-Bas
    "soccer_portugal_primeira_liga", # Primeira Liga - Portugal
]

BOOKMAKERS = ["unibet", "betclic", "winamax", "betway", "bet365"]

# Mises déjà envoyées (évite les doublons dans la session)
sent_matches = set()


# ── Calcul des mises ──────────────────────────────────────────────────────────
def calculer_mises(cote_1: float, cote_x2: float):
    """
    Système ±2€ :
      m1*(c1-1) - mx2 = +TARGET_GAIN
      mx2*(cx2-1) - m1 = -TARGET_LOSS
    => m1 = TARGET_GAIN*(cx2-2) / [(c1-1)*(cx2-1)-1]  [si TARGET_GAIN==TARGET_LOSS]
    => formule générale ci-dessous
    """
    g = TARGET_GAIN
    l = TARGET_LOSS
    denom = (cote_1 - 1) * (cote_x2 - 1) - 1
    if abs(denom) < 1e-9:
        return None, None

    # Résolution générale
    # m1*(c1-1) - mx2 = g  => mx2 = m1*(c1-1) - g
    # [m1*(c1-1)-g]*(cx2-1) - m1 = -l
    # m1*[(c1-1)*(cx2-1)-1] = -l + g*(cx2-1)
    # m1 = (g*(cx2-1) - l) / denom
    m1  = (g * (cote_x2 - 1) - l) / denom
    mx2 = m1 * (cote_1 - 1) - g

    if m1 < MIN_MISE or mx2 < MIN_MISE:
        return None, None

    return round(m1, 2), round(mx2, 2)


# ── Récupération des cotes via The Odds API ───────────────────────────────────
def fetch_odds():
    matches = []
    for sport in SPORTS:
        url = (
            f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
            f"?apiKey={ODDS_API_KEY}"
            f"&regions=eu"
            f"&markets=h2h"
            f"&oddsFormat=decimal"
            f"&bookmakers={','.join(BOOKMAKERS)}"
        )
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                matches.extend(resp.json())
            else:
                logger.warning(f"Odds API {sport}: {resp.status_code} - {resp.text[:200]}")
        except Exception as e:
            logger.error(f"Erreur fetch {sport}: {e}")
    return matches


def extraire_cotes(match: dict):
    """Extrait la meilleure cote 1 et la meilleure cote X2 parmi tous les bookmakers."""
    best_1  = None  # victoire équipe domicile
    best_x2 = None  # nul OU victoire extérieur (on prend le max)

    for bookmaker in match.get("bookmakers", []):
        for market in bookmaker.get("markets", []):
            if market.get("key") != "h2h":
                continue
            outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}
            home = match.get("home_team")
            away = match.get("away_team")

            cote_1  = outcomes.get(home)
            cote_x  = outcomes.get("Draw")
            cote_2  = outcomes.get(away)

            if cote_1 and (best_1 is None or cote_1 > best_1):
                best_1 = cote_1

            # X2 = max(Draw, Away)
            for c in [cote_x, cote_2]:
                if c and (best_x2 is None or c > best_x2):
                    best_x2 = c

    return best_1, best_x2


# ── Analyse et envoi ──────────────────────────────────────────────────────────
async def analyser_et_envoyer():
    bot = Bot(token=TELEGRAM_TOKEN)
    logger.info("🔍 Analyse des matchs en cours...")

    matches = fetch_odds()
    opportunites = 0

    for match in matches:
        match_id   = match.get("id", "")
        home_team  = match.get("home_team", "?")
        away_team  = match.get("away_team", "?")
        commence   = match.get("commence_time", "")
        sport_key  = match.get("sport_key", "")

        # Evite les doublons
        if match_id in sent_matches:
            continue

        cote_1, cote_x2 = extraire_cotes(match)
        if not cote_1 or not cote_x2:
            continue

        m1, mx2 = calculer_mises(cote_1, cote_x2)
        if m1 is None:
            continue

        # Formater la date
        try:
            dt = datetime.fromisoformat(commence.replace("Z", "+00:00"))
            date_str = dt.strftime("%d/%m %H:%M")
        except Exception:
            date_str = commence[:16]

        # Vérification gains
        gain_si_1  = round(m1  * (cote_1  - 1) - mx2, 2)
        gain_si_x2 = round(mx2 * (cote_x2 - 1) - m1,  2)

        sport_label = sport_key.replace("soccer_", "").replace("_", " ").title()

        message = (
            f"⚽ *{home_team} vs {away_team}*\n"
            f"🏆 {sport_label}\n"
            f"🕐 {date_str} UTC\n"
            f"─────────────────\n"
            f"📊 *Cotes :*\n"
            f"  • Cote 1 (domicile) : `{cote_1}`\n"
            f"  • Cote X2 (nul/ext) : `{cote_x2}`\n"
            f"─────────────────\n"
            f"💰 *Mises optimales :*\n"
            f"  • Mise sur 1  : `{m1} €`\n"
            f"  • Mise sur X2 : `{mx2} €`\n"
            f"─────────────────\n"
            f"📈 *Résultats attendus :*\n"
            f"  • Si 1 gagne  : `+{gain_si_1} €` ✅\n"
            f"  • Si X2 gagne : `{gain_si_x2} €` {'✅' if gain_si_x2 >= -2.01 else '⚠️'}\n"
        )

        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            sent_matches.add(match_id)
            opportunites += 1
            logger.info(f"✅ Envoyé : {home_team} vs {away_team}")
        except Exception as e:
            logger.error(f"Erreur envoi Telegram: {e}")

    if opportunites == 0:
        logger.info("Aucune opportunité trouvée ce cycle.")
    else:
        logger.info(f"{opportunites} opportunité(s) envoyée(s).")


# ── Scheduler ─────────────────────────────────────────────────────────────────
async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Paris")

    # MODE TEST : toutes les 2 minutes
    # Commenter cette ligne et décommenter celle du dessous pour passer en prod
    scheduler.add_job(analyser_et_envoyer, "interval", minutes=2, id="test_job")

    # MODE PROD : tous les jours à 10h00 (commenter la ligne test d'abord)
    # scheduler.add_job(analyser_et_envoyer, "cron", hour=10, minute=0, id="prod_job")

    scheduler.start()
    logger.info("🤖 Bot démarré. Ctrl+C pour arrêter.")

    # Lancer une première analyse immédiatement au démarrage
    await analyser_et_envoyer()

    # Garder le process vivant
    import asyncio
    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Bot arrêté.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
