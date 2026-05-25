"""
Simulador interactivo - Bomberman 4
Modelo tipo Betsson: probabilidades reales + margen del libro 5%.

Probabilidades iniciales (suman 100%):
  Sergio 40% | Joel 30% | Gonzalo 15% | Gallo 10% | Parce 5%

Formula:
  weight_i  = prob_inicial_i * BOOST_i ^ puntos_i
  BOOST_i   = 1 + (1 - prob_inicial_i) * K       (K=2.0 - cambios dramaticos)
  prob_i    = weight_i / suma_pesos              (suman 100%)
  cuota_i   = 1 / (prob_i * MARGEN)              (MARGEN=1.05 = casa toma 5%)
"""
import os, json

WIN_GOAL    = 5
NAMES       = ["Sergio", "Joel", "Gonzalo", "Gallo", "Parce"]
INIT_PROBS  = [0.40,     0.30,   0.15,      0.10,    0.05  ]
K_BOOST     = 2.0
MARGEN      = 1.05      # margen del libro (5% como casa real)
MIN_CUOTA   = 1.01

def boost_of(i):
    return 1 + (1 - INIT_PROBS[i]) * K_BOOST

def calcular_probs(scores):
    for i, s in enumerate(scores):
        if s >= WIN_GOAL:
            return [1.0 if j == i else 0.0 for j in range(len(NAMES))]
    weights = [INIT_PROBS[i] * boost_of(i)**scores[i] for i in range(len(NAMES))]
    total   = sum(weights)
    return [w/total for w in weights]

def probs_a_cuotas(probs):
    return [round(max(MIN_CUOTA, 1/(p*MARGEN)), 2) if p > 0 else 999.99 for p in probs]

# Tabla para el detector
tabla = {}
for s0 in range(WIN_GOAL):
    for s1 in range(WIN_GOAL):
        for s2 in range(WIN_GOAL):
            for s3 in range(WIN_GOAL):
                for s4 in range(WIN_GOAL):
                    probs = calcular_probs([s0,s1,s2,s3,s4])
                    tabla[f"{s0},{s1},{s2},{s3},{s4}"] = probs_a_cuotas(probs)
with open("tabla_odds.json","w") as f:
    json.dump(tabla, f)

# ── UI ────────────────────────────────────────────────────────────────────────
def cls():
    os.system("cls" if os.name == "nt" else "clear")

def barra_progreso(pts):
    """Visualizacion de puntos como casillas."""
    return "[" + "*" * pts + "_" * (WIN_GOAL - pts) + "]"

def trend(old_prob, new_prob):
    """Indicador de tendencia."""
    if old_prob is None: return "  "
    diff = (new_prob - old_prob) * 100
    if abs(diff) < 0.1: return "  "
    if diff > 0:        return f"^{diff:+.1f}".replace("+",""[:0])[:5]
    return f"v{diff:.1f}"[:5]

def mostrar(scores, prev_probs, historial):
    cls()
    probs  = calcular_probs(scores)
    cuotas = probs_a_cuotas(probs)
    orden  = sorted(range(len(NAMES)), key=lambda i: -probs[i])

    print("+" + "=" * 70 + "+")
    print("|" + "  BOMBERMAN 4  -  Marcador en vivo  (estilo Betsson)".ljust(70) + "|")
    print("+" + "=" * 70 + "+")
    print()
    print(f"  {'POS':<4} {'JUGADOR':<10} {'PROGRESO':<10} {'PROB':<10} {'CUOTA':>8}  TENDENCIA")
    print("  " + "-" * 65)
    for rank, i in enumerate(orden, 1):
        pct  = probs[i] * 100
        prev = prev_probs[i] if prev_probs else None
        if prev is not None:
            diff = (probs[i] - prev) * 100
            if abs(diff) < 0.05:
                tr = "  --"
            elif diff > 0:
                tr = f"  +{diff:.1f}%"
            else:
                tr = f"  {diff:.1f}%"
        else:
            tr = "    -"

        mark = " <<< FAVORITO" if rank == 1 and probs[i] > 0 else ""
        prog = barra_progreso(scores[i])
        print(f"  #{rank}   {NAMES[i]:<10} {prog:<10}  {pct:>5.1f}%   "
              f"{cuotas[i]:>6.2f}x  {tr:<10}{mark}")
    print()

    # Barra de probabilidades visual
    print("  Distribucion de probabilidad:")
    print("  ", end="")
    for i in orden:
        if probs[i] < 0.005: continue
        n_chars = max(1, int(probs[i] * 60))
        letra = NAMES[i][0]
        print(letra * n_chars, end="")
    print()
    print(f"  ({'='*60})")
    print(f"  TOTAL: {sum(probs)*100:.1f}%  |  Margen del libro: {(MARGEN-1)*100:.0f}%")
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
            print(f"    [{i+1}] {NAMES[i]:<10}  pts: {scores[i]}/5")
    print("    [R] Reiniciar     [Q] Salir")
    print()

# ── Loop ──────────────────────────────────────────────────────────────────────
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
                print()
                print(f"   *** {NAMES[idx].upper()} GANO EL CAMPEONATO! ***")
                print()
                input("   Enter para reiniciar...")
                scores     = [0] * len(NAMES)
                prev_probs = None
                historial  = []
            else:
                new_probs = calcular_probs(scores)
                delta = (new_probs[idx] - prev_probs[idx]) * 100
                cuota_new = round(max(MIN_CUOTA, 1/(new_probs[idx]*MARGEN)), 2)
                historial.append(
                    f"{NAMES[idx]} +1pt  prob {prev_probs[idx]*100:.1f}% -> "
                    f"{new_probs[idx]*100:.1f}% (+{delta:.1f}%)  cuota {cuota_new}x"
                )

    print()
    input("  Listo. Enter para cerrar...")

if __name__ == "__main__":
    main()
