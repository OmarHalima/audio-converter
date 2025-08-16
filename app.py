# app.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "API is running on EasyPanel!"})

@app.route("/convert", methods=["POST"])
def convert():
    data = request.json
    return jsonify({"received": data})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
