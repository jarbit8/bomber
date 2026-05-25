"""
Detector de puntos - Super Bomberman 4
Captura pantalla, detecta coronas y actualiza puntajes + cuotas.
Las cuotas se calculan con la tabla exacta de programacion dinamica
(todas las combinaciones posibles de puntajes precalculadas).
"""
import cv2
import numpy as np
import mss
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path

FIREBASE_URL = "https://bomber-3a196-default-rtdb.firebaseio.com/scores.json"

def push_firebase(scores: dict):
    """Envia el estado completo a Firebase via REST (PUT)."""
    try:
        data = json.dumps(scores).encode("utf-8")
        req  = urllib.request.Request(
            FIREBASE_URL, data=data, method="PUT",
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"[Firebase] Error: {e}", flush=True)

PLAYERS = {
    1: "Sergio",
    2: "Joel",
    3: "Gonzalo",
    4: "Gallo",
    5: "Parce",
}

SCORES_FILE = Path(__file__).parent / "scores.json"
TABLA_FILE  = Path(__file__).parent / "tabla_odds.json"
LOG_FILE    = Path(__file__).parent / "log.txt"

# ── Colores HSV ───────────────────────────────────────────────────────────────
CROWN_HSV_LO = np.array([18, 140, 160])
CROWN_HSV_HI = np.array([38, 255, 255])
BOARD_HSV_LO = np.array([48,  80,  60])
BOARD_HSV_HI = np.array([88, 255, 170])

CROWN_MIN_PX = 30
CAPTURE_SECS = 0.5

# ── Tabla de cuotas exactas (precalculada con DP) ─────────────────────────────
def load_tabla() -> dict:
    if not TABLA_FILE.exists():
        raise FileNotFoundError(
            "No se encontro tabla_odds.json. Corre primero: python simulacion.py"
        )
    with open(TABLA_FILE) as f:
        return json.load(f)

TABLA = load_tabla()

def get_odds_from_tabla(scores: dict) -> dict:
    """
    Busca en la tabla precalculada las cuotas exactas para el estado actual.
    scores = {"1": {"points": N, ...}, ...}
    """
    key = ",".join(str(scores[str(p)]["points"]) for p in range(1, 6))
    odds_list = TABLA.get(key)
    if odds_list is None:
        return {str(p): scores[str(p)]["odds"] for p in range(1, 6)}
    return {str(p): odds_list[p - 1] for p in range(1, 6)}

# ── Utilidades ────────────────────────────────────────────────────────────────
def load_scores() -> dict:
    if SCORES_FILE.exists():
        with open(SCORES_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        str(p): {"name": PLAYERS[p], "points": 0, "odds": 1.5, "history": []}
        for p in PLAYERS
    }

def save_scores(scores: dict):
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)

def log(msg: str):
    ts   = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ── Deteccion ─────────────────────────────────────────────────────────────────
def is_scoreboard(frame_bgr: np.ndarray) -> bool:
    hsv  = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, BOARD_HSV_LO, BOARD_HSV_HI)
    return mask.sum() / (frame_bgr.shape[0] * frame_bgr.shape[1] * 255) > 0.12

def find_board(frame_bgr: np.ndarray):
    hsv  = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, BOARD_HSV_LO, BOARD_HSV_HI)
    k    = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    biggest = max(cnts, key=cv2.contourArea)
    if cv2.contourArea(biggest) < 50_000:
        return None
    return cv2.boundingRect(biggest)

def count_crowns(frame_bgr: np.ndarray, board) -> dict:
    bx, by, bw, bh = board
    header_f = 0.18
    label_f  = 0.30
    n_cells  = 6
    cy0  = int(by + bh * header_f)
    cx0  = int(bx + bw * label_f)
    rowh = int((bh * (1 - header_f)) / 5)
    celw = int((bw * (1 - label_f))  / n_cells)

    hsv   = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    cmask = cv2.inRange(hsv, CROWN_HSV_LO, CROWN_HSV_HI)

    result = {}
    for p in range(5):
        y0 = cy0 + p * rowh
        y1 = y0 + rowh
        cnt = 0
        for c in range(n_cells):
            x0 = cx0 + c * celw
            x1 = x0 + celw
            if cmask[y0:y1, x0:x1].sum() // 255 >= CROWN_MIN_PX:
                cnt += 1
        result[p + 1] = cnt
    return result

# ── Loop principal ─────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  Detector Bomberman 4  |  Ctrl+C para salir")
    print("  Tabla de cuotas: {} estados cargados".format(len(TABLA)))
    print("=" * 55)

    scores = load_scores()
    prev   = {p: 0 for p in range(1, 6)}
    scored_this_board: set = set()
    visible = False

    with mss.mss() as sct:
        mon = sct.monitors[1]
        while True:
            raw   = sct.grab(mon)
            frame = cv2.cvtColor(np.array(raw, dtype=np.uint8), cv2.COLOR_BGRA2BGR)

            if is_scoreboard(frame):
                board = find_board(frame)
                if board:
                    crowns = count_crowns(frame, board)

                    if not visible:
                        log("Scoreboard detectado — baseline sincronizado")
                        prev              = crowns.copy()
                        scored_this_board = set()
                        visible           = True

                    for pnum, cnt in crowns.items():
                        if cnt > prev.get(pnum, 0) and pnum not in scored_this_board:
                            id_   = str(pnum)
                            name  = scores[id_]["name"]
                            scores[id_]["points"] += 1
                            scored_this_board.add(pnum)

                            # Cuotas exactas desde la tabla DP
                            old_odds = {i: scores[str(i)]["odds"] for i in range(1, 6)}
                            new_odds = get_odds_from_tabla(scores)
                            for pid, odd in new_odds.items():
                                scores[pid]["odds"] = odd

                            scores[id_]["history"].append({
                                "ts":         datetime.now().isoformat(),
                                "total":      scores[id_]["points"],
                                "odds_before": old_odds[pnum],
                                "odds_after":  scores[id_]["odds"],
                            })
                            save_scores(scores)
                            push_firebase(scores)

                            log(f"PUNTO: {name}  pts={scores[id_]['points']}  "
                                f"cuota {old_odds[pnum]}x -> {scores[id_]['odds']}x")
                            log("  " + " | ".join(
                                f"{scores[str(p)]['name']}={scores[str(p)]['odds']}x"
                                for p in range(1, 6)
                            ))

                    prev = crowns.copy()
                else:
                    visible = False
            else:
                if visible:
                    log("Scoreboard cerrado")
                    scored_this_board = set()
                visible = False

            time.sleep(CAPTURE_SECS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDetector detenido.")
