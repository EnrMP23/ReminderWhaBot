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
BASE_URL = "https://nfl-api-data.p.rapidapi.com/nfl-team-schedule"
HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "nfl-api-data.p.rapidapi.com"
}

# Función para obtener el calendario de un equipo
def get_team_schedule(team_id):
    """Obtiene el calendario de un equipo de la NFL por su ID."""
    try:
        querystring = {"id": str(team_id)}
        response = requests.get(BASE_URL, headers=HEADERS, params=querystring)
        response.raise_for_status()  # Lanza una excepción si hay errores en la solicitud
        data = response.json()  # Procesa la respuesta JSON
        return data if isinstance(data, list) else []  # Devuelve una lista si la estructura es correcta
    except requests.exceptions.RequestException as e:
        logging.error(f"Error en la solicitud a NFL API: {e}")
        return []

# Función para el comando /schedule
async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el calendario de un equipo de la NFL."""
    if len(context.args) < 1:
        await update.message.reply_text("Por favor, proporciona un ID de equipo. Ejemplo: /schedule 22")
        return

    team_id = context.args[0]
    await update.message.reply_text(f"🔍 Obteniendo el calendario del equipo con ID {team_id}...")
    schedule = get_team_schedule(team_id)

    if schedule:
        message_text = f"📅 Calendario del equipo con ID {team_id}:\n\n"
        for game in schedule:
            opponent = game.get("opponent", "Desconocido")
            date = game.get("date", "Fecha no disponible")
            home_or_away = "Casa" if game.get("is_home", False) else "Visita"
            message_text += f"🔹 {date}: Contra {opponent} ({home_or_away})\n"

        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text(f"🥱 No se encontró calendario para el equipo con ID {team_id}. Intenta más tarde.")

# Configurar y ejecutar el bot de Telegram
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Agregar manejador para el comando /schedule
    application.add_handler(CommandHandler("schedule", schedule))

    # Configurar el webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

    logging.info("BOT FUNCIONANDO")
