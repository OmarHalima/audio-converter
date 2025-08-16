from flask import Flask, request, jsonify
import os
import uuid
import subprocess

app = Flask(__name__)

UPLOAD_FOLDER = "/app/uploads"
CONVERTED_FOLDER = "/app/converted"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@app.route("/convert", methods=["POST"])
def convert():
    try:
        data = request.get_json()
        url = data.get("url")
        output_format = data.get("format", "mp3")

        if not url:
            return jsonify({"error": "No URL provided"}), 400

        # Download input file
        input_file = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.input")
        subprocess.run(["wget", "-O", input_file, url], check=True)

        # Convert file
        output_file = os.path.join(CONVERTED_FOLDER, f"{uuid.uuid4()}.{output_format}")
        subprocess.run(["ffmpeg", "-i", input_file, output_file], check=True)

        return jsonify({"output": output_file})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Audio Converter API is running!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
