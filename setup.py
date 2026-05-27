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
    n = len(init_probs)
    for i, s in enumerate(scores):
        if s >= WIN_GOAL:
            return [1.0 if j == i else 0.0 for j in range(n)]
    weights = [init_probs[i] * (1 + (1 - init_probs[i]) * K_BOOST) ** scores[i]
               for i in range(n)]
    total = sum(weights)
    return [w / total for w in weights]

def probs_a_cuotas(probs):
    return [round(max(MIN_CUOTA, 1 / (p * MARGEN)), 2) if p > 0 else 999.99
            for p in probs]

def generar_tabla(init_probs, active_slots):
    """
    Genera todas las combinaciones para N jugadores activos.
    La key es siempre de 5 slots (rellena con 0 los inactivos).
    """
    n = len(init_probs)
    tabla = {}

    def recurse(scores, depth):
        if depth == n:
            probs  = calcular_probs(scores, init_probs)
            cuotas = probs_a_cuotas(probs)
            # Mapear a 5 slots: slots activos -> sus cuotas, otros -> 999.99
            full = [999.99] * 5
            for idx, slot in enumerate(active_slots):
                full[int(slot) - 1] = cuotas[idx]
            # La key incluye solo los slots activos en orden
            key = ",".join(str(s) for s in scores)
            tabla[key] = full
            return
        for v in range(WIN_GOAL):
            recurse(scores + [v], depth + 1)

    recurse([], 0)
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
    print("  Escribe quien juega en cada color del scoreboard.")
    print("  Escribe 'no' si ese color NO esta en uso.")
    print()

    players_raw = []   # lista de (pos, nombre, prob, color) solo activos
    for i in range(5):
        nombre = input(f"  [{i+1}] {COLORS[i]:<10}: ").strip()
        if not nombre or nombre.lower() == "no":
            print(f"      -> SKIP (sin jugador)")
            continue
        prob = get_prob(nombre)
        skill_msg = "conocido" if nombre.lower() in SKILLS else "default"
        print(f"      -> {nombre} ({skill_msg}, prob {prob*100:.0f}%)")
        players_raw.append((i + 1, nombre, prob, COLORS[i]))

    if len(players_raw) < 2:
        print("\n  Necesitas al menos 2 jugadores.")
        input("  Enter para salir...")
        return

    # Normaliza probabilidades a que sumen 1.0
    total = sum(p[2] for p in players_raw)
    players = {}
    for pos, nombre, prob, color in players_raw:
        players[str(pos)] = {
            "name":  nombre,
            "color": color,
            "prob":  prob / total,
        }

    # init_probs en el orden de los slots activos (para el modelo)
    active_slots = sorted(players.keys(), key=int)
    init_probs   = [players[s]["prob"] for s in active_slots]

    # Cuotas iniciales (todos en 0)
    cuotas_init = probs_a_cuotas(init_probs)
    cuotas_by_slot = {active_slots[i]: cuotas_init[i] for i in range(len(active_slots))}

    cls()
    print("  Configuracion lista:")
    print()
    print(f"  {'POS':<5} {'NOMBRE':<14} {'COLOR':<10} {'PROB%':>7}  {'CUOTA':>8}")
    print("  " + "-" * 50)
    for slot in active_slots:
        p = players[slot]
        print(f"  #{slot}    {p['name']:<14} {p['color']:<10} "
              f"{p['prob']*100:>6.1f}%  {cuotas_by_slot[slot]:>6.2f}x")
    print()

    # Guarda players.json
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)

    # Genera tabla_odds.json (solo para slots activos)
    tabla = generar_tabla(init_probs, active_slots)
    with open(TABLA_FILE, "w") as f:
        json.dump(tabla, f)
    print(f"  tabla_odds.json generada ({len(tabla)} estados, "
          f"{len(active_slots)} jugadores)")

    # Genera scores.json (solo con slots activos)
    scores = {
        slot: {
            "name":    players[slot]["name"],
            "color":   players[slot]["color"],
            "points":  0,
            "odds":    cuotas_by_slot[slot],
            "history": []
        }
        for slot in active_slots
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
