"""
Genera tabla_odds.json con todas las combinaciones posibles de puntajes.
Se ejecuta automaticamente al inicio.
"""
import json
from pathlib import Path

BASE_DIR     = Path(__file__).parent
PLAYERS_FILE = BASE_DIR / "players.json"
TABLA_FILE   = BASE_DIR / "tabla_odds.json"

WIN_GOAL  = 5
K_BOOST   = 0.5
MARGEN    = 1.05
MIN_CUOTA = 1.01

# Lee probs desde players.json si existe, sino usa defaults
if PLAYERS_FILE.exists():
    with open(PLAYERS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    INIT_PROBS = [data[str(i)]["prob"] for i in range(1, 6)]
else:
    INIT_PROBS = [0.40, 0.30, 0.15, 0.10, 0.05]

def boost_of(i):
    return 1 + (1 - INIT_PROBS[i]) * K_BOOST

def calcular_probs(scores):
    for i, s in enumerate(scores):
        if s >= WIN_GOAL:
            return [1.0 if j == i else 0.0 for j in range(5)]
    weights = [INIT_PROBS[i] * boost_of(i)**scores[i] for i in range(5)]
    total   = sum(weights)
    return [w / total for w in weights]

def probs_a_cuotas(probs):
    return [round(max(MIN_CUOTA, 1 / (p * MARGEN)), 2) if p > 0 else 999.99
            for p in probs]

tabla = {}
for s0 in range(WIN_GOAL):
    for s1 in range(WIN_GOAL):
        for s2 in range(WIN_GOAL):
            for s3 in range(WIN_GOAL):
                for s4 in range(WIN_GOAL):
                    probs = calcular_probs([s0, s1, s2, s3, s4])
                    tabla[f"{s0},{s1},{s2},{s3},{s4}"] = probs_a_cuotas(probs)

with open(TABLA_FILE, "w") as f:
    json.dump(tabla, f)

print(f"  tabla_odds.json OK ({len(tabla)} estados)")
