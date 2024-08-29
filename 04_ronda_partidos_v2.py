import os
import requests
import csv
import json
from datetime import datetime

# Configuración del usuario
api_key = '9cfb71dcf14fbef4af0bb8f86c3d2207'
REQUEST_LIMIT = 75000

# Códigos de los países específicos a procesar (ISO Alpha-2)
specific_country_codes = [
    'ES', 'GB', 'DE', 'IT', 'FR', 'AT', 'CH', 'DK', 'NL', 'NO', 'PL', 'PT', 'SE', 'TR'
]

# Ruta del archivo de conteo de solicitudes y estado de progreso
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

# Cargar el estado de progreso desde un archivo
def load_progress():
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {}

# Guardar el estado de progreso en un archivo
def save_progress(progress_dict):
    with open(progress_file, 'w') as f:
        json.dump(progress_dict, f, indent=4)

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

# Función para obtener los fixtures de una liga
def get_fixtures(api_key, league_id, season, round=None, date_from=None, date_to=None):
    if not update_request_count(api_key):
        return []  # Si se alcanzó el límite, retorna vacío
    
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": api_key
    }
    params = {
        "league": league_id,
        "season": season
    }
    if round:
        params["round"] = round
    if date_from:
        params["from"] = date_from
    if date_to:
        params["to"] = date_to

    response = requests.get(url, headers=headers, params=params)
    
    try:
        data = response.json()
        if isinstance(data, dict) and 'response' in data:
            return data['response']
        else:
            print("Advertencia: Respuesta inesperada de la API. Se esperaba un diccionario.")
            return []
    except ValueError:
        print("Error: No se pudo decodificar la respuesta JSON.")
        return []

# Función para guardar los fixtures en un archivo CSV
def save_fixtures_to_csv(fixtures, filepath):
    if not fixtures:
        print("Advertencia: No hay fixtures para guardar.")
        return

    file_exists = os.path.isfile(filepath)

    with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'fixture_id', 'league_id', 'season', 'round',
            'home_team_id', 'home_team_name', 'away_team_id', 'away_team_name',
            'date', 'venue_name', 'venue_city', 'referee', 'status'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()

        for fixture in fixtures:
            try:
                writer.writerow({
                    'fixture_id': fixture['fixture']['id'],
                    'league_id': fixture['league']['id'],
                    'season': fixture['league']['season'],
                    'round': fixture['league']['round'],
                    'home_team_id': fixture['teams']['home']['id'],
                    'home_team_name': fixture['teams']['home']['name'],
                    'away_team_id': fixture['teams']['away']['id'],
                    'away_team_name': fixture['teams']['away']['name'],
                    'date': fixture['fixture']['date'],
                    'venue_name': fixture['fixture']['venue']['name'] if fixture['fixture'].get('venue') else None,
                    'venue_city': fixture['fixture']['venue']['city'] if fixture['fixture'].get('venue') else None,
                    'referee': fixture['fixture'].get('referee'),
                    'status': fixture['fixture']['status']['long'] if fixture['fixture'].get('status') else None
                })
            except KeyError as e:
                print(f"Advertencia: Clave no encontrada {e} en fixture {fixture['fixture']['id']}. Ignorando este fixture.")

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

# Función para guardar las rondas en un archivo CSV
def save_rounds_to_csv(rounds, filepath):
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['round'])
        for round in rounds:
            writer.writerow([round])

# Función principal
def main():
    current_year = datetime.now().year
    seasons = [current_year - i for i in range(5, -1, -1)]  # Últimos 5 años más el actual

    # Cargar el estado de progreso
    progress = load_progress()
    
    for season in seasons:
        for country_code in specific_country_codes:
            leagues = load_league_ids_by_country(season, country_code)
            
            if not leagues:
                print(f"No se encontraron ligas para el código de país {country_code} en la temporada {season}.")
                continue
            
            for league_id, league_name in leagues:
                # Verificar el progreso y continuar desde donde se quedó
                if progress.get(f"{season}_{country_code}_{league_id}", {}).get('processed', False):
                    print(f"Ya procesado: Liga {league_name} (ID: {league_id}) para la temporada {season}")
                    continue
                
                print(f"Procesando la liga {league_name} (ID: {league_id}) para la temporada {season}")

                rounds_dir = os.path.join(str(season), country_code, 'Rounds', league_id)
                fixtures_dir = os.path.join(str(season), country_code, 'Fixtures', league_id)
                
                os.makedirs(rounds_dir, exist_ok=True)
                os.makedirs(fixtures_dir, exist_ok=True)

                rounds_file = os.path.join(rounds_dir, f'rounds_{league_name}_{season}.csv')
                
                rounds_url = "https://v3.football.api-sports.io/fixtures/rounds"
                rounds_params = {
                    "league": league_id,
                    "season": season
                }
                headers = {
                    "x-rapidapi-host": "v3.football.api-sports.io",
                    "x-rapidapi-key": api_key
                }
                
                if not update_request_count(api_key):
                    print("Límite de solicitudes alcanzado. Deteniendo ejecución.")
                    save_progress(progress)
                    return
                
                rounds_response = requests.get(rounds_url, headers=headers, params=rounds_params)
                
                try:
                    rounds_data = rounds_response.json()
                    if isinstance(rounds_data, dict) and 'response' in rounds_data:
                        rounds = rounds_data['response']
                    else:
                        print(f"Advertencia: No se pudo obtener las rondas para la liga {league_name}. Usando rondas predeterminadas.")
                        rounds = ["Regular Season - 1", "Regular Season - 2", "Regular Season - 3"]
                except ValueError:
                    print(f"Error: No se pudo decodificar la respuesta JSON para las rondas de la liga {league_name}. Usando rondas predeterminadas.")
                    rounds = ["Regular Season - 1", "Regular Season - 2", "Regular Season - 3"]
                
                save_rounds_to_csv(rounds, rounds_file)

                fixtures_file = os.path.join(fixtures_dir, f'fixtures_{league_name}_{season}.csv')

                for round in rounds:
                    fixtures_data = get_fixtures(api_key, league_id, season, round=round)
                    if fixtures_data:
                        save_fixtures_to_csv(fixtures_data, fixtures_file)
                    else:
                        print(f"Advertencia: No se obtuvieron fixtures para la ronda {round} en la liga {league_name}.")

                progress[f"{season}_{country_code}_{league_id}"] = {'processed': True}
                save_progress(progress)

                print(f"Todas las rondas y fixtures para la liga {league_name} han sido procesados y guardados.")

# Ejecución del script principal
if __name__ == "__main__":
    main()

