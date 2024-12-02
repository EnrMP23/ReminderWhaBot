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

# Variables de configuración
API_KEY = os.getenv("SPORTSDATAIO_DATA_API_KEY", "205bca4e7d76426ea69a738d9ef11641")  # API key
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN", "7163814190:AAGzhkR3H3SLBQc4LF4Zxi3J4_RnKd26u1M")  # Reemplaza con tu token real
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://reminderwhabot-vsig.onrender.com/webhook")  # URL pública de tu webhook

BASE_URL = "https://api.sportsdata.io/v3/nfl/scores/json/GamesBySeason/2024"
TEAMS_URL = "https://api.sportsdata.io/v3/nfl/scores/json/Teams"
STANDINGS_URL = "https://api.sportsdata.io/v3/nfl/scores/json/Standings/2024"

confidence_threshold = 0.55  # Umbral de confianza
close_threshold = 0.10  # Umbral para considerar probabilidades cercanas

def get_nfl_matches(season='2024'):
    headers = {'Authorization': f"Bearer {API_KEY}"}
    response = requests.get(f"{BASE_URL}/matches?season={season}", headers=headers)

    if response.status_code == 200:
        return response.json().get('matches', [])
    else:
        print(f"Error al obtener partidos de la NFL. Estado: {response.status_code}")
        return []

def get_team_stats_nfl(team_id):
    headers = {'Authorization': f"Bearer {API_KEY}"}
    response = requests.get(f"{TEAMS_URL}/{team_id}/stats", headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al obtener estadísticas del equipo {team_id}. Estado: {response.status_code}")
        return {}

def get_last_5_games_nfl(team_id):
    headers = {'Authorization': f"Bearer {API_KEY}"}
    response = requests.get(f"{TEAMS_URL}/{team_id}/games?status=FINISHED", headers=headers)

    if response.status_code == 200:
        return response.json().get('games', [])[-5:]
    else:
        print(f"Error al obtener los últimos 5 partidos del equipo {team_id}. Estado: {response.status_code}")
        return []

def analyze_local_visitor_performance(team_id, is_home=True):
    last_5_games = get_last_5_games_nfl(team_id)
    relevant_games = [game for game in last_5_games if (is_home and game['isHome']) or (not is_home and not game['isHome'])]

    points_scored = sum(game['score']['home'] if game['isHome'] else game['score']['away'] for game in relevant_games)
    points_allowed = sum(game['score']['away'] if game['isHome'] else game['score']['home'] for game in relevant_games)
    wins = sum(1 for game in relevant_games if (game['isHome'] and game['score']['home'] > game['score']['away']) or
               (not game['isHome'] and game['score']['away'] > game['score']['home']))

    games_count = len(relevant_games)
    return points_scored / max(games_count, 1), points_allowed / max(games_count, 1), wins
    

def predict_nfl_result(home_team_id, away_team_id, home_team_name, away_team_name):
    home_stats = get_team_stats_nfl(home_team_id)
    away_stats = get_team_stats_nfl(away_team_id)

    if not home_stats or not away_stats:
        return None, None, None, None, None, None  # Solo 6 valores ahora

    # Rendimiento reciente
    home_recent_avg, home_allowed_avg, home_wins = analyze_local_visitor_performance(home_team_id, is_home=True)
    away_recent_avg, away_allowed_avg, away_wins = analyze_local_visitor_performance(away_team_id, is_home=False)

    # Factores de ventaja local y diferencial
    home_field_advantage = 3
    point_difference = home_stats['totalPoints'] - away_stats['totalPoints']

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

    return result, home_win_probability, away_win_probability, home_recent_avg, away_recent_avg, home_stats, away_stats

# Uso
home_team_id = "ID_EQUIPO_LOCAL"
away_team_id = "ID_EQUIPO_VISITANTE"
home_team_name = "EQUIPO_LOCAL"
away_team_name = "EQUIPO_VISITANTE"

resultado, prob_local, prob_visitante, prom_local, prom_visitante, stats_local, stats_visitante, _ = predict_nfl_result(
    home_team_id, away_team_id, home_team_name, away_team_name)


async def start(update: types.Message):
    await update.answer("🔍 Obteniendo información de los partidos...")
    matches = await get_nfl_matches()
    
    if matches:
        message_text = "¡Hola! Aquí tienes la lista de partidos disponibles:\n\n"
        
        for match in matches:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            utc_date_str = match['utcDate']
            
            utc_date = datetime.strptime(utc_date_str, '%Y-%m-%dT%H:%M:%SZ')
            local_date = utc_date.replace(tzinfo=pytz.utc).astimezone(SONORA_TZ)
            formatted_date = local_date.strftime('Fecha: %d/%m/%Y Hora: %H:%M (Hora Sonora)')
            
            message_text += f"🔹{match['id']}: {home_team} vs {away_team} - {formatted_date}\n"
        
        message_text += "Usa /predict <match_id> para predecir el resultado de un partido."
        await update.answer(message_text)
    else:
        await update.answer("🥱 No se encontraron partidos disponibles, intenta más tarde.")

async def predict(update: types.Message):
    await update.answer("📊 Analizando predicción del partido...")

    # Obtener ID del partido desde el comando
    if len(update.text.split()) != 2:
        await update.answer("❌ Por favor proporciona un ID de partido válido.")
        return

    match_id = update.text.split()[1]
    
    match_data = requests.get(f"{BASE_URL}/{match_id}", headers={'Authorization': f"Bearer {API_KEY}"})
    
    if match_data.status_code == 200:
        match_info = match_data.json()
        
        home_team_name = match_info['homeTeam']['name']
        away_team_name = match_info['awayTeam']['name']
        home_team_id = match_info['homeTeam']['id']
        away_team_id = match_info['awayTeam']['id']

        # Obtener predicción
        result, home_win_prob, away_win_prob = await predict_nfl_result(home_team_id, away_team_id, home_team_name, away_team_name)
        
        if result:
            # Responder con el resultado y probabilidades
            await update.answer(f"🔰Predicción para el partido {home_team_name} vs {away_team_name}:\n{result}")
            await update.answer(f"🏆Probabilidad de victoria para {home_team_name}: {home_win_prob:.2f}%")
            await update.answer(f"🏆Probabilidad de victoria para {away_team_name}: {away_win_prob:.2f}%")

            # Crear gráficos y enviarlos
            prob_buf = plot_probabilities(home_win_prob, away_win_prob, home_team_name, away_team_name)
            await update.answer_photo(photo=prob_buf)

            # Grafico de rendimiento de los últimos 5 partidos
            performance_buf = plot_last_5_games(home_team_id, away_team_id, home_team_name, away_team_name)
            await update.answer_photo(photo=performance_buf)
        else:
            await update.answer("No se pudo generar la predicción en este momento.")
    else:
        await update.answer("❌ Error al obtener los datos del partido.")


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
    
    print('BOT FUNCIONANDO')
