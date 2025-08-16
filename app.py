# app.py
from flask import Flask, request, jsonify, send_file, abort
import os
import uuid
import subprocess
import shutil

app = Flask(__name__)

BASE_DIR = "/app"
UPLOADS = os.path.join(BASE_DIR, "uploads")
CONVERTED = os.path.join(BASE_DIR, "converted")

os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(CONVERTED, exist_ok=True)

@app.route("/")
def home():
    return jsonify({"message": "Audio Converter API (EasyPanel) is running!"})

@app.route("/convert", methods=["POST"])
def convert():
    """
    POST JSON:
    { "url": "<public file url>", "format": "mp3"|"ogg" } 
    Returns JSON: { "download_url": "/download/<filename>" }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "expected JSON body"}), 400

    url = data.get("url")
    out_fmt = (data.get("format") or "mp3").lower()
    if not url:
        return jsonify({"error": "missing 'url'"}), 400
    if out_fmt not in ("mp3", "ogg"):
        return jsonify({"error": "format must be 'mp3' or 'ogg'"}), 400

    uid = uuid.uuid4().hex
    input_path = os.path.join(UPLOADS, f"{uid}.input")
    output_name = f"{uid}.{out_fmt}"
    output_path = os.path.join(CONVERTED, output_name)

    try:
        # Download input file with wget (works in many base images)
        cmd_dl = ["wget", "-q", "-O", input_path, url]
        subprocess.run(cmd_dl, check=True)

        # Convert using ffmpeg (strip video if any, set reasonable audio params)
        cmd_ff = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", input_path,
            "-vn",                        # no video
            "-ar", "44100",               # sample rate
            "-ac", "2",                   # channels
            "-b:a", "192k",               # bitrate
            output_path
        ]
        subprocess.run(cmd_ff, check=True)

        # Optionally remove input to save space
        try:
            os.remove(input_path)
        except OSError:
            pass

        # Return a path the user (or n8n) can download from (reverse-proxied by EasyPanel)
        download_url = f"/download/{output_name}"
        return jsonify({"download_url": download_url}), 200

    except subprocess.CalledProcessError as e:
        # cleanup on failure
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        return jsonify({"error": "processing failed", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download/<filename>", methods=["GET"])
def download(filename):
    safe_name = os.path.basename(filename)
    path = os.path.join(CONVERTED, safe_name)
    if not os.path.exists(path):
        abort(404)
    # serve file as attachment
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    # debug only; EasyPanel uses gunicorn
    app.run(host="0.0.0.0", port=8080)
