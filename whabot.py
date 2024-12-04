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
BASE_URL = "https://sportapi7.p.rapidapi.com/api/v1/player/7635/unique-tournament/8/season/18020/heatmap"
HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": "sportapi7.p.rapidapi.com"
}

# Función para obtener el heatmap de un jugador
def get_player_heatmap():
    """Obtiene el heatmap de un jugador de la API."""
    try:
        response = requests.get(BASE_URL, headers=HEADERS)
        response.raise_for_status()  # Lanza una excepción si hay errores en la solicitud
        data = response.json()  # Procesa la respuesta JSON
        return data if data else None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error en la solicitud al API de jugadores: {e}")
        return None

# Función para el comando /heatmap
async def heatmap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el heatmap del jugador especificado."""
    await update.message.reply_text("🔍 Obteniendo información del heatmap del jugador...")
    heatmap_data = get_player_heatmap()

    if heatmap_data:
        # Procesar los datos y mostrar información relevante
        player_name = heatmap_data.get("player", {}).get("name", "Desconocido")
        season = heatmap_data.get("season", {}).get("name", "Desconocida")
        tournament = heatmap_data.get("unique_tournament", {}).get("name", "Desconocido")
        positions = heatmap_data.get("heatmap", {}).get("positions", [])

        message_text = f"🌟 Heatmap de {player_name}:\n\n"
        message_text += f"🏆 Torneo: {tournament}\n"
        message_text += f"📅 Temporada: {season}\n\n"

        if positions:
            message_text += "📍 Posiciones destacadas:\n"
            for position in positions:
                x = position.get("x", "N/A")
                y = position.get("y", "N/A")
                intensity = position.get("intensity", "N/A")
                message_text += f"🔹 X: {x}, Y: {y}, Intensidad: {intensity}\n"
        else:
            message_text += "⚠️ No se encontraron datos de posiciones para el heatmap."

        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("❌ No se pudo obtener el heatmap. Intenta más tarde.")

# Configurar y ejecutar el bot de Telegram
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Agregar manejador para el comando /heatmap
    application.add_handler(CommandHandler("heatmap", heatmap))

    # Configurar el webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

    logging.info("BOT FUNCIONANDO")
