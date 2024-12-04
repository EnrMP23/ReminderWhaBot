import requests
import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Variables de configuración
API_KEY = os.getenv("RAPID_API_KEY", "38aeea1ee1msh8469e000f73dd78p108836jsndc03864ae7bc")  # Cambia por tu RapidAPI Key
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4LF4Zxi3J4_RnKd26u1M")  # Cambia por tu token del bot
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")  # Cambia por tu URL pública del webhook

# Definir los headers para la solicitud
headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "nfl-api-data.p.rapidapi.com"
}

# Función para obtener los partidos actuales de la semana
def get_nfl_current_week_games():
    """Obtiene los partidos de la semana actual usando la API de RapidAPI."""
    url = "https://nfl-api-data.p.rapidapi.com/current/games"
    logging.info(f"Consultando los partidos actuales: {url}")

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        games = response.json()
        if games:
            logging.info(f"Partidos encontrados: {len(games)}")
            return games
        else:
            logging.warning("No se encontraron partidos en la respuesta de la API.")
            return []
    else:
        logging.error(f"Error en la solicitud: {response.status_code} - {response.text}")
        return []

# Función para el comando /games
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Obteniendo información de los partidos actuales...")
    matches = get_nfl_current_week_games()

    if matches:
        message_text = "¡Hola! Aquí tienes la lista de partidos actuales:\n\n"
        for match in matches:
            home_team = match['home_team']
            away_team = match['away_team']
            game_time = match['game_time']  # Se asume que esta clave contiene la hora del juego

            message_text += f"🔹 {home_team} vs {away_team} - Fecha y hora: {game_time}\n"

        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("🥱 No se encontraron partidos disponibles. Intenta más tarde.")

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
