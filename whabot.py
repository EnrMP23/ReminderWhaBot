import os
import json
import asyncio
import instaloader
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackContext

# Configuración inicial
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7163814190:AAGJGgmpBcfbhrWG_87Sr87oOT0aTdYA5kI")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")
MONITOREO_FILE = "monitoreo.json"
CHAT_ID = 5602833071  # ID de chat de Telegram para recibir notificaciones

# Inicializa Instaloader
loader = instaloader.Instaloader()

# Funciones de ayuda para manejar datos
def load_data():
    """Carga los datos de perfiles monitoreados desde un archivo JSON."""
    try:
        if os.path.exists(MONITOREO_FILE):
            with open(MONITOREO_FILE, 'r') as file:
                return json.load(file)
    except json.JSONDecodeError:
        return {}
    return {}

def save_data(data):
    """Guarda los datos de perfiles monitoreados en un archivo JSON."""
    with open(MONITOREO_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Comando /start
async def start(update: Update, context: CallbackContext):
    """Muestra un mensaje de bienvenida con los comandos disponibles."""
    await update.message.reply_text(
        "¡Hola! Soy un bot para monitorear los seguidos de perfiles en Instagram.\n"
        "Comandos disponibles:\n"
        "- /monitorear <perfil>: Agrega un perfil para monitorear.\n"
        "- /listar: Muestra los perfiles monitoreados.\n"
    )

# Comando /monitorear
async def monitorear(update: Update, context: CallbackContext):
    """Agrega un perfil para monitorear."""
    if len(context.args) != 1:
        await update.message.reply_text("Por favor, proporciona un nombre de perfil. Ejemplo: /monitorear @instagram")
        return

    perfil = context.args[0]
    monitoreo = load_data()

    if perfil in monitoreo:
        await update.message.reply_text(f"El perfil {perfil} ya está siendo monitoreado.")
    else:
        monitoreo[perfil] = []  # Agregar el perfil al monitoreo con una lista vacía de seguidos
        save_data(monitoreo)
        await update.message.reply_text(f"El perfil {perfil} ha sido agregado al monitoreo.")

# Comando /listar
async def listar(update: Update, context: CallbackContext):
    """Muestra todos los perfiles actualmente monitoreados."""
    monitoreo = load_data()

    if not monitoreo:
        await update.message.reply_text("No hay perfiles en monitoreo.")
    else:
        perfiles = "\n".join(monitoreo.keys())
        await update.message.reply_text(f"Perfiles monitoreados:\n{perfiles}")

# Análisis del perfil
async def analizar_perfil(perfil, chat_id, bot):
    """Analiza los cambios en los seguidos de un perfil de Instagram."""
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
            await bot.send_message(chat_id=chat_id, text=message)

        monitoreo = load_data()
        monitoreo[perfil] = current_followees
        save_data(monitoreo)
    except instaloader.exceptions.ProfileNotExistsException:
        await bot.send_message(chat_id=chat_id, text=f"El perfil {perfil} no existe.")
    except instaloader.exceptions.LoginRequiredException:
        await bot.send_message(chat_id=chat_id, text=f"No se pudo acceder al perfil {perfil}. Verifica las credenciales.")
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"Error analizando {perfil}: {e}")

# Monitoreo automático
async def monitoreo_automatico(context: CallbackContext):
    """Monitorea automáticamente los perfiles a intervalos regulares."""
    monitoreo = load_data()
    for perfil in monitoreo.keys():
        await analizar_perfil(perfil, CHAT_ID, context.bot)

# Configuración principal del bot
async def main():
    # Configurar la aplicación
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Manejar comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("monitorear", monitorear))
    application.add_handler(CommandHandler("listar", listar))

    # Configuración del Webhook
    port = int(os.getenv("PORT", "8443"))
    await application.bot.set_webhook(url=WEBHOOK_URL)

    # Configurar monitoreo automático
    job_queue = application.job_queue
    job_queue.run_repeating(
        monitoreo_automatico,
        interval=3600,  # Cada hora
        first=10  # Primer monitoreo en 10 segundos
    )

    # Ejecutar aplicación en Webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_TOKEN
    )

if __name__ == "__main__":
    asyncio.run(main())
