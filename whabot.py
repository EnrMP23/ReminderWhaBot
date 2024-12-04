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
API_KEY = os.getenv("RAPID_API_KEY", "38aeea1ee1msh8469e000f73dd78p108836jsndc03864ae7bc")  # API Key de RapidAPI
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4Zxi3J4_RnKd26u1M")  # Token del bot de Telegram
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://tuservidor.com/webhook")  # URL pública del webhook

# Configuración del endpoint y headers
BASE_URL = "https://chatgpt-42.p.rapidapi.com/ask"
HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "chatgpt-42.p.rapidapi.com",
    "Content-Type": "application/json"
}

# Función para realizar la consulta a la API
def ask_chatgpt(query: str) -> str:
    """Realiza una consulta al endpoint de ChatGPT-42 y devuelve la respuesta."""
    payload = {"query": query, "language": "en"}  # Puedes cambiar 'language' según lo requieras
    try:
        response = requests.post(BASE_URL, json=payload, headers=HEADERS)
        response.raise_for_status()  # Lanza una excepción si el código HTTP indica error
        data = response.json()
        return data.get("response", "No se obtuvo una respuesta válida de la API.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error en la solicitud a ChatGPT-42: {e}")
        return "Lo siento, no pude procesar tu solicitud en este momento."

# Función para manejar el comando /ask en Telegram
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("❌ Por favor, proporciona una pregunta después del comando /ask.")
        return

    query = " ".join(context.args)  # Combina los argumentos como una sola consulta
    await update.message.reply_text("🤖 Procesando tu consulta, un momento...")
    response = ask_chatgpt(query)  # Realiza la consulta a la API
    await update.message.reply_text(response)

# Configurar y ejecutar el bot de Telegram
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Manejar el comando /ask
    application.add_handler(CommandHandler("ask", ask))

    # Configurar el webhook para producción
    application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

    logging.info("BOT FUNCIONANDO")
