from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os, base64
import cv2
import mediapipe as mp
import numpy as np
from collections import deque, Counter

app = Flask(__name__)
CORS(app)

# ============================
# 1) Cargar Diccionario (texto -> señas - imágenes)
# ============================
with open(os.path.join("senias", "Diccionario.json"), "r", encoding="utf-8") as f:
    diccionario_senas = json.load(f)

@app.route("/")
def home():
    return {"message": "Backend funcionando"}


# ============================
# 2) Texto -> señas (imágenes)
# ============================
@app.route("/traducir", methods=["POST"])
def traducir():
    data = request.json or {}
    texto = data.get("texto", "").lower()

    senas = []
    for letra in texto:
        if letra in diccionario_senas:
            senas.append({"letra": letra, "url": diccionario_senas[letra]})
    return jsonify({"original": texto, "senas": senas})


# ============================
# 3) SeñAS -> LETRA (MediaPipe Hands)
# ============================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,               # 1 mano para alfabeto
    min_detection_confidence=0.65, # un poco más sensible
    min_tracking_confidence=0.65
)
mp_draw = mp.solutions.drawing_utils

WRIST = 0
TIP =   {"thumb":4, "index":8, "middle":12, "ring":16, "pinky":20}
PIP =   {"thumb":3, "index":6, "middle":10, "ring":14, "pinky":18}
MCP =   {"thumb":2, "index":5, "middle":9, "ring":13, "pinky":17}

# ---------- utilidades geométricas ----------
def np_point(lm): return np.array([lm.x, lm.y], dtype=np.float32)

def palm_size(lms):
    """Tamaño relativo de la palma (wrist -> middle_mcp)."""
    w = np_point(lms[WRIST]); m = np_point(lms[MCP["middle"]])
    return np.linalg.norm(m - w) + 1e-6

def norm_landmarks(lms):
    """Wrist en (0,0) y escala por tamaño de palma (robusto a distancia)."""
    w = np_point(lms[WRIST]); s = palm_size(lms)
    return np.vstack([(np_point(lm) - w) / s for lm in lms])  # (21,2)

def dist(a,b): return float(np.linalg.norm(a - b))

def is_finger_extended(pts, finger):
    """Extendido si TIP->WRIST > PIP->WRIST + margen (ligeramente sensible)."""
    w, tip, pip = pts[WRIST], pts[TIP[finger]], pts[PIP[finger]]
    return dist(tip, w) > dist(pip, w) + 0.05  # antes 0.07

def finger_curl(pts, finger):
    """Positivo si el dedo está curvo (TIP más cerca del MCP que el PIP)."""
    tip_mcp = dist(pts[TIP[finger]], pts[MCP[finger]])
    pip_mcp = dist(pts[PIP[finger]], pts[MCP[finger]])
    return pip_mcp - tip_mcp

def thumb_index_tip_distance(pts):  return dist(pts[TIP["thumb"]],  pts[TIP["index"]])
def index_middle_tip_distance(pts): return dist(pts[TIP["index"]], pts[TIP["middle"]])
def ring_pinky_tip_distance(pts):   return dist(pts[TIP["ring"]],   pts[TIP["pinky"]])

def finger_dir(pts, finger): return pts[TIP[finger]] - pts[MCP[finger]]

def angle(u, v):
    u = u / (np.linalg.norm(u) + 1e-8)
    v = v / (np.linalg.norm(v) + 1e-8)
    return float(np.arccos(np.clip((u * v).sum(), -1.0, 1.0)))

def group_distance(pts, tips=("index","middle","ring","pinky")):
    """Dispersión de puntas: cuán abiertos están los 4 dedos largos."""
    arr = np.stack([pts[TIP[t]] for t in tips], axis=0)
    c = arr.mean(axis=0)
    return float(np.mean(np.linalg.norm(arr - c, axis=1)))


