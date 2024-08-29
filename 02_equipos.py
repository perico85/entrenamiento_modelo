import requests
import csv
import os
import pandas as pd
from datetime import datetime

# Tu clave de API
api_key = '9cfb71dcf14fbef4af0bb8f86c3d2207'
headers = {
    'x-rapidapi-host': 'v3.football.api-sports.io',
    'x-rapidapi-key': api_key
}

# Función para crear directorio si no existe
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Función para obtener equipos por ID de liga
def fetch_teams_by_league(league_id, season):
    url = f"https://v3.football.api-sports.io/teams?league={league_id}&season={season}"
    response = requests.get(url, headers=headers)
    return response.json()

# Función para guardar equipos en un archivo CSV
def save_teams_to_csv(teams, file_name):
    fieldnames = ['team_id', 'team_name', 'team_code', 'team_country', 'team_founded', 'team_national', 'team_logo', 
                  'venue_id', 'venue_name', 'venue_address', 'venue_city', 'venue_capacity', 'venue_surface', 'venue_image']
    
    with open(file_name, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for team in teams:
            row = {
                'team_id': team['team']['id'],
                'team_name': team['team']['name'],
                'team_code': team['team'].get('code'),
                'team_country': team['team']['country'],
                'team_founded': team['team'].get('founded'),
                'team_national': team['team']['national'],
                'team_logo': team['team']['logo'],
                'venue_id': team['venue'].get('id'),
                'venue_name': team['venue'].get('name'),
                'venue_address': team['venue'].get('address'),
                'venue_city': team['venue'].get('city'),
                'venue_capacity': team['venue'].get('capacity'),
                'venue_surface': team['venue'].get('surface'),
                'venue_image': team['venue'].get('image')
            }
            writer.writerow(row)

# Función principal
def main():
    current_year = datetime.now().year
    seasons = [current_year - i for i in range(5, -1, -1)]  # Últimos 5 años más el actual

    # Leer el archivo de ligas
    for season in seasons:
        leagues_file = os.path.join(str(season), f"league_teams_{season}.csv")
        leagues_df = pd.read_csv(leagues_file)

        for _, row in leagues_df.iterrows():
            league_id = row['league_id']
            league_name = row['league_name'].replace(' ', '_')
            country_code = row['country_code']
            
            # Crear un directorio para el país
            country_dir = os.path.join(str(season), country_code)
            create_directory(country_dir)
            
            # Obtener los equipos de la liga
            data = fetch_teams_by_league(league_id, season)
            teams = data['response']

            if teams:
                # Guardar los equipos en un archivo CSV dentro del directorio del país
                teams_file_name = os.path.join(country_dir, f"teams_{league_id}.csv")
                save_teams_to_csv(teams, teams_file_name)
                print(f"Equipos de la liga {league_name} de la temporada {season} guardados en {teams_file_name}")

if __name__ == "__main__":
    main()

