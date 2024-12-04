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
RAPIDAPI_KEY = os.getenv("RAPID_API_KEY", "38aeea1ee1msh8469e000f73dd78p108836jsndc03864ae7bc")  # API Key de RapidAPI
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4LF4Zxi3J4_RnKd26u1M")  # Token del bot de Telegram
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")  # URL pública del webhook

# Configuración del endpoint y headers
BASE_URL = "https://nfl-api-data.p.rapidapi.com/nfl-team-listing/v1/data"
HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "nfl-api-data.p.rapidapi.com"
}

# Función para obtener la lista de equipos de la NFL
def get_nfl_teams():
    """Obtiene la lista de equipos de la NFL desde la API."""
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        response.raise_for_status()  # Lanza una excepción si hay errores en la solicitud
        data = response.json()  # Procesa la respuesta JSON
        return data if data else []
    except requests.exceptions.RequestException as e:
        logging.error(f"Error en la solicitud a NFL API: {e}")
        return []

# Función para el comando /teams
async def teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista de equipos de la NFL."""
    await update.message.reply_text("🔍 Obteniendo la lista de equipos de la NFL...")
    teams = get_nfl_teams()

    if teams:
        message_text = "🏈 Lista de equipos de la NFL:\n\n"
        for team in teams.get("teams", []):  # Asumiendo que los equipos están en un objeto llamado "teams"
            team_name = team.get("name", "Nombre no disponible")
            city = team.get("city", "Ciudad no disponible")
            abbreviation = team.get("abbreviation", "Abreviación no disponible")
            message_text += f"🔹 {team_name} ({abbreviation}) - {city}\n"

        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("🥱 No se pudo obtener la lista de equipos. Intenta más tarde.")

# Configurar y ejecutar el bot de Telegram
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Agregar manejador para el comando /teams
    application.add_handler(CommandHandler("teams", teams))

    # Configurar el webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

    logging.info("BOT FUNCIONANDO")
