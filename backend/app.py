from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os, base64, time
import cv2
import mediapipe as mp
import numpy as np
from collections import deque, Counter

app = Flask(__name__)

# ============================
# Configuración
# ============================
# Si pones False, el backend NO devolverá la imagen anotada (menos carga).
RETURN_FRAME = False
# Máximo ancho del frame procesado en el servidor (reduce CPU/RAM)
SERVER_MAX_W = 400

# ---- CORS: autoriza tu GitHub Pages y (opcional) localhost ----
ALLOWED_ORIGINS = [
    "https://samuelarangoizad.github.io",
    "https://samuelarangoizad.github.io/Hands-Help",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]
CORS(
    app,
    resources={r"/*": {"origins": ALLOWED_ORIGINS}},
    supports_credentials=False,
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

@app.after_request
def add_cors_headers(resp):
    origin = request.headers.get("Origin")
    if origin in ALLOWED_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Vary"] = "Origin"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

# ============================
# Diccionario (texto -> señas)
# ============================
with open(os.path.join("senias", "Diccionario.json"), "r", encoding="utf-8") as f:
    diccionario_senas = json.load(f)

@app.route("/")
def home():
    return {"message": "Backend funcionando"}

@app.route("/traducir", methods=["POST", "OPTIONS"])
def traducir():
    if request.method == "OPTIONS":
        return ("", 200)
    data = request.json or {}
    texto = (data.get("texto") or "").lower()
    senas = [{"letra": ch, "url": diccionario_senas[ch]} for ch in texto if ch in diccionario_senas]
    return jsonify({"original": texto, "senas": senas})

# ============================
# MediaPipe Hands
# ============================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=0,            # 0 = más rápido (ideal para servidor free)
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
mp_draw = mp.solutions.drawing_utils

WRIST = 0
TIP =   {"thumb":4, "index":8, "middle":12, "ring":16, "pinky":20}
PIP =   {"thumb":3, "index":6, "middle":10, "ring":14, "pinky":18}
MCP =   {"thumb":2, "index":5, "middle":9, "ring":13, "pinky":17}

def np_point(lm): return np.array([lm.x, lm.y], dtype=np.float32)

def palm_size(lms):
    w = np_point(lms[WRIST]); m = np_point(lms[MCP["middle"]])
    return np.linalg.norm(m - w) + 1e-6

def norm_landmarks(lms):
    w = np_point(lms[WRIST]); s = palm_size(lms)
    return np.vstack([(np_point(lm) - w) / s for lm in lms])

def dist(a,b): return float(np.linalg.norm(a - b))

def is_finger_extended(pts, finger):
    w, tip, pip = pts[WRIST], pts[TIP[finger]], pts[PIP[finger]]
    return dist(tip, w) > dist(pip, w) + 0.05

def finger_curl(pts, finger):
    tip_mcp = dist(pts[TIP[finger]], pts[MCP[finger]])
    pip_mcp = dist(pts[PIP[finger]], pts[MCP[finger]])
    return pip_mcp - tip_mcp

def thumb_index_tip_distance(pts):  return dist(pts[TIP["thumb"]],  pts[TIP["index"]])
def finger_dir(pts, finger): return pts[TIP[finger]] - pts[MCP[finger]]

def angle(u, v):
    u = u / (np.linalg.norm(u) + 1e-8)
    v = v / (np.linalg.norm(v) + 1e-8)
    return float(np.arccos(np.clip((u * v).sum(), -1.0, 1.0)))

def group_distance(pts, tips=("index","middle","ring","pinky")):
    arr = np.stack([pts[TIP[t]] for t in tips], axis=0)
    c = arr.mean(axis=0)
    return float(np.mean(np.linalg.norm(arr - c, axis=1)))

def classify_letter(pts):
    ext = {f: is_finger_extended(pts, f) for f in TIP.keys()}
    d_ti = thumb_index_tip_distance(pts)

    curl_vals = [finger_curl(pts, f) for f in ["index","middle","ring","pinky"]]
    curl_mean = float(np.mean(curl_vals))

    dir_idx, dir_mid, dir_thumb = finger_dir(pts,"index"), finger_dir(pts,"middle"), finger_dir(pts,"thumb")
    x_axis = np.array([1.0, 0.0], dtype=np.float32)
    ang_idx_x  = angle(dir_idx, x_axis)
    ang_mid_x  = angle(dir_mid, x_axis)
    ang_idx_mid = angle(dir_idx, dir_mid)
    ang_idx_thumb = angle(dir_idx, dir_thumb)
    spread = group_distance(pts)

    if (ext["thumb"] and ext["index"] and ext["middle"] and ext["ring"] and ext["pinky"]
        and curl_mean > 0.02 and 0.10 <= d_ti <= 0.45
        and 1.05 <= ang_idx_thumb <= 2.45 and spread >= 0.05):
        return "C"
    if (not ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]
        and curl_mean > 0.04 and d_ti < 0.14):
        return "E"
    if (ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]
        and ext["thumb"] and ang_idx_x < 0.45 and angle(dir_idx, dir_thumb) < 0.6):
        return "G"
    if (ext["index"] and ext["middle"] and not ext["ring"] and not ext["pinky"] and not ext["thumb"]
        and ang_idx_mid < 0.35 and max(ang_idx_x, ang_mid_x) < 0.5):
        return "H"

    if (not ext["thumb"] and all(ext[f] for f in ["index","middle","ring","pinky"])): return "B"
    if (ext["index"] and ext["thumb"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]): return "L"
    if (ext["index"] and ext["middle"] and not ext["ring"] and not ext["pinky"] and not ext["thumb"]):  return "V"
    if (ext["index"] and ext["middle"] and ext["ring"] and not ext["pinky"] and not ext["thumb"]):      return "W"
    if (ext["thumb"] and not ext["index"] and not ext["middle"] and not ext["ring"] and ext["pinky"]):  return "Y"
    if (ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]):                   return "D"
    if d_ti < 0.15 and (ext["middle"] or ext["ring"] or ext["pinky"]):                                   return "F"

    if not any([ext["index"], ext["middle"], ext["ring"], ext["pinky"]]): return "A"
    return "?"

