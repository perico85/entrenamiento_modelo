import os
import csv
import requests
import json
from datetime import datetime

# Configuración del usuario
api_key = '9cfb71dcf14fbef4af0bb8f86c3d2207'
REQUEST_LIMIT = 75000
headers = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": api_key
}

# Códigos de los países específicos a procesar (ISO Alpha-2)
specific_country_codes = [
    'ES', 'GB', 'DE', 'IT', 'FR', 'AT', 'CH', 'DK', 'NL', 'NO', 'PL', 'PT', 'SE', 'TR'
]

# Ruta del archivo de conteo de solicitudes
requests_count_file = 'requests_count.json'
progress_file = 'h2h_progress.json'  # Archivo para guardar el progreso

# Cargar el conteo de solicitudes desde un archivo
def load_requests_count():
    if os.path.exists(requests_count_file):
        with open(requests_count_file, 'r') as f:
            return json.load(f)
    return {}

# Guardar el conteo de solicitudes en un archivo
def save_requests_count(count_dict):
    with open(requests_count_file, 'w') as f:
        json.dump(count_dict, f, indent=4)

# Función para actualizar el conteo de solicitudes
def update_request_count(api_key):
    today = datetime.now().strftime('%Y-%m-%d')
    counts = load_requests_count()
    if api_key not in counts:
        counts[api_key] = {'date': today, 'count': 0}
    
    if counts[api_key]['date'] != today:
        counts[api_key] = {'date': today, 'count': 0}
    
    if counts[api_key]['count'] >= REQUEST_LIMIT:
        print(f"Límite de solicitudes alcanzado para el día {today}.")
        save_requests_count(counts)
        return False

    counts[api_key]['count'] += 1
    save_requests_count(counts)
    return True

# Cargar el estado de progreso
def load_progress():
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {}

# Guardar el estado de progreso
def save_progress(progress_dict):
    with open(progress_file, 'w') as f:
        json.dump(progress_dict, f, indent=4)

# Función para cargar los IDs de las ligas y los equipos por país
def load_league_and_team_ids(season, country_code):
    league_team_data = []
    league_teams_file = os.path.join(str(season), f'league_teams_{season}.csv')
    
    if not os.path.exists(league_teams_file):
        print(f"Error: No se encontró el archivo {league_teams_file}")
        return league_team_data

    with open(league_teams_file, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Saltar la cabecera
        for row in reader:
            league_id = row[0]
            if row[5] == country_code:  # Filtrar por el código del país
                teams_file = os.path.join(str(season), country_code, f'teams_{league_id}.csv')
                if os.path.exists(teams_file):
                    with open(teams_file, mode='r', encoding='utf-8') as team_csvfile:
                        team_reader = csv.DictReader(team_csvfile)
                        for team_row in team_reader:
                            team_id = team_row['team_id']
                            league_team_data.append((team_id, league_id, country_code))
                else:
                    print(f"Advertencia: No se encontró el archivo {teams_file}")
    
    return league_team_data

# Función para obtener datos Head to Head entre dos equipos
def get_head_to_head(api_key, team1_id, team2_id, league_id, season, last=5):
    if not update_request_count(api_key):
        return []  # Si se alcanzó el límite, retorna vacío
    
    url = f"https://v3.football.api-sports.io/fixtures/headtohead"
    params = {
        "h2h": f"{team1_id}-{team2_id}",
        "league": league_id,
        "season": season,
        "last": last
    }
    response = requests.get(url, headers=headers, params=params)
    
    try:
        data = response.json()
        if isinstance(data, dict) and 'response' in data:
            return data['response']
        else:
            print(f"Advertencia: Respuesta inesperada de la API para h2h {team1_id}-{team2_id}.")
            return []
    except ValueError:
        print(f"Error: No se pudo decodificar la respuesta JSON para h2h {team1_id}-{team2_id}.")
        return []

# Función para determinar el resultado del partido
def determine_result(home_goals, away_goals):
    if home_goals > away_goals:
        return '1'
    elif home_goals < away_goals:
        return '2'
    else:
        return 'X'

# Función para guardar los datos Head to Head en un archivo CSV
def save_head_to_head_to_csv(h2h_data, filepath):
    if not h2h_data:
        print("Advertencia: No hay datos de Head to Head para guardar.")
        return

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'fixture_id', 'date', 'venue_name', 'venue_city', 'status',
            'home_team_id', 'home_team_name', 'away_team_id', 'away_team_name',
            'home_goals', 'away_goals', 'halftime_home', 'halftime_away', 'fulltime_home', 'fulltime_away',
            'result'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for match in h2h_data:
            home_goals = match['goals']['home']
            away_goals = match['goals']['away']
            result = determine_result(home_goals, away_goals)

            writer.writerow({
                'fixture_id': match['fixture']['id'],
                'date': match['fixture']['date'],
                'venue_name': match['fixture']['venue']['name'],
                'venue_city': match['fixture']['venue']['city'],
                'status': match['fixture']['status']['long'],
                'home_team_id': match['teams']['home']['id'],
                'home_team_name': match['teams']['home']['name'],
                'away_team_id': match['teams']['away']['id'],
                'away_team_name': match['teams']['away']['name'],
                'home_goals': home_goals,
                'away_goals': away_goals,
                'halftime_home': match['score']['halftime']['home'],
                'halftime_away': match['score']['halftime']['away'],
                'fulltime_home': match['score']['fulltime']['home'],
                'fulltime_away': match['score']['fulltime']['away'],
                'result': result
            })

# Función principal para procesar los datos Head to Head
def process_head_to_head(api_key, season, country_code):
    progress = load_progress()

    league_team_data = load_league_and_team_ids(season, country_code)

    if not league_team_data:
        print(f"No se encontraron datos de equipos para {country_code} en la temporada {season}.")
        return

    processed_pairs = set()

    for team1_id, league_id, country_code in league_team_data:
        for team2_id, _, _ in league_team_data:
            if team1_id != team2_id and (team2_id, team1_id) not in processed_pairs:
                
                # Verificar si ya fue procesado
                progress_key = f"{season}_{country_code}_{league_id}_{team1_id}_{team2_id}"
                if progress.get(progress_key):
                    print(f"H2H entre {team1_id} y {team2_id} en la liga {league_id} para la temporada {season} ya fue procesado. Saltando.")
                    continue

                print(f"Procesando H2H entre {team1_id} y {team2_id} en la liga {league_id} para la temporada {season}")

                h2h_data = get_head_to_head(api_key, team1_id, team2_id, league_id, season, last=5)

                output_dir = os.path.join(str(season), country_code, 'H2H', str(team1_id))
                os.makedirs(output_dir, exist_ok=True)
                h2h_filepath = os.path.join(output_dir, f'h2h_{team1_id}_{team2_id}.csv')

                save_head_to_head_to_csv(h2h_data, h2h_filepath)

                processed_pairs.add((team1_id, team2_id))

                # Guardar el progreso
                progress[progress_key] = True
                save_progress(progress)

# Ejecución del script principal
if __name__ == "__main__":
    current_year = datetime.now().year
    seasons = [current_year - i for i in range(5, -1, -1)]  # Últimos 5 años más el actual

    for season in seasons:
        for country_code in specific_country_codes:
            process_head_to_head(api_key, season, country_code)
    
    print(f"Total de llamadas a la API realizadas: {load_requests_count().get(api_key, {}).get('count', 0)}")

