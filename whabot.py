import requests
import logging
import os
from datetime import datetime, timedelta
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Variables de configuración
API_KEY = os.getenv("SPORTSDATAIO_DATA_API_KEY", "205bca4e7d76426ea69a738d9ef11641")  # API key
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4LF4Zxi3J4_RnKd26u1M")  # Token de tu bot de Telegram
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")  # URL pública de tu webhook
season = 2024

# URL base para los endpoints de la API
BASE_URL = f"https://api.sportsdata.io/v3/nfl/scores/json/GamesBySeason/{season}"
STANDINGS_URL = f"https://api.sportsdata.io/v3/nfl/scores/json/Standings/{season}"
TEAMS_URL = "https://api.sportsdata.io/v3/nfl/scores/json/Teams"

# Definir los headers para la solicitud
headers = {'Ocp-Apim-Subscription-Key': API_KEY}

# Función para obtener los partidos del día siguiente
def get_nfl_matches_next_day():
    """Obtiene los partidos del siguiente día."""
    # Obtener la fecha de mañana
    next_day = datetime.today() + timedelta(days=1)
    next_day_str = next_day.strftime('%Y-%m-%d')  # Formatear la fecha como YYYY-MM-DD

    # Log the constructed URL for debugging
    logging.info(f"Fetching games for the next day: {next_day_str}")

    # Solicitar los partidos para el día siguiente
    url = f"https://api.sportsdata.io/v3/nfl/scores/json/GamesByDate/{next_day_str}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()  # Devuelve los partidos para el día siguiente
    else:
        logging.error(f"Error al obtener partidos para el día siguiente: {response.status_code}")
        return []




# Función para el comando /games
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Obteniendo información de los partidos...")
    matches = get_nfl_matches_next_day()  # Obtener partidos para el siguiente día

    if matches:
        message_text = "¡Hola! Aquí tienes la lista de partidos del siguiente día:\n\n"
        for match in matches:
            home_team = match['HomeTeam']
            away_team = match['AwayTeam']
            utc_date = datetime.strptime(match['Date'], '%Y-%m-%dT%H:%M:%S')
            local_date = utc_date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('America/Hermosillo'))  # Hora Sonora
            formatted_date = local_date.strftime('Fecha: %d/%m/%Y Hora: %H:%M (Hora Sonora)')

            message_text += f"🔹 {match['GameKey']}: {home_team} vs {away_team} - {formatted_date}\n"

        message_text += "Usa /predict <GameKey> para predecir el resultado de un partido."
        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("🥱 No se encontraron partidos disponibles. Intenta más tarde.")

# Función para el comando /predict
async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Por favor proporciona un ID de partido válido.")
        return

    game_key = context.args[0]
    matches = get_nfl_matches_next_day()  # Obtener partidos para el siguiente día
    match = next((m for m in matches if m['GameKey'] == game_key), None)

    if match:
        home_team = match['HomeTeam']
        away_team = match['AwayTeam']
        home_team_id = home_team
        away_team_id = away_team

        result, home_prob, away_prob = predict_nfl_result(home_team_id, away_team_id, home_team, away_team)
        await update.message.reply_text(f"🔰 Predicción para el partido {home_team} vs {away_team}:\n{result}")
        await update.message.reply_text(f"🏆 Probabilidad de victoria para {home_team}: {home_prob:.2f}%")
        await update.message.reply_text(f"🏆 Probabilidad de victoria para {away_team}: {away_prob:.2f}%")
    else:
        await update.message.reply_text("❌ Partido no encontrado.")

# Configurar y ejecutar el bot de Telegram
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("games", start))
    application.add_handler(CommandHandler("predict", predict))

    application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path="/webhook",
        webhook_url=WEBHOOK_URL
    )

    logging.info("BOT FUNCIONANDO")
