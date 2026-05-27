"""
Setup - Bomberman 4
Asigna nombres reales a cada color de personaje.
Guarda en players.json para que detector y simulador usen los mismos datos.
"""
import json, os
from pathlib import Path

PLAYERS_FILE = Path(__file__).parent / "players.json"
SCORES_FILE  = Path(__file__).parent / "scores.json"

# Colores de personajes en Super Bomberman 4 (orden del scoreboard)
COLORS = ["Blanco", "Negro", "Rojo", "Azul", "Verde"]

# Probabilidades por rango (mejor jugador en pos 1, peor en pos 5)
# Gradual: Pos1 es el mejor pero no abrumadoramente
PROBS_BY_RANK = [0.40, 0.30, 0.15, 0.10, 0.05]

# Cuotas iniciales que genera el modelo (referencia visual)
# Con K=0.5, MARGEN=1.05 y todos en 0 puntos:
CUOTAS_REF = [2.38, 3.17, 6.35, 9.52, 19.05]

def cls():
    os.system("cls" if os.name == "nt" else "clear")

def main():
    cls()
    print("+" + "=" * 58 + "+")
    print("|" + "  BOMBERMAN 4  -  Configuracion de jugadores".center(58) + "|")
    print("+" + "=" * 58 + "+")
    print()
    print("  Escribe el nombre de cada jugador segun su color.")
    print("  El ORDEN importa: pon al MEJOR jugador en pos 1.")
    print("  Deja vacio para usar el color como nombre.")
    print()
    print(f"  {'POS':<5} {'COLOR':<10} {'PROB%':>7}  {'CUOTA INICIAL':>14}")
    print("  " + "-" * 42)
    for i in range(5):
        print(f"  [{i+1}]   {COLORS[i]:<10} {PROBS_BY_RANK[i]*100:>6.0f}%  "
              f"{CUOTAS_REF[i]:>12.2f}x")
    print()

    players = {}
    for i in range(5):
        nombre = input(f"  Jugador {i+1} ({COLORS[i]}): ").strip()
        if not nombre:
            nombre = COLORS[i]
        players[str(i + 1)] = {
            "name":  nombre,
            "color": COLORS[i],
            "prob":  PROBS_BY_RANK[i],
        }

    cls()
    print()
    print("  Configuracion guardada:")
    print()
    print(f"  {'POS':<5} {'NOMBRE':<14} {'COLOR':<10} {'CUOTA INICIAL':>14}")
    print("  " + "-" * 48)
    for i in range(5):
        p = players[str(i + 1)]
        print(f"  #{i+1}    {p['name']:<14} {p['color']:<10} {CUOTAS_REF[i]:>12.2f}x")
    print()

    # Guarda players.json
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)

    # Regenera scores.json con puntajes en 0 y cuotas iniciales correctas
    scores = {
        str(i + 1): {
            "name":    players[str(i + 1)]["name"],
            "color":   COLORS[i],
            "points":  0,
            "odds":    CUOTAS_REF[i],
            "history": []
        }
        for i in range(5)
    }
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)

    print("  players.json y scores.json creados.")
    print()
    input("  Enter para iniciar el detector...")

if __name__ == "__main__":
    main()
