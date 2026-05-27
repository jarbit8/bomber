"""
Detector de puntos - Super Bomberman 4
Lee players.json para nombres, usa tabla_odds.json para cuotas.
Pushea a Firebase en tiempo real.
"""
import cv2
import numpy as np
import mss
import json
import ssl
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
FIREBASE_URL = "https://bomber-3a196-default-rtdb.firebaseio.com/scores.json"
SCORES_FILE  = BASE_DIR / "scores.json"
TABLA_FILE   = BASE_DIR / "tabla_odds.json"
PLAYERS_FILE = BASE_DIR / "players.json"
LOG_FILE     = BASE_DIR / "log.txt"
DEBUG_DIR    = BASE_DIR / "debug"

# Colores HSV del scoreboard verde y coronas doradas
BOARD_HSV_LO = np.array([48,  80,  60])
BOARD_HSV_HI = np.array([88, 255, 170])
CROWN_HSV_LO = np.array([18, 140, 160])
CROWN_HSV_HI = np.array([38, 255, 255])

BOARD_AREA_MIN = 50_000   # como el original que funcionaba
BOARD_PCT_MIN  = 0.12     # 12% como el original
CROWN_PX_MIN   = 30       # como el original
CONFIRM_FRAMES = 1        # instantaneo (sin esperar)
CAPTURE_SECS   = 0.25     # captura cada 250 ms
VERBOSE        = True     # log de % verde
SAVE_DEBUG     = True     # guarda screenshots cada N segs

WIN_GOAL = 5

# SSL sin verificacion (fix Python 3.14)
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode    = ssl.CERT_NONE

# ── Firebase ──────────────────────────────────────────────────────────────────
def push_firebase(scores: dict):
    try:
        data = json.dumps(scores).encode("utf-8")
        req  = urllib.request.Request(
            FIREBASE_URL, data=data, method="PUT",
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=6, context=_CTX)
    except Exception as e:
        print(f"  [Firebase ERROR] {e}", flush=True)

def fetch_firebase():
    """Lee el estado actual de Firebase. Devuelve None si falla."""
    try:
        req = urllib.request.Request(FIREBASE_URL, method="GET")
        with urllib.request.urlopen(req, timeout=6, context=_CTX) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  [Firebase GET ERROR] {e}", flush=True)
        return None

# ── Scores / Players ──────────────────────────────────────────────────────────
def load_scores() -> dict:
    if SCORES_FILE.exists():
        with open(SCORES_FILE, encoding="utf-8") as f:
            return json.load(f)
    # Fallback si no existe scores.json
    return {str(p): {"name": f"Jugador{p}", "color": "?", "points": 0,
                     "odds": 5.0, "history": []} for p in range(1, 6)}

def save_scores(scores: dict):
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)

# ── Tabla de odds ─────────────────────────────────────────────────────────────
def load_tabla() -> dict:
    if not TABLA_FILE.exists():
        raise FileNotFoundError(
            "tabla_odds.json no encontrado.\n"
            "Corre primero: python simulacion.py"
        )
    with open(TABLA_FILE) as f:
        return json.load(f)

def get_odds(scores: dict) -> dict:
    # Key dinamica: solo los slots que existen, en orden
    slots = sorted(scores.keys(), key=int)
    key = ",".join(str(scores[s]["points"]) for s in slots)
    lst = TABLA.get(key)
    if lst is None:
        return {s: scores[s]["odds"] for s in slots}
    # lst es siempre de 5 slots (slots no activos = 999.99)
    return {s: lst[int(s) - 1] for s in slots}

TABLA = load_tabla()

# ── Log ───────────────────────────────────────────────────────────────────────
def log(msg: str):
    ts   = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ── Deteccion ─────────────────────────────────────────────────────────────────
def detect_board(frame: np.ndarray, debug_info=None):
    h, w = frame.shape[:2]
    hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, BOARD_HSV_LO, BOARD_HSV_HI)
    pct  = mask.sum() / (h * w * 255)
    if debug_info is not None:
        debug_info["pct_verde"] = pct
    if pct < BOARD_PCT_MIN:
        return None
    k    = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    biggest = max(cnts, key=cv2.contourArea)
    area = cv2.contourArea(biggest)
    if debug_info is not None:
        debug_info["area"] = area
    if area < BOARD_AREA_MIN:
        return None
    return cv2.boundingRect(biggest)

def count_crowns(frame: np.ndarray, board) -> dict:
    bx, by, bw, bh = board
    hsv   = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    cmask = cv2.inRange(hsv, CROWN_HSV_LO, CROWN_HSV_HI)

    header_f = 0.18
    label_f  = 0.30
    n_cells  = 6

    cy0  = int(by + bh * header_f)
    cx0  = int(bx + bw * label_f)
    rowh = int((bh * (1 - header_f)) / 5)
    celw = int((bw * (1 - label_f))  / n_cells)

    result = {}
    for p in range(5):
        y0 = cy0 + p * rowh
        y1 = y0 + rowh
        cnt = 0
        for c in range(n_cells):
            x0 = cx0 + c * celw
            x1 = x0 + celw
            if cmask[y0:y1, x0:x1].sum() // 255 >= CROWN_PX_MIN:
                cnt += 1
        result[p + 1] = cnt
    return result

