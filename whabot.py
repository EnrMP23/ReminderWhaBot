import os
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
import instaloader
import logging

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7680282118:AAHAu9QhhahvyRCflOt3u2rNhlcH88e5hoM")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")
PORT = int(os.getenv("PORT", "8443"))
MONITOREO_FILE = "monitoreo.json"

# Datos de inicio de sesión de Instagram
INSTAGRAM_USER = os.getenv("INSTAGRAM_USER", "@enriquemaynez")
INSTAGRAM_PASS = os.getenv("INSTAGRAM_PASS", "@EnriqueMP2002")

# Instaloader para interacción con Instagram
loader = instaloader.Instaloader()

# Configuración del log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Funciones para cargar y guardar datos
def load_data():
    try:
        if os.path.exists(MONITOREO_FILE):
            with open(MONITOREO_FILE, "r") as file:
                return json.load(file)
    except json.JSONDecodeError:
        return {}
    return {}

def save_data(data):
    with open(MONITOREO_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Iniciar sesión en Instagram
def login_instagram():
    try:
        # Intentar cargar la sesión guardada
        loader.load_session_from_file(INSTAGRAM_USER)  # Cargar desde archivo
        logger.info("Sesión de Instagram cargada exitosamente.")
    except FileNotFoundError:
        # Si no existe la sesión guardada, hacer login
        logger.info("No se encontró sesión guardada, iniciando sesión con usuario y contraseña...")
        loader.login(INSTAGRAM_USER, INSTAGRAM_PASS)
        loader.save_session_to_file()  # Guardar la sesión para futuras ejecuciones
        logger.info("Sesión de Instagram guardada exitosamente.")

# Comando start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id  # Obtener el chat ID del usuario
    logger.info(f"Comando /start recibido de chat ID {chat_id}")
    await update.message.reply_text(
        f"¡Hola! Soy un bot para monitorear los seguidos de perfiles en Instagram.\n"
        f"Tu chat ID es: {chat_id}\n"
        "Comandos disponibles:\n"
        "- /monitorear <perfil>: Agrega un perfil para monitorear.\n"
        "- /listar: Muestra los perfiles monitoreados."
    )

# Comando monitorear
async def monitorear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        await update.message.reply_text("Por favor, proporciona un nombre de perfil. Ejemplo: /monitorear instagram")
        return

    perfil = context.args[0]
    monitoreo = load_data()

    if perfil in monitoreo:
        await update.message.reply_text(f"El perfil {perfil} ya está siendo monitoreado.")
    else:
        monitoreo[perfil] = []
        save_data(monitoreo)
        await update.message.reply_text(f"El perfil {perfil} ha sido agregado al monitoreo.")

# Comando listar
async def listar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    monitoreo = load_data()
    if not monitoreo:
        await update.message.reply_text("No hay perfiles en monitoreo.")
    else:
        perfiles = "\n".join(monitoreo.keys())
        await update.message.reply_text(f"Perfiles monitoreados:\n{perfiles}")

# Lógica del monitoreo
async def analizar_perfil(perfil, chat_id, application) -> None:
    try:
        # Cargar el perfil de Instagram
        profile = instaloader.Profile.from_username(loader.context, perfil)
        current_followees = [followee.username for followee in profile.get_followees()]
        previous_followees = load_data().get(perfil, [])

        new_followees = set(current_followees) - set(previous_followees)
        removed_followees = set(previous_followees) - set(current_followees)

        if new_followees or removed_followees:
            message = f"📊 Actualización para {perfil}:\n"
            if new_followees:
                message += "📈 Nuevos seguidos:\n" + "\n".join(f"- {u}" for u in new_followees) + "\n\n"
            if removed_followees:
                message += "📉 Seguidos eliminados:\n" + "\n".join(f"- {u}" for u in removed_followees) + "\n\n"
            await application.bot.send_message(chat_id=chat_id, text=message)

        monitoreo = load_data()
        monitoreo[perfil] = current_followees
        save_data(monitoreo)
    except Exception as e:
        await application.bot.send_message(chat_id=chat_id, text=f"Error analizando {perfil}: {e}")

# Configuración principal
if __name__ == '__main__':
    # Iniciar sesión en Instagram antes de ejecutar el bot
    login_instagram()

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Configuración de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("monitorear", monitorear))
    application.add_handler(CommandHandler("listar", listar))

    # Configuración de webhook
    application.run_webhook(
        listen="0.0.0.0",  # Escuchar en todas las interfaces
        port=PORT,          # Puerto de tu servidor
        url_path="/webhook",  # Ruta del webhook
        webhook_url=WEBHOOK_URL  # URL completa del webhook
    )
