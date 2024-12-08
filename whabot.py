import os
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
import instaloader

# Configuración
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7163814190:AAGJGgmpBcfbhrWG_87Sr87oOT0aTdYA5kI")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")
PORT = int(os.getenv("PORT", "8443"))
MONITOREO_FILE = "monitoreo.json"
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "@enriquemaynez")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "EnriqueMP2002")
SESSION_FILE = "insta_session"

# Instaloader para interacción con Instagram
loader = instaloader.Instaloader()

# Iniciar sesión en Instagram
def login_instagram():
    if os.path.exists(SESSION_FILE):
        loader.load_session_from_file(INSTAGRAM_USERNAME, SESSION_FILE)
    else:
        loader.context.log("Iniciando sesión en Instagram...")
        loader.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        loader.save_session_to_file(SESSION_FILE)

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

# Comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "¡Hola! Soy un bot para monitorear los seguidos de perfiles en Instagram.\n"
        "Comandos disponibles:\n"
        "- /monitorear <perfil>: Agrega un perfil para monitorear.\n"
        "- /listar: Muestra los perfiles monitoreados."
    )

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
def main() -> None:
    # Primero, loguearse en Instagram
    login_instagram()

    # Creación de la aplicación
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Configuración de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("monitorear", monitorear))
    application.add_handler(CommandHandler("listar", listar))

    # Configuración de webhook
    application.run_webhook(
        listen="0.0.0.0",  # Escucha en todas las interfaces
        port=PORT,         # Puerto configurado
        webhook_url=WEBHOOK_URL,  # URL del webhook
    )

if __name__ == "__main__":
    main()
