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
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")  # URL pública de tu webhook

# Definir los headers para la solicitud
headers = {'Ocp-Apim-Subscription-Key': API_KEY}

# Función para obtener los partidos del día siguiente
def get_nfl_matches_next_day():
    """Obtiene los partidos del siguiente día."""
    # Obtener la fecha de mañana
    next_day = datetime.utcnow() + timedelta(days=1)  # UTC para alinearse con la API
    next_day_str = next_day.strftime('%Y-%m-%d')  # Formato YYYY-MM-DD

    # Construir la URL del endpoint
    url = f"https://api.sportsdata.io/v3/nfl/scores/json/GamesByDate/{next_day_str}"
    logging.info(f"Fetching games for date: {next_day_str} | URL: {url}")

    # Hacer la solicitud
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        logging.info(f"Games fetched successfully for {next_day_str}")
        return response.json()  # Lista de partidos
    elif response.status_code == 404:
        logging.warning(f"No games found for {next_day_str}")
        return []  # No hay partidos
    else:
        logging.error(f"Error fetching games for {next_day_str}: {response.status_code} - {response.text}")
        return []

# Función para el comando /games
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Obteniendo información de los partidos...")
    matches = get_nfl_matches_next_day()  # Obtener partidos para el siguiente día

    if matches:
        message_text = "¡Hola! Aquí tienes la lista de partidos del siguiente día:\n\n"
        for match in matches:
            home_team = match.get('HomeTeam', 'Desconocido')
            away_team = match.get('AwayTeam', 'Desconocido')
            game_date = match.get('Date', '')

            try:
                utc_date = datetime.strptime(game_date, '%Y-%m-%dT%H:%M:%S')
                local_date = utc_date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('America/Hermosillo'))
                formatted_date = local_date.strftime('Fecha: %d/%m/%Y Hora: %H:%M (Hora Sonora)')
            except ValueError:
                formatted_date = "Fecha no disponible"

            message_text += f"🔹 {home_team} vs {away_team} - {formatted_date}\n"

        message_text += "Usa /predict <GameKey> para predecir el resultado de un partido."
        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("🥱 No se encontraron partidos disponibles para mañana.")

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
