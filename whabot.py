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
RAPIDAPI_KEY = os.getenv("RAPID_API_KEY", "38aeea1ee1msh8469e000f73dd78p108836jsndc03864ae7bc")  # API Key de RapidAPI
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4LF4Zxi3J4_RnKd26u1M")  # Token del bot de Telegram
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")  # URL pública del webhook

# Configuración del endpoint y headers
BASE_URL = "https://nfl-api-data.p.rapidapi.com/nfl/games"
HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "nfl-api-data.p.rapidapi.com"
}

# Función para obtener los partidos actuales
def get_current_games():
    """Obtiene los partidos actuales de la NFL."""
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        response.raise_for_status()  # Lanza una excepción si la respuesta es un error
        data = response.json()  # Procesa la respuesta JSON
        return data if data else []
    except requests.exceptions.RequestException as e:
        logging.error(f"Error en la solicitud a NFL API: {e}")
        return []

# Función para el comando /games
async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los partidos actuales de la NFL."""
    await update.message.reply_text("🔍 Obteniendo información de los partidos...")
    games = get_current_games()

    if games:
        message_text = "🏈 Lista de partidos actuales de la NFL:\n\n"
        for game in games:
            home_team = game.get("home_team", "Desconocido")
            away_team = game.get("away_team", "Desconocido")
            game_time = game.get("game_time", "Hora no disponible")
            message_text += f"🔹 {away_team} vs {home_team}\n🕒 {game_time}\n\n"

        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("🥱 No se encontraron partidos en este momento. Intenta más tarde.")

# Configurar y ejecutar el bot de Telegram
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Agregar manejador para el comando /games
    application.add_handler(CommandHandler("games", games))

    # Configurar el webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

    logging.info("BOT FUNCIONANDO")
