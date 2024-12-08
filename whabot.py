import os
import json
import instaloader
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, JobQueue, CallbackContext
import logging
import asyncio

# Configuración básica
TELEGRAM_TOKEN = os.getenv("7163814190:AAGJGgmpBcfbhrWG_87Sr87oOT0aTdYA5kI")
WEBHOOK_URL = os.getenv("https://reminderwhabot-vsig.onrender.com/webhook")
MONITOREO_FILE = "monitoreo.json"
chat_id = os.getenv("CHAT_ID", "5602833071")  # Mejor no hardcodear el chat_id
INSTAGRAM_USER = os.getenv("@enriquemaynez")
INSTAGRAM_PASSWORD = os.getenv("EnriqueMP2002")

# Configuración de logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa Instaloader
loader = instaloader.Instaloader()

# Funciones de ayuda para manejar datos
def load_data():
    """Carga los perfiles monitoreados desde el archivo JSON."""
    if os.path.exists(MONITOREO_FILE):
        try:
            with open(MONITOREO_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            logger.error("Error al leer el archivo JSON.")
    return {}

def save_data(data):
    """Guarda los datos de monitoreo en el archivo JSON."""
    with open(MONITOREO_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Comando /start
async def start(update: Update, context: CallbackContext):
    """Comando /start para el bot."""
    message = (
        "¡Hola! Soy un bot para monitorear los seguidos de perfiles en Instagram.\n"
        "Comandos disponibles:\n"
        "- /monitorear <perfil>: Agrega un perfil para monitorear.\n"
        "- /analizar <perfil>: Analiza manualmente un perfil.\n"
        "- /listar: Muestra los perfiles monitoreados."
    )
    await update.message.reply_text(message)

# Comando /monitorear
async def monitorear(update: Update, context: CallbackContext):
    """Comando /monitorear para agregar perfiles al monitoreo."""
    if len(context.args) != 1:
        await update.message.reply_text("Por favor, proporciona un nombre de perfil. Ejemplo: /monitorear @instagram")
        return

    perfil = context.args[0]
    monitoreo = load_data()

    if perfil in monitoreo:
        await update.message.reply_text(f"El perfil {perfil} ya está siendo monitoreado.")
    else:
        monitoreo[perfil] = []  # Agregar perfil al monitoreo con lista vacía
        save_data(monitoreo)
        await update.message.reply_text(f"El perfil {perfil} ha sido agregado al monitoreo.")

# Comando /listar
async def listar(update: Update, context: CallbackContext):
    """Comando /listar para mostrar los perfiles monitoreados."""
    monitoreo = load_data()

    if not monitoreo:
        await update.message.reply_text("No hay perfiles en monitoreo.")
    else:
        perfiles = "\n".join(monitoreo.keys())
        await update.message.reply_text(f"Perfiles monitoreados:\n{perfiles}")

# Función para analizar cambios en un perfil de Instagram
async def analizar_perfil(perfil, chat_id, updater):
    """Analiza los cambios en un perfil de Instagram y envía una actualización."""
    try:
        # Login en Instagram
        loader.login(INSTAGRAM_USER, INSTAGRAM_PASSWORD)

        profile = instaloader.Profile.from_username(loader.context, perfil)
        current_followees = [followee.username for followee in profile.get_followees()]

        monitoreo = load_data()
        previous_followees = monitoreo.get(perfil, [])

        # Identificar nuevos y eliminados seguidos
        new_followees = set(current_followees) - set(previous_followees)
        removed_followees = set(previous_followees) - set(current_followees)

        if new_followees or removed_followees:
            message = f"📊 Actualización para {perfil}:\n"
            if new_followees:
                message += "📈 Nuevos seguidos:\n" + "\n".join(f"- {u}" for u in new_followees) + "\n\n"
            if removed_followees:
                message += "📉 Seguidos eliminados:\n" + "\n".join(f"- {u}" for u in removed_followees) + "\n\n"
            await updater.bot.send_message(chat_id=chat_id, text=message)

        # Actualizar datos monitoreados
        monitoreo[perfil] = current_followees
        save_data(monitoreo)
    except instaloader.exceptions.ProfileNotExistsException:
        logger.error(f"El perfil {perfil} no existe.")
        await updater.bot.send_message(chat_id=chat_id, text=f"El perfil {perfil} no existe.")
    except instaloader.exceptions.LoginRequiredException:
        logger.error(f"No se pudo acceder al perfil {perfil}. Verifica las credenciales.")
        await updater.bot.send_message(chat_id=chat_id, text="No se pudo acceder a Instagram. Verifica las credenciales.")
    except Exception as e:
        logger.exception(f"Error analizando {perfil}: {e}")
        await updater.bot.send_message(chat_id=chat_id, text=f"Error analizando {perfil}: {e}")

# Monitoreo automático
async def monitoreo_automatico(context: CallbackContext):
    """Realiza el monitoreo automático de los perfiles."""
    chat_id = context.job.context['chat_id']
    monitoreo = load_data()

    for perfil in monitoreo.keys():
        try:
            await analizar_perfil(perfil, chat_id, context.application)
        except Exception as e:
            logger.error(f"Error monitoreando {perfil}: {e}")
            await context.bot.send_message(chat_id=chat_id, text=f"Error monitoreando {perfil}: {e}")

# Configuración del bot
async def main():
    """Función principal para ejecutar el bot."""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Configura JobQueue
    job_queue = application.job_queue

    # Maneja comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("monitorear", monitorear))
    application.add_handler(CommandHandler("listar", listar))

    # Agregar monitoreo periódico usando JobQueue
    job_queue.run_repeating(
        monitoreo_automatico,
        interval=3600,  # Ejecutar cada 1 hora
        first=10,  # Esperar 10 segundos antes de la primera ejecución
        context={"chat_id": chat_id}
    )

    # Iniciar el webhook
    await application.run_webhook(
        listen="0.0.0.0",  # Escuchar en todas las interfaces
        port=8443,  # Puerto para el webhook
        url_path="/webhook",  # Path para el webhook
        webhook_url=WEBHOOK_URL  # URL completa del webhook
    )

if __name__ == '__main__':
    asyncio.run(main())
