import os
import json
import instaloader
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram import Update

# Inicializa Instaloader
loader = instaloader.Instaloader()

# Archivo para guardar perfiles a monitorear
MONITOREO_FILE = "monitoreo.json"

# Funciones de ayuda para manejar datos
def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}

def save_data(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Comando /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "¡Hola! Soy un bot para monitorear los seguidos de perfiles en Instagram.\n"
        "Comandos disponibles:\n"
        "- /monitorear <perfil>: Agrega un perfil para monitorear.\n"
        "- /analizar <perfil>: Analiza manualmente un perfil.\n"
        "- /listar: Muestra los perfiles monitoreados."
    )

# Comando /monitorear
async def monitorear(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        await update.message.reply_text("Por favor, proporciona un nombre de perfil. Ejemplo: /monitorear @instagram")
        return

    perfil = context.args[0]
    monitoreo = load_data(MONITOREO_FILE)
    if perfil in monitoreo:
        await update.message.reply_text(f"El perfil {perfil} ya está siendo monitoreado.")
    else:
        monitoreo[perfil] = []
        save_data(MONITOREO_FILE, monitoreo)
        await update.message.reply_text(f"El perfil {perfil} ha sido agregado al monitoreo.")

# Comando /listar
async def listar(update: Update, context: CallbackContext):
    monitoreo = load_data(MONITOREO_FILE)
    if not monitoreo:
        await update.message.reply_text("No hay perfiles en monitoreo.")
    else:
        perfiles = "\n".join(monitoreo.keys())
        await update.message.reply_text(f"Perfiles monitoreados:\n{perfiles}")

# Analizar cambios en un perfil
async def analizar_perfil(perfil, chat_id, bot):
    data_file = f"{perfil}_seguimientos.json"
    try:
        # Iniciar sesión en Instagram
        loader.login("@enriquemaynez", "EnriqueMP2002")

        # Obtener el perfil
        profile = instaloader.Profile.from_username(loader.context, perfil)
        current_followees = [followee.username for followee in profile.get_followees()]

        # Cargar datos previos
        previous_followees = load_data(data_file)

        # Detectar cambios
        new_followees = set(current_followees) - set(previous_followees)
        removed_followees = set(previous_followees) - set(current_followees)

        # Construir mensaje
        message = f"📊 Actualización para {perfil}:\n"
        if new_followees:
            message += "📈 Nuevos seguidos:\n" + "\n".join(f"- {u}" for u in new_followees) + "\n\n"
        if removed_followees:
            message += "📉 Seguidos eliminados:\n" + "\n".join(f"- {u}" for u in removed_followees) + "\n\n"

        # Enviar mensaje si hay cambios
        if new_followees or removed_followees:
            await bot.send_message(chat_id=chat_id, text=message)

        # Guardar la lista actual
        save_data(data_file, current_followees)
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text=f"Hubo un error al analizar {perfil}: {e}")

# Monitoreo automático
async def monitoreo_automatico(context: CallbackContext):
    monitoreo = load_data(MONITOREO_FILE)
    for perfil in monitoreo.keys():
        await analizar_perfil(perfil, context.job.context['chat_id'], context.bot)

async def main():
    # Token del Bot de Telegram
    token = "7163814190:AAG7Ntm7GdlqpZFBcrTSgpjPVbLPTP-kkTo"

    # Inicializa la aplicación
    application = Application.builder().token(token).build()

    # Maneja comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("monitorear", monitorear))
    application.add_handler(CommandHandler("listar", listar))

    # Agregar monitoreo periódico
    job_queue = application.job_queue
    job_queue.run_repeating(monitoreo_automatico, interval=3600, first=10, context={"chat_id": "5602833071"})

    # Ejecutar webhook
    application.run_webhook(
        listen="0.0.0.0",  # Escucha en todas las interfaces
        port=8443,         # Puerto donde escuchará el webhook
        url_path="/webhook",  # Ruta para el webhook
        webhook_url="https://reminderwhabot-vsig.onrender.com/webhook"  # La URL completa donde el webhook será accesible
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
