"""
Reset completo: puntajes a 0, sube a Firebase.
"""
import json, ssl, urllib.request
from pathlib import Path

BASE_DIR     = Path(__file__).parent
SCORES_FILE  = BASE_DIR / "scores.json"
FIREBASE_URL = "https://bomber-3a196-default-rtdb.firebaseio.com/scores.json"

CUOTAS_INIT = [2.38, 3.17, 6.35, 9.52, 19.05]
COLORS      = ["Blanco", "Negro", "Rojo", "Azul", "Verde"]

# Lee nombres de players.json si existe
players_file = BASE_DIR / "players.json"
if players_file.exists():
    with open(players_file, encoding="utf-8") as f:
        pdata = json.load(f)
    names  = [pdata[str(i)]["name"]  for i in range(1, 6)]
    colors = [pdata[str(i)]["color"] for i in range(1, 6)]
else:
    names  = [f"Jugador{i}" for i in range(1, 6)]
    colors = COLORS

scores = {
    str(i + 1): {
        "name":    names[i],
        "color":   colors[i],
        "points":  0,
        "odds":    CUOTAS_INIT[i],
        "history": []
    }
    for i in range(5)
}

# Guarda local
with open(SCORES_FILE, "w", encoding="utf-8") as f:
    json.dump(scores, f, indent=2, ensure_ascii=False)
print("scores.json reseteado.")

# Sube a Firebase
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode    = ssl.CERT_NONE

data = json.dumps(scores).encode("utf-8")
req  = urllib.request.Request(
    FIREBASE_URL, data=data, method="PUT",
    headers={"Content-Type": "application/json"}
)
try:
    urllib.request.urlopen(req, timeout=10, context=ctx)
    print("Firebase reseteado OK.")
except Exception as e:
    print(f"Error Firebase: {e}")

print("\nTodo en cero. Jugadores:")
for i in range(5):
    s = scores[str(i+1)]
    print(f"  [{i+1}] {s['name']:<14} ({s['color']})  cuota: {s['odds']}x")

print()
input("Enter para cerrar...")
