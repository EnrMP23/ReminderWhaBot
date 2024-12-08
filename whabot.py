import os
import json
import asyncio
import instaloader
from telegram import Update
from telegram.ext import Application, CommandHandler, JobQueue, CallbackContext

# Archivo para guardar perfiles a monitorear
MONITOREO_FILE = "monitoreo.json"

# Inicializa Instaloader
loader = instaloader.Instaloader()

# Funciones de ayuda para manejar datos
def load_data():
    if os.path.exists(MONITOREO_FILE):
        with open(MONITOREO_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_data(data):
    with open(MONITOREO_FILE, 'w') as file:
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
    monitoreo = load_data()  # Cargar datos de los perfiles monitoreados

    if perfil in monitoreo:
        await update.message.reply_text(f"El perfil {perfil} ya está siendo monitoreado.")
    else:
        monitoreo[perfil] = []  # Agregar el perfil al monitoreo con una lista vacía de seguidos
        save_data(monitoreo)  # Guardar los cambios en el archivo JSON
        await update.message.reply_text(f"El perfil {perfil} ha sido agregado al monitoreo.")

# Comando /listar
async def listar(update: Update, context: CallbackContext):
    monitoreo = load_data()  # Cargar datos de los perfiles monitoreados

    if not monitoreo:
        await update.message.reply_text("No hay perfiles en monitoreo.")
    else:
        perfiles = "\n".join(monitoreo.keys())  # Obtener los nombres de los perfiles monitoreados
        await update.message.reply_text(f"Perfiles monitoreados:\n{perfiles}")

# Función para analizar cambios en un perfil de Instagram
async def analizar_perfil(perfil, chat_id, updater):
    data_file = f"{perfil}_seguimientos.json"
    try:
        # Iniciar sesión en Instagram (agrega tus credenciales aquí)
        loader.login("@enriquemaynez", "EnriqueMP2002")  # Aquí debes poner tus credenciales de Instagram

        # Obtener el perfil de Instagram
        profile = instaloader.Profile.from_username(loader.context, perfil)
        current_followees = [followee.username for followee in profile.get_followees()]

        # Cargar los seguidos previos
        previous_followees = load_data().get(perfil, [])

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
            await updater.bot.send_message(chat_id=chat_id, text=message)

        # Guardar la lista actual de seguidos
        monitoreo = load_data()
        monitoreo[perfil] = current_followees
        save_data(monitoreo)
    except Exception as e:
        await updater.bot.send_message(chat_id=chat_id, text=f"Hubo un error al analizar {perfil}: {e}")

# Monitoreo automático
async def monitoreo_automatico(context: CallbackContext):
    chat_id = context.job.context['chat_id']  # Obtener el chat_id desde el contexto
    monitoreo = load_data()  # Cargar perfiles monitoreados
    for perfil in monitoreo.keys():
        await analizar_perfil(perfil, chat_id, context.application)

# Configuración del bot
async def main():
    token = "7163814190:AAG7Ntm7GdlqpZFBcrTSgpjPVbLPTP-kkTo"  # Reemplaza esto con tu token real del bot
    application = Application.builder().token(token).build()

    # Configura JobQueue
    job_queue = application.job_queue

    # Maneja comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("monitorear", monitorear))
    application.add_handler(CommandHandler("listar", listar))

    # URL del webhook
    webhook_url = "https://reminderwhabot-vsig.onrender.com/webhook"  # Reemplaza esto con la URL de tu app en Render

    # Configura el webhook
    await application.bot.set_webhook(webhook_url)

    # Agregar monitoreo periódico usando JobQueue
    job_queue.run_repeating(
        monitoreo_automatico,
        interval=3600,  # Ejecutar cada 1 hora
        first=10,  # Esperar 10 segundos antes de la primera ejecución
    )

    # Ejecuta el bot usando webhook
    await application.run_webhook(
        listen="0.0.0.0",  # Escucha en todas las interfaces
        port=8443,         # Puerto donde escuchará el webhook
        url_path="/webhook",  # Ruta para el webhook
        webhook_url=webhook_url  # La URL completa donde el webhook será accesible
    )

if __name__ == "__main__":
    asyncio.run(main())
