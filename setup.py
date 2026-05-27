"""
Setup - Bomberman 4
Asigna jugadores a cada color. Reconoce nombres conocidos y aplica su skill.
Genera players.json, scores.json y tabla_odds.json.
"""
import json, os, ssl, urllib.request
from pathlib import Path

BASE_DIR     = Path(__file__).parent
PLAYERS_FILE = BASE_DIR / "players.json"
SCORES_FILE  = BASE_DIR / "scores.json"
TABLA_FILE   = BASE_DIR / "tabla_odds.json"

FIREBASE_URL = "https://bomber-3a196-default-rtdb.firebaseio.com/scores.json"

# ── Habilidades conocidas (nombre -> probabilidad base) ──────────────────────
SKILLS = {
    "sergio":  0.40,   # el mejor
    "joel":    0.30,
    "gonzalo": 0.15,
    "gallo":   0.10,
    "parce":   0.05,   # el peor
}
DEFAULT_PROB = 0.20    # para nombres no conocidos

# Colores del scoreboard de Super Bomberman 4 (orden fijo)
COLORS = ["Blanco", "Negro", "Rojo", "Azul", "Verde"]

# ── Modelo de cuotas (igual q el detector) ───────────────────────────────────
WIN_GOAL  = 5
K_BOOST   = 0.5
MARGEN    = 1.05
MIN_CUOTA = 1.01

def cls():
    os.system("cls" if os.name == "nt" else "clear")

def get_prob(name: str) -> float:
    return SKILLS.get(name.strip().lower(), DEFAULT_PROB)

def calcular_probs(scores, init_probs):
    for i, s in enumerate(scores):
        if s >= WIN_GOAL:
            return [1.0 if j == i else 0.0 for j in range(5)]
    weights = [init_probs[i] * (1 + (1 - init_probs[i]) * K_BOOST) ** scores[i]
               for i in range(5)]
    total = sum(weights)
    return [w / total for w in weights]

def probs_a_cuotas(probs):
    return [round(max(MIN_CUOTA, 1 / (p * MARGEN)), 2) if p > 0 else 999.99
            for p in probs]

def generar_tabla(init_probs):
    tabla = {}
    for s0 in range(WIN_GOAL):
        for s1 in range(WIN_GOAL):
            for s2 in range(WIN_GOAL):
                for s3 in range(WIN_GOAL):
                    for s4 in range(WIN_GOAL):
                        probs = calcular_probs([s0, s1, s2, s3, s4], init_probs)
                        tabla[f"{s0},{s1},{s2},{s3},{s4}"] = probs_a_cuotas(probs)
    return tabla

def push_firebase(scores):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    data = json.dumps(scores).encode("utf-8")
    req  = urllib.request.Request(
        FIREBASE_URL, data=data, method="PUT",
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=8, context=ctx)
        return True
    except Exception as e:
        print(f"  [Firebase] {e}")
        return False

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    cls()
    print("+" + "=" * 60 + "+")
    print("|" + "  BOMBERMAN 4  -  Setup de jugadores".center(60) + "|")
    print("+" + "=" * 60 + "+")
    print()
    print("  Jugadores conocidos (skill auto-detectado):")
    for name, p in SKILLS.items():
        print(f"    {name.capitalize():<10} -> prob {p*100:.0f}%")
    print(f"    (otros nombres -> {DEFAULT_PROB*100:.0f}%)")
    print()
    print("  Escribe quien juega en cada color del scoreboard:")
    print()

    players = {}
    raw_probs = []

    for i in range(5):
        while True:
            nombre = input(f"  [{i+1}] {COLORS[i]:<10}: ").strip()
            if nombre:
                break
            print("     (no puede estar vacio)")

        prob = get_prob(nombre)
        raw_probs.append(prob)
        players[str(i + 1)] = {
            "name":  nombre,
            "color": COLORS[i],
            "prob":  prob,
        }
        skill_msg = "conocido" if nombre.lower() in SKILLS else "default"
        print(f"      -> {nombre} ({skill_msg}, prob {prob*100:.0f}%)")

    # Normaliza para que sumen 1.0
    total = sum(raw_probs)
    init_probs = [p / total for p in raw_probs]
    for i in range(5):
        players[str(i + 1)]["prob"] = init_probs[i]

    # Cuotas iniciales (estado 0,0,0,0,0)
    cuotas_init = probs_a_cuotas(init_probs)

    cls()
    print("  Configuracion lista:")
    print()
    print(f"  {'POS':<5} {'NOMBRE':<14} {'COLOR':<10} {'PROB%':>7}  {'CUOTA':>8}")
    print("  " + "-" * 50)
    for i in range(5):
        p = players[str(i + 1)]
        print(f"  #{i+1}    {p['name']:<14} {p['color']:<10} "
              f"{p['prob']*100:>6.1f}%  {cuotas_init[i]:>6.2f}x")
    print()

    # Guarda players.json
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)

    # Genera tabla_odds.json
    tabla = generar_tabla(init_probs)
    with open(TABLA_FILE, "w") as f:
        json.dump(tabla, f)
    print(f"  tabla_odds.json generada ({len(tabla)} estados)")

    # Genera scores.json
    scores = {
        str(i + 1): {
            "name":    players[str(i + 1)]["name"],
            "color":   COLORS[i],
            "points":  0,
            "odds":    cuotas_init[i],
            "history": []
        }
        for i in range(5)
    }
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)
    print("  scores.json creado")

    # Sube a Firebase
    if push_firebase(scores):
        print("  Firebase sincronizado OK")
    print()
    input("  Enter para iniciar el detector...")

if __name__ == "__main__":
    main()
