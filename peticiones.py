import subprocess

# Lista de scripts a ejecutar en orden
scripts_to_run = [
    "05_detalles_partidos_v3.py",
    "06_h2h_v3.py",
    "07_lineups_v3.py",
    "08_players_fixture_stats_v3.py"
]

# Ejecutar cada script en orden
for script in scripts_to_run:
    print(f"Ejecutando {script}...")
    result = subprocess.run(["python3", script], capture_output=True, text=True)
    
    # Imprimir la salida del script
    print(result.stdout)
    
    # Verificar si hubo errores
    if result.returncode != 0:
        print(f"Error al ejecutar {script}. Detalle del error:")
        print(result.stderr)
        break

print("Ejecución de scripts completada.")

