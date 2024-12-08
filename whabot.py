import os
import json
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
import instaloader

# Configuración de logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7680282118:AAHAu9QhhahvyRCflOt3u2rNhlcH88e5hoM")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")
PORT = int(os.getenv("PORT", "8443"))

# Instaloader para la interacción con Instagram
loader = instaloader.Instaloader()

# Función para iniciar sesión en Instagram
def instagram_login():
    try:
        username = os.getenv("INSTAGRAM_USERNAME", "@enriquemaynez")
        password = os.getenv("INSTAGRAM_PASSWORD", "EnriqueMP2002")

        logger.info(f"Iniciando sesión en Instagram con el usuario {username}")
        loader.login(username, password)
        logger.info("Sesión iniciada correctamente en Instagram.")
    except Exception as e:
        logger.error(f"Error al iniciar sesión en Instagram: {e}")

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.message.chat_id  # Obtener el chat ID del usuario
        logger.info(f"Comando /start recibido de chat ID {chat_id}")
        
        # Responder con un mensaje
        await update.message.reply_text(
            f"¡Hola! Soy un bot para monitorear los seguidos de perfiles en Instagram.\n"
            f"Tu chat ID es: {chat_id}\n"
            "Comandos disponibles:\n"
            "- /monitorear <perfil>: Agrega un perfil para monitorear.\n"
            "- /listar: Muestra los perfiles monitoreados."
        )
    except Exception as e:
        logger.error(f"Error al procesar /start: {e}")
        await update.message.reply_text("Ocurrió un error al procesar el comando /start.")

# Comando /monitorear
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

# Comando /listar
async def listar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    monitoreo = load_data()
    if not monitoreo:
        await update.message.reply_text("No hay perfiles en monitoreo.")
    else:
        perfiles = "\n".join(monitoreo.keys())
        await update.message.reply_text(f"Perfiles monitoreados:\n{perfiles}")

# Funciones para cargar y guardar datos
MONITOREO_FILE = "monitoreo.json"

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

# Función para analizar el perfil de Instagram
async def analizar_perfil(perfil, chat_id, application) -> None:
    try:
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

# Función principal para la configuración del bot y webhook
def main() -> None:
    try:
        # Iniciar sesión en Instagram
        instagram_login()

        # Crea la aplicación de Telegram con el token de acceso
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        # Agrega los manejadores de comandos
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("monitorear", monitorear))
        application.add_handler(CommandHandler("listar", listar))

        # Configura el webhook
        logger.info(f"Iniciando webhook en {WEBHOOK_URL} en el puerto {PORT}")
        application.run_webhook(
            listen="0.0.0.0",  # Escuchar en todas las interfaces
            port=PORT,  # Puerto configurado
            webhook_url=WEBHOOK_URL,  # URL del webhook
        )
    except Exception as e:
        logger.error(f"Error al iniciar el bot: {e}")

if __name__ == "__main__":
    main()