# ---------- clasificador heurístico (mejorado para 'C') ----------
def classify_letter(pts):
    ext = {f: is_finger_extended(pts, f) for f in TIP.keys()}
    d_ti = thumb_index_tip_distance(pts)  # apertura entre pulgar e índice

    # Curvatura promedio de los 4 dedos largos
    curl_vals = [finger_curl(pts, f) for f in ["index","middle","ring","pinky"]]
    curl_mean = float(np.mean(curl_vals))

    # direcciones y paralelismos
    dir_idx, dir_mid, dir_thumb = finger_dir(pts,"index"), finger_dir(pts,"middle"), finger_dir(pts,"thumb")
    x_axis = np.array([1.0, 0.0], dtype=np.float32)
    ang_idx_x  = angle(dir_idx, x_axis)
    ang_mid_x  = angle(dir_mid, x_axis)
    ang_idx_mid = angle(dir_idx, dir_mid)
    ang_idx_thumb = angle(dir_idx, dir_thumb)
    spread = group_distance(pts)

    # ========= Letras con reglas dedicadas =========

    # C: dedos extendidos pero CURVOS (mano arqueada), apertura moderada,
    #    pulgar oponiéndose al índice (aprox 60°–140°), y dedos no demasiado juntos.
    if (ext["thumb"] and ext["index"] and ext["middle"] and ext["ring"] and ext["pinky"]
        and curl_mean > 0.02                          # dedos arqueados (no rectos)
        and 0.10 <= d_ti <= 0.45                      # apertura razonable de la "C" (más amplio el máximo)
        and 1.05 <= (ang_idx_thumb) <= 2.45           # ~60° a ~140° en radianes
        and spread >= 0.05):                          # algo de separación entre puntas
        return "C"

    # E: puño con puntas recogidas (pulgar cubre/adelante). Distingue de A/S
    if (not ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]
        and curl_mean > 0.04 and d_ti < 0.14):
        return "E"

    # G: índice y pulgar extendidos casi paralelos y horizontales
    if (ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]
        and ext["thumb"] and ang_idx_x < 0.45 and angle(dir_idx, dir_thumb) < 0.6):
        return "G"

    # H: índice y medio extendidos, casi paralelos y horizontales; resto doblado y pulgar no extendido
    if (ext["index"] and ext["middle"] and not ext["ring"] and not ext["pinky"] and not ext["thumb"]
        and ang_idx_mid < 0.35 and max(ang_idx_x, ang_mid_x) < 0.5):
        return "H"

    # ========= Otras letras base =========
    if (not ext["thumb"] and all(ext[f] for f in ["index","middle","ring","pinky"])): return "B"
    if (ext["index"] and ext["thumb"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]): return "L"
    if (ext["index"] and ext["middle"] and not ext["ring"] and not ext["pinky"] and not ext["thumb"]):  return "V"
    if (ext["index"] and ext["middle"] and ext["ring"] and not ext["pinky"] and not ext["thumb"]):      return "W"
    if (ext["thumb"] and not ext["index"] and not ext["middle"] and not ext["ring"] and ext["pinky"]):  return "Y"
    if (ext["index"] and not ext["middle"] and not ext["ring"] and not ext["pinky"]):                   return "D"
    if d_ti < 0.15 and (ext["middle"] or ext["ring"] or ext["pinky"]):                                   return "F"

    # Puño por defecto => A (sin distinguir S)
    if not any([ext["index"], ext["middle"], ext["ring"], ext["pinky"]]): return "A"

    return "?"


# ---------- suavizado temporal (evita “parpadeo”) ----------
last_preds = deque(maxlen=7)


@app.route("/detectar-senas", methods=["POST"])
def detectar_senas():
    data = request.json or {}
    frame_data = data.get("frame")
    if not frame_data:
        return jsonify({"error": "No frame recibido"}), 400

    try:
        _, b64 = frame_data.split(",", 1)
    except ValueError:
        b64 = frame_data
    frame = cv2.imdecode(np.frombuffer(base64.b64decode(b64), np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({"error": "Frame inválido"}), 400

    # --- MediaPipe ---
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    letra = "?"
    if res.multi_hand_landmarks:
        hand_landmarks = res.multi_hand_landmarks[0]

        # 1) DIBUJAR landmarks y conexiones (lo querías activo)
        mp_draw.draw_landmarks(
            frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
            mp_draw.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=3),
            mp_draw.DrawingSpec(color=(255,0,0), thickness=2)
        )

        # 2) Normalizar y clasificar
        pts = norm_landmarks(hand_landmarks.landmark)
        letra = classify_letter(pts)

    # Suavizado: moda de los últimos frames válidos
    if letra != "?":
        last_preds.append(letra)
    letra_estable = Counter(last_preds).most_common(1)[0][0] if last_preds else "?"

    # **DEBUG visual**: pinta la letra arriba a la izquierda
    cv2.rectangle(frame, (8, 8), (140, 48), (0, 0, 0), thickness=-1)
    cv2.putText(frame, f"Letra: {letra_estable}", (16, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2, cv2.LINE_AA)

    # Devuelve frame + letra
    _, buf = cv2.imencode(".jpg", frame)
    img64 = base64.b64encode(buf).decode("utf-8")
    return jsonify({"frame": f"data:image/jpeg;base64,{img64}", "letra": letra_estable})


if __name__ == "__main__":
    # Render usa PORT del entorno
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
