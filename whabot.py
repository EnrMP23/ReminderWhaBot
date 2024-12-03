import requests
import logging
import os
from datetime import datetime, timedelta
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Variables de configuración
API_KEY = os.getenv("SPORTSDATAIO_DATA_API_KEY", "205bca4e7d76426ea69a738d9ef11641")  # API key
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4LF4Zxi3J4_RnKd26u1M")  # Token de tu bot de Telegram
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://tuservidor.com/webhook")  # URL pública de tu webhook
season = 2024

# Definir los headers para la solicitud
headers = {'Ocp-Apim-Subscription-Key': API_KEY}

# Función para calcular la semana actual de la temporada NFL
def get_current_nfl_week():
    """Calcula la semana actual de la temporada NFL basada en la fecha."""
    season_start_date = datetime(2024, 9, 5)  # Fecha del primer jueves de la temporada 2024
    today = datetime.today()
    delta = today - season_start_date
    week = (delta.days // 7) + 1  # Divide los días entre 7 y suma 1 para obtener la semana actual
    return max(1, min(week, 18))  # Asegura que esté entre las semanas válidas (1-18)

# Función para obtener los partidos de la semana actual
def get_nfl_matches_current_week():
    """Obtiene los partidos de la semana actual."""
    current_week = get_current_nfl_week()
    url = f"https://api.sportsdata.io/v3/nfl/scores/json/GamesByWeek/{season}/{current_week}"
    logging.info(f"Fetching games for season {season}, week {current_week} | URL: {url}")

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        games = response.json()
        if games:
            logging.info(f"Partidos encontrados para la semana {current_week}: {len(games)}")
            return games
        else:
            logging.warning(f"No se encontraron partidos para la temporada {season}, semana {current_week}.")
            return []
    elif response.status_code == 404:
        logging.warning(f"No se encontraron datos para la temporada {season}, semana {current_week}. Verifica la API.")
    else:
        logging.error(f"Error inesperado: {response.status_code} - {response.text}")
    return []


# Función para el comando /games
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Obteniendo información de los partidos de esta semana...")
    matches = get_nfl_matches_current_week()

    if matches:
        message_text = "¡Hola! Aquí tienes la lista de partidos de esta semana:\n\n"
        for match in matches:
            home_team = match['HomeTeam']
            away_team = match['AwayTeam']
            utc_date = datetime.strptime(match['Date'], '%Y-%m-%dT%H:%M:%S')
            local_date = utc_date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('America/Hermosillo'))
            formatted_date = local_date.strftime('Fecha: %d/%m/%Y Hora: %H:%M (Hora Sonora)')

            message_text += f"🔹 {match['GameKey']}: {home_team} vs {away_team} - {formatted_date}\n"

        message_text += "Usa /predict <GameKey> para predecir el resultado de un partido."
        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("🥱 No se encontraron partidos disponibles para esta semana. Intenta más tarde.")

# Configurar y ejecutar el bot de Telegram
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("games", start))

    application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

    logging.info("BOT FUNCIONANDO")
