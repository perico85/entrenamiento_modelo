import requests
import csv
import os
import json
from datetime import datetime

# Configuración del usuario
api_key = '9cfb71dcf14fbef4af0bb8f86c3d2207'
REQUEST_LIMIT = 75000
headers = {
    'x-rapidapi-host': 'v3.football.api-sports.io',
    'x-rapidapi-key': api_key
}

# Ruta del archivo de conteo de solicitudes
requests_count_file = 'requests_count.json'
progress_file = 'lineups_progress.json'  # Archivo para guardar el progreso

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

# Actualizar el conteo de solicitudes
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

# Función para crear directorio si no existe
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Función para obtener alineaciones (lineups) para un fixture específico
def fetch_lineups(fixture_id):
    if not update_request_count(api_key):
        return {}  # Si se alcanzó el límite, retorna vacío

    url = f"https://v3.football.api-sports.io/fixtures/lineups?fixture={fixture_id}"
    response = requests.get(url, headers=headers)
    return response.json()

# Función para guardar las alineaciones en un archivo CSV
def save_lineups_to_csv(lineups, file_name):
    with open(file_name, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Escribir encabezados
        writer.writerow([
            'team_id', 'team_name', 'formation', 'player_id', 'player_name', 'player_number',
            'player_position', 'player_grid', 'is_substitute', 'coach_id', 'coach_name'
        ])
        
        for team in lineups:
            team_id = team['team']['id']
            team_name = team['team']['name']
            formation = team['formation']
            coach_id = team['coach']['id']
            coach_name = team['coach']['name']
            
            # Escribir titulares (start XI)
            for player in team['startXI']:
                writer.writerow([
                    team_id, team_name, formation,
                    player['player']['id'], player['player']['name'], player['player']['number'],
                    player['player']['pos'], player['player']['grid'], False,
                    coach_id, coach_name
                ])
            
            # Escribir suplentes (substitutes)
            for player in team['substitutes']:
                writer.writerow([
                    team_id, team_name, formation,
                    player['player']['id'], player['player']['name'], player['player']['number'],
                    player['player']['pos'], player['player']['grid'], True,
                    coach_id, coach_name
                ])

# Función para leer los valores de league_id y league_name desde el archivo CSV
def load_leagues_from_csv(season, country_code):
    leagues = []
    league_teams_file = os.path.join(str(season), f'league_teams_{season}.csv')
    
    if not os.path.exists(league_teams_file):
        print(f"Error: No se encontró el archivo {league_teams_file}")
        return leagues
    
    with open(league_teams_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['country_code'] == country_code:
                leagues.append((row['league_id'], row['league_name']))
    
    return leagues

# Función principal para procesar los fixtures y generar archivos de alineaciones
def process_fixtures_for_lineups(season, country_code):
    progress = load_progress()
    leagues = load_leagues_from_csv(season, country_code)
    
    if not leagues:
        print(f"No se encontraron ligas para el país {country_code} en la temporada {season}.")
        return
    
    for league_id, league_name in leagues:
        fixtures_file = os.path.join(str(season), country_code, 'Fixtures', league_id, f'fixtures_{league_name}_{season}.csv')
        
        if not os.path.exists(fixtures_file):
            print(f"Error: No se encontró el archivo {fixtures_file}")
            continue
        
        with open(fixtures_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                fixture_id = row['fixture_id']

                # Verificar si ya fue procesado
                progress_key = f"{season}_{country_code}_{league_id}_{fixture_id}"
                if progress.get(progress_key):
                    print(f"Fixture {fixture_id} en la liga {league_name} (ID: {league_id}) para la temporada {season} ya fue procesado. Saltando.")
                    continue

                print(f"Procesando fixture {fixture_id}")
                
                lineups_data = fetch_lineups(fixture_id)
                
                if 'response' in lineups_data and lineups_data['response']:
                    lineups = lineups_data['response']
                    output_dir = os.path.join(str(season), country_code, 'Lineups', league_id)
                    create_directory(output_dir)
                    output_file_name = os.path.join(output_dir, f'lineups_{fixture_id}.csv')
                    save_lineups_to_csv(lineups, output_file_name)
                    print(f"Alineaciones guardadas en {output_file_name}")

                    # Guardar el progreso
                    progress[progress_key] = True
                    save_progress(progress)
                else:
                    print(f"No se encontraron alineaciones para el fixture {fixture_id}")

# Ejecución del script principal
if __name__ == "__main__":
    current_year = datetime.now().year
    seasons = [current_year - i for i in range(5, -1, -1)]  # Últimos 5 años más el actual
    specific_country_codes = [
        'ES', 'GB', 'DE', 'IT', 'FR', 'AT', 'CH', 'DK', 'NL', 'NO', 'PL', 'PT', 'SE', 'TR'
    ]
    
    for season in seasons:
        for country_code in specific_country_codes:
            process_fixtures_for_lineups(season, country_code)
    
    print(f"Total de llamadas a la API realizadas: {load_requests_count().get(api_key, {}).get('count', 0)}")

