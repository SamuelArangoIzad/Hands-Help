
---

# Hands-Help 🤲✨

**Welcome to the future of inclusive communication.**

Hands-Help is a technological tool designed to bridge the gap between spoken/written language and sign language. It provides both **text-to-sign translation** (via images) and **real-time sign-to-text recognition** (via webcam and computer vision).

🌐 **Live demo:** [Hands-Help on GitHub Pages](https://samuelarangolzad.github.io/Hands-Help/)
🖥️ **Backend API:** [Hands-Help on Render](https://hands-help.onrender.com)

---

## 🚀 Project Overview

Hands-Help is composed of two main components:

1. **Backend (Flask + MediaPipe + OpenCV)**

   * Deployed on [Render](https://render.com).
   * Handles REST API endpoints for:

     * Translating text into sign images.
     * Recognizing hand signs via MediaPipe Hands and returning the detected letter.
   * Optimized for limited resources (free Render tier) with:

     * Python 3.11.9 runtime.
     * Gunicorn process manager.
     * Lightweight OpenCV (`opencv-contrib-python-headless`).

2. **Frontend (Static HTML/CSS/JS)**

   * Hosted on **GitHub Pages**.
   * Provides a modern interface for both modes:

     * **Text → Signs:** Displays sign images sequentially for each letter.
     * **Signs → Text:** Uses webcam frames sent to backend for real-time recognition.
   * Responsive UI built with clean typography, pill-style buttons, and split-panel layout.

---

## ⚙️ Architecture

```
+------------------+       HTTPS        +-----------------------+
|   GitHub Pages   |  <----------------> |  Render (Flask API)   |
| (Frontend UI)    |                     | /traducir             |
| - index.html     |                     | /detectar-senas       |
| - app.js         |                     | Flask-CORS enabled    |
+------------------+                     +-----------------------+
```

* **Frontend → Backend communication:**

  * `fetch` requests with `mode: "cors"`.
  * API base URL is injected via JS constant (`API_BASE`).
* **CORS configuration:**

  * Allowed origins: GitHub Pages domain + localhost for dev.

---

## 🛠️ Backend Configuration (Render)

* **Root Directory:** `backend/`
* **runtime.txt:**

  ```
  python-3.11.9
  ```
* **requirements.txt (minimal):**

  ```
  Flask==3.0.3
  Flask-Cors==4.0.1
  gunicorn==21.2.0
  numpy==1.26.4
  opencv-contrib-python-headless==4.10.0.84
  mediapipe==0.10.14
  ```
* **Build Command:**

  ```
  pip install --upgrade pip && pip install -r requirements.txt
  ```
* **Start Command:**

  ```
  gunicorn app:app --timeout 120 --workers 1 --threads 4
  ```

---

## 🌐 Frontend Configuration (GitHub Pages)

* **Branch:** `main`
* **Deployment:** via GitHub Actions workflow (`.github/workflows/deploy.yml`)
* **Workflow steps:**

  * Copy `frontend/` and `database/` into a `public/` folder.
  * Auto-generate `404.html` from `index.html` to support SPA routing.
  * Deploy artifact to `gh-pages` branch.

Sample workflow snippet:

```yaml
- name: Prepare static site
  run: |
    rm -rf public
    mkdir -p public
    cp -r frontend/* public/
    cp -r database public/database
    if [ ! -f public/404.html ]; then cp public/index.html public/404.html; fi
```

---

## 📦 Features

* **Text-to-Sign Translation:**
  Input text → Backend returns corresponding sign images from dictionary → Frontend displays them sequentially.

* **Sign-to-Text Recognition:**
  Webcam capture → Frames compressed & sent to backend → MediaPipe extracts hand landmarks → Heuristic classifier detects letter → Text displayed in real time.

* **Optimizations for Render Free Tier:**

  * Input frames resized (≤ 480px).
  * JPEG compression \~0.45.
  * Throttled to \~2–3 FPS to avoid timeouts.
  * Backend disables annotated frame return by default to save resources.

---

## 🧑‍💻 Development Setup

Clone repository:

```
git clone https://github.com/SamuelArangoIzad/Hands-Help.git
cd Hands-Help
```

### Backend (local run)

```
cd backend
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python app.py
```

Runs at: `http://localhost:5000`

### Frontend (local preview)

Open `frontend/index.html` in browser or serve with:

```
cd frontend
python -m http.server 5500
```

---

## 🔮 Future Improvements

* Extend detection to full words and gestures, not just single letters.
* Integrate with cloud storage for custom sign dictionaries.
* Improve ML classifier accuracy with real datasets.
* Add multilingual support.

---

## 📄 License

MIT License © 2025 — Hands-Help Project

---

## 🤝 Acknowledgements

* [MediaPipe](https://developers.google.com/mediapipe) for real-time hand landmark detection.
* [OpenCV](https://opencv.org/) for image processing.
* [Render](https://render.com/) for free backend hosting.
* [GitHub Pages](https://pages.github.com/) for frontend deployment.

---

**Hands-Help** — *“Technology that speaks with hands.”* ✋💙

---
