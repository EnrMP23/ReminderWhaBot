import requests
import logging
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Variables de configuración
API_KEY = os.getenv("RAPID_API_KEY", "38aeea1ee1msh8469e000f73dd78p108836jsndc03864ae7bc")  # Sustituir con tu clave de RapidAPI
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4LF4Zxi3J4_RnKd26u1M")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")

# Función para obtener la programación actual
def get_nfl_schedule():
    """Obtiene los partidos actuales de la NFL desde RapidAPI."""
    url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/schedule"
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()  # Retorna la programación de los partidos
    else:
        logging.error(f"Error en la solicitud: {response.status_code} - {response.text}")
        return None

# Función para el comando /games
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Obteniendo información de los partidos actuales...")
    games = get_nfl_schedule()

    if games and "games" in games:  # Ajustar según el formato exacto de la respuesta
        message_text = "¡Hola! Aquí tienes la lista de partidos actuales:\n\n"
        for game in games["games"]:
            home_team = game['homeTeam']
            away_team = game['awayTeam']
            start_time = game['startTime']
            formatted_date = datetime.fromisoformat(start_time).strftime('%d/%m/%Y %H:%M')

            message_text += f"🔹 {home_team} vs {away_team} - {formatted_date}\n"

        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("🥱 No se encontraron partidos disponibles.")

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
