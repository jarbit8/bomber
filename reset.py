"""
Reset completo — pone todos los puntajes en 0 y sube a Firebase.
"""
import json, ssl, urllib.request
from pathlib import Path

SCORES_FILE  = Path(__file__).parent / "scores.json"
FIREBASE_URL = "https://bomber-3a196-default-rtdb.firebaseio.com/scores.json"

scores = {
    "1": {"name": "Sergio",  "points": 0, "odds": 1.50,  "history": []},
    "2": {"name": "Joel",    "points": 0, "odds": 2.20,  "history": []},
    "3": {"name": "Gonzalo", "points": 0, "odds": 3.70,  "history": []},
    "4": {"name": "Gallo",   "points": 0, "odds": 7.00,  "history": []},
    "5": {"name": "Parce",   "points": 0, "odds": 70.00, "history": []},
}

# Guarda local
with open(SCORES_FILE, "w", encoding="utf-8") as f:
    json.dump(scores, f, indent=2, ensure_ascii=False)
print("scores.json reseteado.")

# Sube a Firebase
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

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

print("\nTodo en cero. Ya puedes iniciar el detector.")
input("Enter para cerrar...")
