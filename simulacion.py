"""
Simulador interactivo - Bomberman 4
Modelo tipo Betsson: probabilidades reales + margen del libro 5%.

Probabilidades iniciales (suman 100%):
  Pos1 40% | Pos2 30% | Pos3 15% | Pos4 10% | Pos5 5%

  Con MARGEN=1.05 esto da cuotas iniciales:
  Pos1 ~2.38x | Pos2 ~3.17x | Pos3 ~6.35x | Pos4 ~9.52x | Pos5 ~19.05x

Formula:
  weight_i  = prob_i * BOOST_i ^ puntos_i
  BOOST_i   = 1 + (1 - prob_i) * K        (K=0.5 - cambios graduales)
  prob_i    = weight_i / suma_pesos        (suman 100%)
  cuota_i   = 1 / (prob_i * MARGEN)       (MARGEN=1.05)
"""
import os, json
from pathlib import Path

WIN_GOAL   = 5
K_BOOST    = 0.5     # gradual, no dramatico
MARGEN     = 1.05
MIN_CUOTA  = 1.01

PLAYERS_FILE = Path(__file__).parent / "players.json"

def load_players():
    """Carga nombres desde players.json o usa defaults."""
    if PLAYERS_FILE.exists():
        with open(PLAYERS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        names = [data[str(i)]["name"] for i in range(1, 6)]
        probs = [data[str(i)]["prob"]  for i in range(1, 6)]
        return names, probs
    return (["Jugador1","Jugador2","Jugador3","Jugador4","Jugador5"],
            [0.40, 0.30, 0.15, 0.10, 0.05])

NAMES, INIT_PROBS = load_players()

def boost_of(i):
    return 1 + (1 - INIT_PROBS[i]) * K_BOOST

def calcular_probs(scores):
    for i, s in enumerate(scores):
        if s >= WIN_GOAL:
            return [1.0 if j == i else 0.0 for j in range(len(NAMES))]
    weights = [INIT_PROBS[i] * boost_of(i)**scores[i] for i in range(len(NAMES))]
    total   = sum(weights)
    return [w / total for w in weights]

def probs_a_cuotas(probs):
    return [round(max(MIN_CUOTA, 1 / (p * MARGEN)), 2) if p > 0 else 999.99
            for p in probs]

# ── Genera tabla para el detector ────────────────────────────────────────────
tabla = {}
for s0 in range(WIN_GOAL):
    for s1 in range(WIN_GOAL):
        for s2 in range(WIN_GOAL):
            for s3 in range(WIN_GOAL):
                for s4 in range(WIN_GOAL):
                    probs = calcular_probs([s0, s1, s2, s3, s4])
                    tabla[f"{s0},{s1},{s2},{s3},{s4}"] = probs_a_cuotas(probs)

tabla_path = Path(__file__).parent / "tabla_odds.json"
with open(tabla_path, "w") as f:
    json.dump(tabla, f)
print(f"  tabla_odds.json generada ({len(tabla)} estados)")

# ── UI ────────────────────────────────────────────────────────────────────────
def cls():
    os.system("cls" if os.name == "nt" else "clear")

def barra(pts):
    return "[" + "+" * pts + "_" * (WIN_GOAL - pts) + "]"

def mostrar(scores, prev_probs, historial):
    cls()
    probs  = calcular_probs(scores)
    cuotas = probs_a_cuotas(probs)
    orden  = sorted(range(len(NAMES)), key=lambda i: -probs[i])

    print("+" + "=" * 72 + "+")
    print("|" + "  BOMBERMAN 4  -  Marcador en vivo  (estilo Betsson)".center(72) + "|")
    print("+" + "=" * 72 + "+")
    print()
    print(f"  {'#':<3} {'JUGADOR':<12} {'PROG':<10} {'PROB%':>7}  {'CUOTA':>7}  CAMBIO")
    print("  " + "-" * 60)

    for rank, i in enumerate(orden, 1):
        pct  = probs[i] * 100
        prev = prev_probs[i] if prev_probs else None
        if prev is not None:
            diff = (probs[i] - prev) * 100
            tr   = f"  +{diff:.1f}%" if diff > 0.05 else (f"  {diff:.1f}%" if diff < -0.05 else "  --")
        else:
            tr = "  -"

        fav  = " <<< FAVORITO" if rank == 1 and probs[i] > 0 else ""
        print(f"  #{rank:<2}  {NAMES[i]:<12} {barra(scores[i]):<10}  "
              f"{pct:>6.1f}%  {cuotas[i]:>6.2f}x  {tr}{fav}")
    print()
    print(f"  Margen del libro: {(MARGEN-1)*100:.0f}%  |  "
          f"Total prob: {sum(probs)*100:.1f}%")
    print()

    if historial:
        print("  Ultimos eventos:")
        for h in historial[-5:]:
            print(f"    {h}")
        print()

def mostrar_menu(scores):
    print("  Quien sumo punto?")
    for i in range(len(NAMES)):
        if scores[i] < WIN_GOAL:
            print(f"    [{i+1}] {NAMES[i]:<12}  {scores[i]}/5")
    print("    [R] Reiniciar     [Q] Salir")
    print()

def main():
    scores     = [0] * len(NAMES)
    prev_probs = None
    historial  = []

    while True:
        mostrar(scores, prev_probs, historial)
        mostrar_menu(scores)
        cmd = input("  > ").strip().upper()

        if cmd == "Q":
            break
        elif cmd == "R":
            scores     = [0] * len(NAMES)
            prev_probs = None
            historial  = []
        elif cmd.isdigit() and 1 <= int(cmd) <= len(NAMES):
            idx = int(cmd) - 1
            if scores[idx] >= WIN_GOAL:
                input(f"  {NAMES[idx]} ya gano! [Enter]")
                continue

            prev_probs = calcular_probs(scores)
            scores[idx] += 1

            if scores[idx] >= WIN_GOAL:
                mostrar(scores, prev_probs, historial)
                print(f"\n  *** {NAMES[idx].upper()} GANO EL CAMPEONATO! ***\n")
                input("  Enter para reiniciar...")
                scores     = [0] * len(NAMES)
                prev_probs = None
                historial  = []
            else:
                new_probs = calcular_probs(scores)
                delta     = (new_probs[idx] - prev_probs[idx]) * 100
                cuota_new = probs_a_cuotas(new_probs)[idx]
                historial.append(
                    f"{NAMES[idx]} +1pt  "
                    f"{prev_probs[idx]*100:.1f}% -> {new_probs[idx]*100:.1f}% "
                    f"({delta:+.1f}%)  cuota {cuota_new}x"
                )

    print()
    input("  Listo. Enter para cerrar...")

if __name__ == "__main__":
    main()
