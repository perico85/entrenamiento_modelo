import requests
import csv
import os
import pandas as pd
import json
from datetime import datetime

# Tu clave de API
api_key = '9cfb71dcf14fbef4af0bb8f86c3d2207'
headers = {
    'x-rapidapi-host': 'v3.football.api-sports.io',
    'x-rapidapi-key': api_key
}

# Códigos de los países específicos a procesar (ISO Alpha-2)
specific_country_codes = [
    'ES', 'GB', 'DE', 'IT', 'FR', 'AT', 'CH', 'DK', 'NL', 'NO', 'PL', 'PT', 'SE', 'TR'
]

# Límite de solicitudes diarias
daily_limit = 7500
solicitudes_realizadas = 0

# Función para crear directorio si no existe
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Función para obtener estadísticas por equipo
def fetch_team_statistics(team_id, league_id, season):
    global solicitudes_realizadas
    if solicitudes_realizadas >= daily_limit - 50:
        print("Límite de solicitudes alcanzado, guardando progreso...")
        return None
    
    url = f"https://v3.football.api-sports.io/teams/statistics?team={team_id}&league={league_id}&season={season}"
    print(f"Solicitando estadísticas del equipo {team_id} en la liga {league_id} para la temporada {season}")
    response = requests.get(url, headers=headers)
    solicitudes_realizadas += 1
    data = response.json()
    print(f"Datos obtenidos para el equipo {team_id}: {data}")
    return data

# Función para guardar estadísticas de equipo en un archivo CSV
def save_team_statistics_to_csv(stats, file_name):
    # Aplanar los datos de tarjetas amarillas y rojas
    cards_data = {}
    for card_type in ['yellow', 'red']:
        for minute_range in ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90', '91-105', '106-120']:
            total_key = f'{card_type}_cards_{minute_range}_total'
            percentage_key = f'{card_type}_cards_{minute_range}_percentage'
            minute_stats = stats['cards'].get(card_type, {}).get(minute_range, {})
            cards_data[total_key] = minute_stats.get('total', None)
            cards_data[percentage_key] = minute_stats.get('percentage', None)

    # Estructurar las filas de datos
    row = {
        'team_id': stats['team']['id'],
        'team_name': stats['team']['name'],
        'league_id': stats['league']['id'],
        'league_name': stats['league']['name'],
        'form': stats['form'],
        'played_home': stats['fixtures']['played']['home'],
        'played_away': stats['fixtures']['played']['away'],
        'played_total': stats['fixtures']['played']['total'],
        'wins_home': stats['fixtures']['wins']['home'],
        'wins_away': stats['fixtures']['wins']['away'],
        'wins_total': stats['fixtures']['wins']['total'],
        'draws_home': stats['fixtures']['draws']['home'],
        'draws_away': stats['fixtures']['draws']['away'],
        'draws_total': stats['fixtures']['draws']['total'],
        'loses_home': stats['fixtures']['loses']['home'],
        'loses_away': stats['fixtures']['loses']['away'],
        'loses_total': stats['fixtures']['loses']['total'],
        'goals_for_home': stats['goals']['for']['total']['home'],
        'goals_for_away': stats['goals']['for']['total']['away'],
        'goals_for_total': stats['goals']['for']['total']['total'],
        'goals_against_home': stats['goals']['against']['total']['home'],
        'goals_against_away': stats['goals']['against']['total']['away'],
        'goals_against_total': stats['goals']['against']['total']['total'],
    }

    # Combinar los datos de tarjetas con los datos generales
    row.update(cards_data)

    # Obtener todos los posibles fieldnames
    all_fieldnames = list(row.keys())

    with open(file_name, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=all_fieldnames)
        writer.writeheader()
        writer.writerow(row)

    print(f"Estadísticas de {row['team_name']} guardadas en {file_name}")

# Función para cargar el progreso
def cargar_progreso(country_code):
    progreso_path = f'progreso_{country_code}.json'
    if os.path.exists(progreso_path):
        with open(progreso_path, 'r') as file:
            return json.load(file)
    else:
        return {}

# Función para guardar el progreso
def guardar_progreso(progreso, country_code):
    progreso_path = f'progreso_{country_code}.json'
    with open(progreso_path, 'w') as file:
        json.dump(progreso, file)

# Función principal
def main():
    global solicitudes_realizadas

    current_year = datetime.now().year
    seasons = [current_year - i for i in range(5, -1, -1)]  # Últimos 5 años más el actual

    for country_code in specific_country_codes:
        progreso = cargar_progreso(country_code)
        last_processed_league = progreso.get('league_name')
        last_processed_team = progreso.get('team_id')

        for season in seasons:
            # Cargar las ligas procesadas del archivo 'league_teams_{season}.csv'
            leagues_file = os.path.join(str(season), f"league_teams_{season}.csv")
            leagues_df = pd.read_csv(leagues_file)

            procesando = False if last_processed_league else True  # Comenzar desde el principio si no hay progreso guardado

            for _, league_row in leagues_df.iterrows():
                if league_row['country_code'] != country_code:
                    continue  # Saltar ligas que no son del país especificado

                league_name = league_row['league_name'].replace(' ', '_')
                league_id = league_row['league_id']

                # Crear directorio para el país y la temporada
                country_dir = os.path.join(str(season), country_code)
                create_directory(country_dir)

                if not procesando and league_name == last_processed_league:
                    procesando = True  # Comenzar desde esta liga si se encontró la última procesada
                
                if procesando:
                    # Obtener los equipos de la liga
                    teams_file = os.path.join(country_dir, f"teams_{league_id}.csv")
                    if os.path.exists(teams_file):
                        teams_df = pd.read_csv(teams_file)
                        for _, team_row in teams_df.iterrows():
                            if last_processed_team and team_row['team_id'] == last_processed_team:
                                last_processed_team = None  # Reanudar desde el próximo equipo
                            
                            if last_processed_team is None:  # Procesar si ya se pasó el último equipo procesado
                                team_id = team_row['team_id']
                                
                                # Obtener estadísticas del equipo
                                stats_data = fetch_team_statistics(team_id, league_id, season)
                                if stats_data is None:  # Límite de solicitudes alcanzado
                                    guardar_progreso({'league_name': league_name, 'team_id': team_id}, country_code)
                                    print(f"Progreso guardado: {league_name} - Team ID: {team_id}")
                                    return

                                if 'response' in stats_data and stats_data['response']:
                                    team_stats = stats_data['response']
                                    
                                    # Guardar estadísticas en un archivo CSV
                                    team_name = team_row['team_name'].replace(' ', '_')
                                    stats_file_name = os.path.join(country_dir, f"{team_id}_statistics.csv")
                                    save_team_statistics_to_csv(team_stats, stats_file_name)
                                    print(f"Estadísticas de {team_name} guardadas en {stats_file_name}")
                                else:
                                    print(f"No se encontraron estadísticas para el equipo {team_id} en la liga {league_id}")

            # Guardar progreso completado si el script finaliza correctamente para este país y temporada
            guardar_progreso({}, country_code)
            print(f"Todas las estadísticas han sido procesadas y guardadas para {country_code} en la temporada {season}.")

if __name__ == "__main__":
    main()

