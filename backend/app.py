from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permite que el frontend pueda hacer peticiones

@app.route("/")
def home():
    return {"message": "Backend funcionando 🚀"}

# Ruta para traducir texto a señas (ejemplo inicial)
@app.route("/traducir", methods=["POST"])
def traducir():
    data = request.json
    texto = data.get("texto", "")

    # Por ahora, solo devolvemos cada letra en una lista
    traduccion = list(texto)

    return jsonify({
        "original": texto,
        "traduccion": traduccion
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
