import requests
import csv
import os
from datetime import datetime

# Tu clave de API
api_key = '9cfb71dcf14fbef4af0bb8f86c3d2207'
headers = {
    'x-rapidapi-host': 'v3.football.api-sports.io',
    'x-rapidapi-key': api_key
}

# Código de países europeos (ISO Alpha-2)
european_country_codes = [
    'AT', 'CH', 'DE', 'DK', 'ES', 'FR', 'GB', 'IT', 'NL', 'NO', 'PL', 'PT', 'SE', 'TR'
]

# Función para crear directorio si no existe
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Función para obtener las ligas
def fetch_leagues(season):
    url = f"https://v3.football.api-sports.io/leagues?season={season}"
    response = requests.get(url, headers=headers)
    return response.json()

# Función para guardar las ligas en un archivo CSV
def save_leagues_to_csv(leagues, file_name):
    fieldnames = [
        'league_id', 'league_name', 'league_type', 'league_logo', 'country_name', 'country_code', 
        'season_year', 'season_start', 'season_end', 'current', 'coverage_fixtures_events', 
        'coverage_fixtures_lineups', 'coverage_statistics_fixtures', 'coverage_statistics_players', 
        'coverage_standings', 'coverage_players', 'coverage_top_scorers', 'coverage_top_assists', 
        'coverage_top_cards'
    ]
    
    with open(file_name, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for league in leagues:
            for season in league['seasons']:
                # Filtro por los valores True en las columnas especificadas
                if (season['coverage']['fixtures']['events'] and
                    season['coverage']['fixtures']['lineups'] and
                    season['coverage']['fixtures']['statistics_fixtures'] and
                    season['coverage']['fixtures']['statistics_players'] and
                    season['coverage']['standings'] and
                    season['coverage']['players']):
                    
                    row = {
                        'league_id': league['league']['id'],
                        'league_name': league['league']['name'],
                        'league_type': league['league']['type'],
                        'league_logo': league['league']['logo'],
                        'country_name': league['country']['name'],
                        'country_code': league['country']['code'],
                        'season_year': season['year'],
                        'season_start': season['start'],
                        'season_end': season['end'],
                        'current': season['current'],
                        'coverage_fixtures_events': season['coverage']['fixtures']['events'],
                        'coverage_fixtures_lineups': season['coverage']['fixtures']['lineups'],
                        'coverage_statistics_fixtures': season['coverage']['fixtures']['statistics_fixtures'],
                        'coverage_statistics_players': season['coverage']['fixtures']['statistics_players'],
                        'coverage_standings': season['coverage']['standings'],
                        'coverage_players': season['coverage']['players'],
                        'coverage_top_scorers': season['coverage']['top_scorers'],
                        'coverage_top_assists': season['coverage']['top_assists'],
                        'coverage_top_cards': season['coverage']['top_cards']
                    }
                    writer.writerow(row)

# Función principal
def main():
    current_year = datetime.now().year
    seasons = [current_year - i for i in range(5, -1, -1)]  # Últimos 5 años más el actual

    for season in seasons:
        # Directorio base basado en la temporada
        base_dir = os.path.join(os.getcwd(), str(season))
        create_directory(base_dir)
        
        data = fetch_leagues(season)
        leagues = data['response']

        # Filtrar ligas por países europeos
        european_leagues = [
            league for league in leagues 
            if league['country']['code'] in european_country_codes
        ]

        # Ordenar ligas por country_code
        european_leagues_sorted = sorted(european_leagues, key=lambda x: x['country']['code'])

        if european_leagues_sorted:
            # Nombre del archivo de salida
            output_file_name = os.path.join(base_dir, f"league_teams_{season}.csv")
            
            # Guardar las ligas filtradas en un archivo CSV
            save_leagues_to_csv(european_leagues_sorted, output_file_name)
            print(f"Ligas de la temporada {season} guardadas en {output_file_name}")
        else:
            print(f"No se encontraron ligas europeas para la temporada {season}.")

if __name__ == "__main__":
    main()

