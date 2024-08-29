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
progress_file = 'progress.json'

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

# Función para cargar el estado de progreso
def load_progress():
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {}

# Función para guardar el estado de progreso
def save_progress(progress_dict):
    with open(progress_file, 'w') as f:
        json.dump(progress_dict, f, indent=4)

# Función para obtener las estadísticas de un fixture
def get_fixture_statistics(api_key, fixture_id):
    if not update_request_count(api_key):
        return None  # Si se alcanzó el límite, retorna None

    url = f"https://v3.football.api-sports.io/fixtures/statistics"
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
            return None
    except ValueError:
        print(f"Error: No se pudo decodificar la respuesta JSON para el fixture {fixture_id}.")
        return None

# Función para obtener la información del fixture, incluyendo los goles
def get_fixture_information(api_key, fixture_id):
    if not update_request_count(api_key):
        return None  # Si se alcanzó el límite, retorna None

    url = f"https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": api_key
    }
    params = {"id": fixture_id}
    response = requests.get(url, headers=headers, params=params)
    try:
        data = response.json()
        if isinstance(data, dict) and 'response' in data and data['response']:
            return data['response'][0]
        else:
            print(f"Advertencia: Respuesta inesperada de la API para el fixture {fixture_id}.")
            return None
    except ValueError:
        print(f"Error: No se pudo decodificar la respuesta JSON para el fixture {fixture_id}.")
        return None

# Función para guardar estadísticas en un archivo CSV
def save_statistics_to_csv(statistics, filepath):
    if not statistics:
        print("Advertencia: No hay estadísticas para guardar.")
        return

    file_exists = os.path.isfile(filepath)

    with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'fixture_id', 'home_team_id', 'home_team_name', 'away_team_id', 'away_team_name',
            'result', 'home_team_ft_goals', 'away_team_ft_goals',
            'home_team_ht_goals', 'away_team_ht_goals',
            'home_team_Shots_on_Goal', 'away_team_Shots_on_Goal',
            'home_team_Shots_off_Goal', 'away_team_Shots_off_Goal',
            'home_team_Total_Shots', 'away_team_Total_Shots',
            'home_team_Blocked_Shots', 'away_team_Blocked_Shots',
            'home_team_Shots_insidebox', 'away_team_Shots_insidebox',
            'home_team_Shots_outsidebox', 'away_team_Shots_outsidebox',
            'home_team_Fouls', 'away_team_Fouls',
            'home_team_Corner_Kicks', 'away_team_Corner_Kicks',
            'home_team_Offsides', 'away_team_Offsides',
            'home_team_Ball_Possession', 'away_team_Ball_Possession',
            'home_team_Yellow_Cards', 'away_team_Yellow_Cards',
            'home_team_Red_Cards', 'away_team_Red_Cards',
            'home_team_Goalkeeper_Saves', 'away_team_Goalkeeper_Saves',
            'home_team_Total_passes', 'away_team_Total_passes',
            'home_team_Passes_accurate', 'away_team_Passes_accurate',
            'home_team_Passes_%', 'away_team_Passes_%'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()

        for stat in statistics:
            writer.writerow(stat)

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