# suavizado temporal
last_preds = deque(maxlen=7)

@app.route("/detectar-senas", methods=["POST", "OPTIONS"])
def detectar_senas():
    if request.method == "OPTIONS":
        return ("", 200)

    t0 = time.time()
    try:
        data = request.json or {}
        frame_data = data.get("frame")
        if not frame_data:
            return jsonify({"error": "No frame recibido"}), 400

        # ---- Decodificar base64
        try:
            _, b64 = frame_data.split(",", 1)
        except ValueError:
            b64 = frame_data
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(b64), np.uint8),
                             cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({"error": "Frame inválido"}), 400

        # ---- Reescalar en servidor
        h, w = frame.shape[:2]
        if w > SERVER_MAX_W:
            nh = int(h * SERVER_MAX_W / w)
            frame = cv2.resize(frame, (SERVER_MAX_W, nh), interpolation=cv2.INTER_AREA)

        # ---- MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)

        letra = "?"
        n_hands = 0
        if res.multi_hand_landmarks:
            n_hands = len(res.multi_hand_landmarks)
            hl = res.multi_hand_landmarks[0]
            pts = norm_landmarks(hl.landmark)
            letra = classify_letter(pts)
            # Dibuja solo si vas a devolver imagen
            if RETURN_FRAME:
                mp_draw.draw_landmarks(
                    frame, hl, mp_hands.HAND_CONNECTIONS,
                    mp_draw.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=2),
                    mp_draw.DrawingSpec(color=(255,0,0), thickness=2)
                )

        if letra != "?":
            last_preds.append(letra)
        letra_estable = Counter(last_preds).most_common(1)[0][0] if last_preds else "?"

        payload = {
            "letra": letra_estable,
            "debug": {"hands": n_hands, "ms": round((time.time()-t0)*1000)}
        }

        if RETURN_FRAME:
            cv2.rectangle(frame, (8, 8), (220, 64), (0, 0, 0), thickness=-1)
            cv2.putText(frame, f"Letra: {letra_estable}", (16, 56),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2, cv2.LINE_AA)
            ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            if ok:
                payload["frame"] = "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")

        return jsonify(payload)

    except Exception as e:
        # Evita 500 -> Render 502; devuelve 200 con error controlado
        return jsonify({"error": "server-fail", "detail": str(e)}), 200

# ============================
# Main (Render usa PORT)
# ============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
