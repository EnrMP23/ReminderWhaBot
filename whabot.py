import logging
import instaloader
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import os

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Credenciales de Instagram
INSTAGRAM_USER = "@enriquemaynez"
INSTAGRAM_PASS = "EnriqueMP2002"

# Configuración del bot de Telegram
TELEGRAM_TOKEN = "7680282118:AAHAu9QhhahvyRCflOt3u2rNhlcH88e5hoM"
WEBHOOK_URL = "https://reminderwhabot-vsig.onrender.com/webhook"

# Archivo donde se almacenan los datos de los perfiles monitoreados
DATA_FILE = "monitoreo_data.json"

# Instaloader para interactuar con Instagram
loader = instaloader.Instaloader()

# Función para guardar los datos en un archivo JSON
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# Función para cargar los datos desde el archivo JSON
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

# Función para iniciar sesión en Instagram
def login_instagram():
    try:
        # Intenta cargar la sesión guardada
        loader.load_session(INSTAGRAM_USER)
        logger.info("Sesión de Instagram cargada correctamente.")
    except FileNotFoundError:
        logger.info("No se encontró sesión guardada, iniciando sesión con usuario y contraseña...")
        loader.context.log("Iniciando sesión...")
        loader.login(INSTAGRAM_USER, INSTAGRAM_PASS)  # Inicia sesión con usuario y contraseña
        loader.save_session(INSTAGRAM_USER)  # Guarda la sesión para futuras ejecuciones
        logger.info("Sesión guardada correctamente.")

# Comando para monitorear un perfil
async def monitorear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        perfil = context.args[0]  # Obtener el nombre del perfil desde el comando
        chat_id = update.message.chat_id  # Obtener el chat_id del usuario

        # Enviar mensaje de confirmación
        await update.message.reply_text(f"Monitoreando el perfil de Instagram: {perfil}")

        # Llamar a la función para analizar ese perfil
        await analizar_perfil(perfil, chat_id, context.application)
    else:
        await update.message.reply_text("Por favor, ingresa el nombre del perfil a monitorear después del comando.\nEjemplo: /monitorear johndoe")

# Función para analizar los seguidores de un perfil
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

        # Guardar la lista actualizada de seguidos
        monitoreo = load_data()
        monitoreo[perfil] = current_followees
        save_data(monitoreo)
    except Exception as e:
        await application.bot.send_message(chat_id=chat_id, text=f"Error al analizar {perfil}: {e}")

# Función principal que arranca el bot
def main():
    login_instagram()  # Inicia sesión en Instagram al arrancar

    # Crea la aplicación de Telegram
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Agrega los manejadores de comandos
    application.add_handler(CommandHandler("monitorear", monitorear))

    # Inicia el webhook del bot
    application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

if __name__ == '__main__':
    main()
