import os
import json
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackContext,
    ContextTypes,
    JobQueue,
)
import instaloader

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7680282118:AAHAu9QhhahvyRCflOt3u2rNhlcH88e5hoM")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")
PORT = int(os.getenv("PORT", "8443"))
MONITOREO_FILE = "monitoreo.json"
INSTAGRAM_USER = os.getenv("INSTAGRAM_USER", "@enriquemaynez")
INSTAGRAM_PASS = os.getenv("INSTAGRAM_PASS", "EnriqueMP2002")

# Configurar el logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instaloader para interacción con Instagram
loader = instaloader.Instaloader()

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

# Función de login en Instagram
def login_instagram():
    try:
        loader.load_session(INSTAGRAM_USER)  # Intentamos cargar la sesión guardada
    except FileNotFoundError:
        logger.info("No se encontró sesión guardada, iniciando sesión con usuario y contraseña...")
        loader.context.log("Cargando nueva sesión de Instagram...")
        loader.login(INSTAGRAM_USER, INSTAGRAM_PASS)  # Iniciar sesión con usuario y contraseña
        loader.save_session(INSTAGRAM_USER)  # Guardar la sesión para futuras ejecuciones

# Función para analizar los perfiles y sus seguidores
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

        # Actualizar los seguidores en el archivo
        monitoreo = load_data()
        monitoreo[perfil] = current_followees
        save_data(monitoreo)
    except Exception as e:
        await application.bot.send_message(chat_id=chat_id, text=f"Error analizando {perfil}: {e}")

# Función de monitoreo automático (revisar perfiles cada cierto tiempo)
async def monitoreo_automatico(context: CallbackContext) -> None:
    chat_id = context.job.context
    monitoreo = load_data()

    # Analizar todos los perfiles monitoreados
    for perfil in monitoreo.keys():
        try:
            await analizar_perfil(perfil, chat_id, context.application)
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"Error monitoreando {perfil}: {e}")

# Comandos del bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Comando /start recibido de chat ID {chat_id}")
    await update.message.reply_text(
        f"¡Hola! Soy un bot para monitorear los seguidos de perfiles en Instagram.\n"
        f"Tu chat ID es: {chat_id}\n"
        "Comandos disponibles:\n"
        "- /monitorear <perfil>: Agrega un perfil para monitorear.\n"
        "- /listar: Muestra los perfiles monitoreados."
    )

async def monitorear(update: Update, context: CallbackContext) -> None:
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

async def listar(update: Update, context: CallbackContext) -> None:
    monitoreo = load_data()
    if not monitoreo:
        await update.message.reply_text("No hay perfiles en monitoreo.")
    else:
        perfiles = "\n".join(monitoreo.keys())
        await update.message.reply_text(f"Perfiles monitoreados:\n{perfiles}")

# Función principal que inicializa el bot
def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Configuración de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("monitorear", monitorear))
    application.add_handler(CommandHandler("listar", listar))

    # Agregar trabajo programado para monitoreo automático (cada 1 hora)
    job_queue = application.job_queue
    job_queue.run_repeating(monitoreo_automatico, interval=10, first=0)  # Ejecutar cada hora

    # Iniciar el bot con webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    login_instagram()  # Inicia sesión en Instagram al arrancar
    main()  # Iniciar el bot
