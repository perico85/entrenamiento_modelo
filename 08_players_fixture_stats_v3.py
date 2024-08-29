import os
import csv
import json
import requests
from datetime import datetime

# Configuración del usuario
api_key = '9cfb71dcf14fbef4af0bb8f86c3d2207'
REQUEST_LIMIT = 75000

# Códigos de los países específicos a procesar (ISO Alpha-2)
specific_country_codes = [
    'ES', 'GB', 'DE', 'IT', 'FR', 'AT', 'CH', 'DK', 'NL', 'NO', 'PL', 'PT', 'SE', 'TR'
]

# Rutas de archivos
requests_count_file = 'requests_count.json'
progress_file = 'players_progress.json'

# Cargar el conteo de solicitudes desde un archivo
def load_requests_count():
    if os.path.exists(requests_count_file):
        with open(requests_count_file, 'r') as f:
            return json.load(f)
    return {}

# Guardar el conteo de solicitudes en un archivo
def save_requests_count(count_dict):
    with open(requests_count_file, 'w') as f):
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

# Función para obtener las estadísticas de jugadores de un fixture
def get_players_statistics(api_key, fixture_id):
    if not update_request_count(api_key):
        return []  # Si se alcanzó el límite, retorna vacío

    url = f"https://v3.football.api-sports.io/fixtures/players"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": api_key
    }
    params = {"fixture": fixture_id}
    response = requests.get(url, headers=headers, params=params)
    try:
        data = response.json()
        if isinstance(data, dict) and 'response' in data:
            return data['response']
        else:
            print(f"Advertencia: Respuesta inesperada de la API para el fixture {fixture_id}.")
            return []
    except ValueError:
        print(f"Error: No se pudo decodificar la respuesta JSON para el fixture {fixture_id}.")
        return []

# Función para guardar estadísticas de jugadores en un archivo CSV
def save_players_statistics_to_csv(players_stats, season, country_code, fixture_id):
    if not players_stats:
        print("Advertencia: No hay estadísticas de jugadores para guardar.")
        return

    output_dir = os.path.join(str(season), country_code, 'Players_fixture_stats', str(fixture_id))
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f'{fixture_id}_players_stats.csv')

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'team_id', 'team_name', 'player_id', 'player_name', 'position', 'minutes', 'rating', 
            'captain', 'substitute', 'offsides', 'total_shots', 'shots_on', 'goals', 'conceded', 'assists', 'saves',
            'passes_total', 'passes_key', 'passes_accuracy', 'tackles_total', 'blocks', 'interceptions', 
            'duels_total', 'duels_won', 'dribbles_attempts', 'dribbles_success', 'fouls_drawn', 
            'fouls_committed', 'yellow_cards', 'red_cards', 'penalty_won', 'penalty_committed', 'penalty_scored', 
            'penalty_missed', 'penalty_saved'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for team_data in players_stats:
            team_id = team_data['team']['id']
            team_name = team_data['team']['name']
            for player in team_data['players']:
                player_data = player['player']
                stats = player['statistics'][0]
                writer.writerow({
                    'team_id': team_id,
                    'team_name': team_name,
                    'player_id': player_data['id'],
                    'player_name': player_data['name'],
                    'position': stats['games']['position'],
                    'minutes': stats['games']['minutes'],
                    'rating': stats['games']['rating'],
                    'captain': stats['games']['captain'],
                    'substitute': stats['games']['substitute'],
                    'offsides': stats['offsides'],
                    'total_shots': stats['shots']['total'],
                    'shots_on': stats['shots']['on'],
                    'goals': stats['goals']['total'],
                    'conceded': stats['goals']['conceded'],
                    'assists': stats['goals']['assists'],
                    'saves': stats['goals']['saves'],
                    'passes_total': stats['passes']['total'],
                    'passes_key': stats['passes']['key'],
                    'passes_accuracy': stats['passes']['accuracy'],
                    'tackles_total': stats['tackles']['total'],
                    'blocks': stats['tackles']['blocks'],
                    'interceptions': stats['tackles']['interceptions'],
                    'duels_total': stats['duels']['total'],
                    'duels_won': stats['duels']['won'],
                    'dribbles_attempts': stats['dribbles']['attempts'],
                    'dribbles_success': stats['dribbles']['success'],
                    'fouls_drawn': stats['fouls']['drawn'],
                    'fouls_committed': stats['fouls']['committed'],
                    'yellow_cards': stats['cards']['yellow'],
                    'red_cards': stats['cards']['red'],
                    'penalty_won': stats['penalty']['won'],
                    'penalty_committed': stats['penalty']['commited'],
                    'penalty_scored': stats['penalty']['scored'],
                    'penalty_missed': stats['penalty']['missed'],
                    'penalty_saved': stats['penalty']['saved'],
                })

# Función para cargar los IDs de las ligas por país
def load_league_ids_by_country(season, country_code):
    file_path = os.path.join(str(season), f'league_teams_{season}.csv')
    league_ids = []
    
    if not os.path.exists(file_path):
        print(f"Error: No se encontró el archivo {file_path}")
        return league_ids

    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Saltar la cabecera
        for row in reader:
            if row[5] == country_code:  # La sexta columna es country_code
                league_ids.append((row[0], row[2]))  # La primera columna es league_id, la tercera es league_name

    return league_ids

# Función para cargar fixtures desde un archivo CSV
def load_fixtures_from_csv(filepath):
    fixtures = []
    if not os.path.exists(filepath):
        print(f"Error: No se encontró el archivo {filepath}")
        return fixtures

    with open(filepath, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            fixtures.append(row)
    return fixtures

# Función principal para procesar las estadísticas de jugadores de cada fixture
def process_players_statistics(api_key, season, country_code):
    progress = load_progress()
    
    leagues = load_league_ids_by_country(season, country_code)
    
    if not leagues:
        print(f"No se encontraron ligas para el código de país {country_code} en la temporada {season}.")
        return
    
    for league_id, league_name in leagues:
        fixtures_file = os.path.join(str(season), country_code, 'Fixtures', league_id, f'fixtures_{league_name}_{season}.csv')
        fixtures = load_fixtures_from_csv(fixtures_file)
        
        if not fixtures:
            print(f"No se encontraron fixtures en {fixtures_file}.")
            continue

        for fixture in fixtures:
            fixture_id = fixture['fixture_id']

            # Verificar si ya fue procesado
            progress_key = f"{season}_{country_code}_{league_id}_{fixture_id}_players"
            if progress.get(progress_key):
                print(f"Fixture {fixture_id} en la liga {league_name} (ID: {league_id}) para la temporada {season} ya fue procesado. Saltando.")
                continue

            print(f"Procesando estadísticas de jugadores para el fixture {fixture_id}")
            
            players_stats = get_players_statistics(api_key, fixture_id)
            if not players_stats:
                print(f"Advertencia: No se obtuvieron estadísticas de jugadores para el fixture {fixture_id}.")
                continue

            save_players_statistics_to_csv(players_stats, season, country_code, fixture_id)
            print(f"Estadísticas de jugadores guardadas para el fixture {fixture_id}")

            # Guardar el progreso
            progress[progress_key] = True
            save_progress(progress)

# Ejecución del script principal
if __name__ == "__main__":
    current_year = datetime.now().year
    seasons = [current_year - i for i in range(5, -1, -1)]  # Últimos 5 años más el actual

    for season in seasons:
        for country_code in specific_country_codes:
            process_players_statistics(api_key, season, country_code)

