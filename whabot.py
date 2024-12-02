import requests
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import io
import os
from datetime import datetime
import pytz
import numpy as np
from difflib import get_close_matches
from math import pi
import logging

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Variables de configuración
API_KEY = os.getenv("SPORTSDATAIO_DATA_API_KEY", "205bca4e7d76426ea69a738d9ef11641")  # API key
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4LF4Zxi3J4_RnKd26u1M")  # Reemplaza con tu token real
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")  # URL pública de tu webhook
season = 2024

BASE_URL = "https://api.sportsdata.io/v3/nfl/scores/json/CurrentSeason?key=205bca4e7d76426ea69a738d9ef11641"
STANDINGS_URL = "https://api.sportsdata.io/v3/nfl/scores/json/Standings/2024"
TEAMS_URL = "https://api.sportsdata.io/v3/nfl/scores/json/Teams"

# Umbrales
confidence_threshold = 0.55
close_threshold = 0.10

# Funciones auxiliares
def get_nfl_matches(season='2024'):
    headers = {'Ocp-Apim-Subscription-Key': API_KEY}
    # Endpoint correcto para obtener los partidos por temporada
    response = requests.get(f"https://api.sportsdata.io/v3/nfl/scores/json/GamesBySeason/2024", headers=headers)

    if response.status_code == 200:
        return response.json()  # Devuelve la lista de partidos
    else:
        logging.error(f"Error al obtener partidos de la NFL: {response.status_code}")
        return []

def get_team_stats_nfl(team_id):
    headers = {'Ocp-Apim-Subscription-Key': API_KEY}
    # Endpoint correcto para obtener estadísticas de un equipo
    response = requests.get(f"https://api.sportsdata.io/v3/nfl/scores/json/Team/{team_id}", headers=headers)

    if response.status_code == 200:
        return response.json()  # Devuelve las estadísticas del equipo
    else:
        logging.error(f"Error al obtener estadísticas del equipo {team_id}: {response.status_code}")
        return {}

def analyze_local_visitor_performance(team_id, is_home=True):
    last_5_games = get_last_5_games_nfl(team_id)
    relevant_games = [game for game in last_5_games if (is_home and game['IsHome']) or (not is_home and not game['IsHome'])]

    points_scored = sum(game['Score'] for game in relevant_games)
    points_allowed = sum(game['OpponentScore'] for game in relevant_games)
    wins = sum(1 for game in relevant_games if game['Win'])

    games_count = len(relevant_games)
    return points_scored / max(games_count, 1), points_allowed / max(games_count, 1), wins

def predict_nfl_result(home_team_id, away_team_id, home_team_name, away_team_name):
    home_stats = get_team_stats_nfl(home_team_id)
    away_stats = get_team_stats_nfl(away_team_id)

    if not home_stats or not away_stats:
        return "No se pueden calcular las predicciones debido a datos insuficientes."

    # Rendimiento reciente
    home_recent_avg, home_allowed_avg, home_wins = analyze_local_visitor_performance(home_team_id, is_home=True)
    away_recent_avg, away_allowed_avg, away_wins = analyze_local_visitor_performance(away_team_id, is_home=False)

    # Factores de ventaja local y diferencial
    home_field_advantage = 3
    point_difference = home_stats.get('TotalPoints', 0) - away_stats.get('TotalPoints', 0)

    # Goles estimados
    estimated_home_score = (home_recent_avg + away_allowed_avg) / 2 + home_field_advantage + point_difference * 0.1
    estimated_away_score = (away_recent_avg + home_allowed_avg) / 2 - point_difference * 0.1

    # Cálculo de probabilidades
    total_points = estimated_home_score + estimated_away_score
    home_win_probability = (estimated_home_score / total_points) * 100 if total_points > 0 else 50
    away_win_probability = (estimated_away_score / total_points) * 100 if total_points > 0 else 50

    # Predicción
    if abs(home_win_probability - away_win_probability) < close_threshold * 100:
        result = "Juego cerrado, difícil de predecir"
    elif home_win_probability > away_win_probability:
        result = f"{home_team_name} tiene más probabilidades de ganar"
    else:
        result = f"{away_team_name} tiene más probabilidades de ganar"

    return result, home_win_probability, away_win_probability

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Obteniendo información de los partidos...")
    matches = get_nfl_matches()

    if matches:
        message_text = "¡Hola! Aquí tienes la lista de partidos disponibles:\n\n"
        for match in matches:
            home_team = match['HomeTeam']
            away_team = match['AwayTeam']
            utc_date = datetime.strptime(match['Date'], '%Y-%m-%dT%H:%M:%S')
            local_date = utc_date.replace(tzinfo=pytz.utc).astimezone(SONORA_TZ)
            formatted_date = local_date.strftime('Fecha: %d/%m/%Y Hora: %H:%M (Hora Sonora)')

            message_text += f"🔹 {match['GameKey']}: {home_team} vs {away_team} - {formatted_date}\n"

        message_text += "Usa /predict <GameKey> para predecir el resultado de un partido."
        await update.message.reply_text(message_text)
    else:
        await update.message.reply_text("🥱 No se encontraron partidos disponibles. Intenta más tarde.")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Por favor proporciona un ID de partido válido.")
        return

    game_key = context.args[0]
    matches = get_nfl_matches()
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

# Definir los headers para la solicitud
headers = {'Ocp-Apim-Subscription-Key': API_KEY}

# Hacer la solicitud con los headers definidos
response = requests.get(f"https://api.sportsdata.io/v3/nfl/scores/json/GamesBySeason/2024", headers=headers)

if response.status_code == 200:
    print("Datos obtenidos correctamente.")
    # Procesar la respuesta aquí
else:
    print(f"Error al obtener los partidos: {response.status_code}")

response = requests.get(f"https://api.sportsdata.io/v3/nfl/scores/json/GamesBySeason/2024", headers=headers)
if response.status_code == 404:
    logging.error(f"Endpoint no encontrado para la temporada {season}. Revisa la URL y los parámetros.")
elif response.status_code != 200:
    logging.error(f"Error en la API: {response.status_code} - {response.text}")


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