def save_debug(frame: np.ndarray, tag: str):
    DEBUG_DIR.mkdir(exist_ok=True)
    ts   = datetime.now().strftime("%H%M%S")
    path = str(DEBUG_DIR / f"{tag}_{ts}.png")
    cv2.imwrite(path, frame)
    log(f"  [DEBUG] -> debug/{tag}_{ts}.png")

# ── Loop principal ─────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  Detector Bomberman 4  |  Ctrl+C para salir")
    print(f"  Tabla cargada: {len(TABLA)} estados")
    print("=" * 55)

    scores = load_scores()

    # Jugadores activos (no incluye los marcados como "no")
    active_slots = [int(p) for p in scores.keys()]

    # Muestra jugadores configurados
    print()
    for p in active_slots:
        d = scores[str(p)]
        print(f"  [{p}] {d['name']:<14} color: {d.get('color','?'):<8} "
              f"cuota inicial: {d['odds']}x")
    print(f"  ({len(active_slots)} jugadores activos)")
    print()

    push_firebase(scores)
    log("Scores iniciales enviados a Firebase")

    confirm_count = 0
    visible       = False
    prev_crowns   = {}
    scored_set    = set()
    last_verbose  = 0
    last_snapshot = 0

    with mss.mss() as sct:
        mon = sct.monitors[1]
        while True:
            raw   = sct.grab(mon)
            frame = cv2.cvtColor(np.array(raw, dtype=np.uint8), cv2.COLOR_BGRA2BGR)
            info  = {}
            board = detect_board(frame, info)

            now = time.time()
            # Log de % de verde cada 3 segs (para debug)
            if VERBOSE and now - last_verbose > 3.0:
                pct  = info.get("pct_verde", 0) * 100
                area = info.get("area", 0)
                state = "VISIBLE" if visible else "buscando"
                print(f"  [{state}] verde={pct:.1f}%  area={int(area):>7}  "
                      f"(min {BOARD_PCT_MIN*100:.0f}% / {BOARD_AREA_MIN})",
                      flush=True)
                last_verbose = now

            # Screenshot cada 10 segs para diagnostico
            if SAVE_DEBUG and now - last_snapshot > 10.0:
                DEBUG_DIR.mkdir(exist_ok=True)
                snap_path = str(DEBUG_DIR / f"snap_{datetime.now().strftime('%H%M%S')}.png")
                cv2.imwrite(snap_path, frame)
                last_snapshot = now

            if board:
                confirm_count += 1
                if not visible and confirm_count >= CONFIRM_FRAMES:
                    visible     = True
                    prev_crowns = count_crowns(frame, board)
                    scored_set  = set()
                    log(f"SCOREBOARD confirmado  baseline={prev_crowns}")
                    save_debug(frame, "scoreboard")

                if visible:
                    crowns = count_crowns(frame, board)
                    for pnum in active_slots:
                        nueva = crowns.get(pnum, 0)
                        vieja = prev_crowns.get(pnum, 0)
                        if nueva > vieja and pnum not in scored_set:
                            id_  = str(pnum)
                            name = scores[id_]["name"]

                            old_odds = {i: scores[str(i)]["odds"] for i in active_slots}
                            scores[id_]["points"] = min(
                                WIN_GOAL, scores[id_]["points"] + 1
                            )
                            scored_set.add(pnum)

                            new_odds = get_odds(scores)
                            for pid in scores.keys():
                                if pid in new_odds:
                                    scores[pid]["odds"] = new_odds[pid]

                            scores[id_]["history"].append({
                                "ts":          datetime.now().isoformat(),
                                "total":       scores[id_]["points"],
                                "odds_before": old_odds[pnum],
                                "odds_after":  scores[id_]["odds"],
                            })
                            save_scores(scores)
                            push_firebase(scores)

                            log(f"PUNTO -> {name}  "
                                f"pts={scores[id_]['points']}  "
                                f"{old_odds[pnum]}x -> {scores[id_]['odds']}x")
                            log("  " + " | ".join(
                                f"{scores[str(p)]['name']}="
                                f"{scores[str(p)]['odds']}x"
                                for p in active_slots))

                    prev_crowns = crowns

            else:
                if visible:
                    log("Scoreboard cerrado")
                    scored_set  = set()
                    prev_crowns = {}
                    # Sincroniza desde Firebase por si la web reseteo
                    fb = fetch_firebase()
                    if fb:
                        fb_total    = sum(fb[str(p)]["points"] for p in active_slots if str(p) in fb)
                        local_total = sum(scores[str(p)]["points"] for p in active_slots)
                        if fb_total < local_total:
                            log("Reset detectado desde web -> sincronizando")
                            scores = {str(p): fb[str(p)] for p in active_slots if str(p) in fb}
                            save_scores(scores)
                visible       = False
                confirm_count = 0

            time.sleep(CAPTURE_SECS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDetector detenido.")