# Función principal para procesar los fixtures y obtener las estadísticas
def process_statistics_for_fixtures(api_key, season, country_code):
    progress = load_progress()

    # Reanudar desde el último progreso guardado
    last_processed_league = progress.get(f"{season}_{country_code}", None)
    if last_processed_league:
        last_league_id = last_processed_league['league_id']
        leagues = load_league_ids_by_country(season, country_code)
        leagues = [(league_id, league_name) for league_id, league_name in leagues if league_id > last_league_id]
    else:
        leagues = load_league_ids_by_country(season, country_code)
    
    if not leagues:
        print(f"No se encontraron ligas para el código de país {country_code} en la temporada {season}.")
        return

    for league_id, league_name in leagues:
        output_dir = os.path.join(str(season), country_code, 'Fixtures_stats', league_id)
        stats_filepath = os.path.join(output_dir, f'stats_{league_id}_{season}.csv')
        
        # Saltar si el archivo ya existe
        if os.path.exists(stats_filepath):
            print(f"Archivo existente encontrado: {stats_filepath}. Saltando procesamiento.")
            continue

        print(f"Procesando estadísticas para la liga {league_name} (ID: {league_id}) para la temporada {season}")

        fixtures_file = os.path.join(str(season), country_code, 'Fixtures', league_id, f'fixtures_{league_name}_{season}.csv')
        fixtures = load_fixtures_from_csv(fixtures_file)
        
        if not fixtures:
            print(f"No se encontraron fixtures en {fixtures_file}.")
            continue

        statistics = []

        for fixture in fixtures:
            fixture_id = fixture['fixture_id']

            stats = get_fixture_statistics(api_key, fixture_id)
            if stats is None:
                # Si se alcanzó el límite, guardar el progreso y salir
                progress[f"{season}_{country_code}"] = {
                    'season': season,
                    'country_code': country_code,
                    'league_id': league_id,
                    'fixture_id': fixture_id
                }
                save_progress(progress)
                print(f"Límite alcanzado. Progreso guardado en la liga {league_name} (ID: {league_id}) para el fixture {fixture_id}.")
                return

            if not stats or len(stats) < 2:
                print(f"Advertencia: No se obtuvieron estadísticas para el fixture {fixture_id}.")
                continue

            home_stats = {stat['type']: stat['value'] for stat in stats[0]['statistics']}
            away_stats = {stat['type']: stat['value'] for stat in stats[1]['statistics']}

            # Obtener resultado final y al descanso
            fixture_info = get_fixture_information(api_key, fixture_id)
            if fixture_info:
                home_team_ft_goals = fixture_info['goals']['home']
                away_team_ft_goals = fixture_info['goals']['away']

                home_team_ht_goals = fixture_info['score']['halftime']['home']
                away_team_ht_goals = fixture_info['score']['halftime']['away']

                # Determinar el resultado del partido
                if home_team_ft_goals > away_team_ft_goals:
                    result = '1'
                elif home_team_ft_goals < away_team_ft_goals:
                    result = '2'
                else:
                    result = 'X'
            else:
                home_team_ft_goals = "N/A"
                away_team_ft_goals = "N/A"
                home_team_ht_goals = "N/A"
                away_team_ht_goals = "N/A"
                result = "N/A"

            statistics.append({
                'fixture_id': fixture_id,
                'home_team_id': fixture['home_team_id'],
                'home_team_name': fixture['home_team_name'],
                'away_team_id': fixture['away_team_id'],
                'away_team_name': fixture['away_team_name'],
                'result': result,
                'home_team_ft_goals': home_team_ft_goals,
                'away_team_ft_goals': away_team_ft_goals,
                'home_team_ht_goals': home_team_ht_goals,
                'away_team_ht_goals': away_team_ht_goals,
                'home_team_Shots_on_Goal': home_stats.get('Shots on Goal'),
                'away_team_Shots_on_Goal': away_stats.get('Shots on Goal'),
                'home_team_Shots_off_Goal': home_stats.get('Shots off Goal'),
                'away_team_Shots_off_Goal': away_stats.get('Shots off Goal'),
                'home_team_Total_Shots': home_stats.get('Total Shots'),
                'away_team_Total_Shots': away_stats.get('Total Shots'),
                'home_team_Blocked_Shots': home_stats.get('Blocked Shots'),
                'away_team_Blocked_Shots': away_stats.get('Blocked Shots'),
                'home_team_Shots_insidebox': home_stats.get('Shots insidebox'),
                'away_team_Shots_insidebox': away_stats.get('Shots insidebox'),
                'home_team_Shots_outsidebox': home_stats.get('Shots outsidebox'),
                'away_team_Shots_outsidebox': away_stats.get('Shots outsidebox'),
                'home_team_Fouls': home_stats.get('Fouls'),
                'away_team_Fouls': away_stats.get('Fouls'),
                'home_team_Corner_Kicks': home_stats.get('Corner Kicks'),
                'away_team_Corner_Kicks': away_stats.get('Corner Kicks'),
                'home_team_Offsides': home_stats.get('Offsides'),
                'away_team_Offsides': away_stats.get('Offsides'),
                'home_team_Ball_Possession': home_stats.get('Ball Possession'),
                'away_team_Ball_Possession': away_stats.get('Ball Possession'),
                'home_team_Yellow_Cards': home_stats.get('Yellow Cards'),
                'away_team_Yellow_Cards': away_stats.get('Yellow Cards'),
                'home_team_Red_Cards': home_stats.get('Red Cards'),
                'away_team_Red_Cards': away_stats.get('Red Cards'),
                'home_team_Goalkeeper_Saves': home_stats.get('Goalkeeper Saves'),
                'away_team_Goalkeeper_Saves': away_stats.get('Goalkeeper Saves'),
                'home_team_Total_passes': home_stats.get('Total passes'),
                'away_team_Total_passes': away_stats.get('Total passes'),
                'home_team_Passes_accurate': home_stats.get('Passes accurate'),
                'away_team_Passes_accurate': away_stats.get('Passes accurate'),
                'home_team_Passes_%': home_stats.get('Passes %'),
                'away_team_Passes_%': away_stats.get('Passes %')
            })

        os.makedirs(output_dir, exist_ok=True)
        save_statistics_to_csv(statistics, stats_filepath)
        print(f"Estadísticas guardadas en {stats_filepath}")

        # Actualizar el estado de progreso con el último archivo generado
        progress[f"{season}_{country_code}"] = {
            'season': season,
            'country_code': country_code,
            'league_id': league_id,
            'fixture_id': fixture_id
        }
        save_progress(progress)

# Ejecución del script principal
if __name__ == "__main__":
    current_year = datetime.now().year
    seasons = [2021, 2022, 2023, 2024]

    progress = load_progress()

    for season in seasons:
        for country_code in specific_country_codes:
            process_statistics_for_fixtures(api_key, season, country_code)

