# app.py
from flask import Flask, request, jsonify, send_file
import subprocess
import os
import requests
import uuid
import tempfile

app = Flask(__name__)

OUTPUT_DIR = "/app/converted"   # inside container path
os.makedirs(OUTPUT_DIR, exist_ok=True)

MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024  # 200 MB cap
REQUEST_TIMEOUT = (5, 60)  # connect timeout 5s, read timeout 60s

@app.route("/convert", methods=["POST"])
def convert():
    data = request.json
    if not data or "url" not in data or "format" not in data:
        return jsonify({"error": "Missing 'url' or 'format'"}), 400

    url = data["url"]
    output_format = data["format"].lower()

    if output_format not in ("mp3", "ogg"):
        return jsonify({"error": "format must be mp3 or ogg"}), 400

    # Download input file safely
    with tempfile.NamedTemporaryFile(suffix=".in", delete=False) as tmp:
        input_file = tmp.name
        try:
            with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT) as r:
                if r.status_code != 200:
                    return jsonify({"error": "Failed to download file"}), 400

                # Basic content-type check (video/audio)
                ct = r.headers.get("content-type", "")
                if not (ct.startswith("video") or ct.startswith("audio") or "octet-stream" in ct):
                    # not definitive, but helps block some wrong URLs
                    return jsonify({"error": f"Unexpected content-type: {ct}"}), 400

                total = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        return jsonify({"error": "File too large"}), 413
                    tmp.write(chunk)
        except requests.RequestException as e:
            return jsonify({"error": f"Download error: {str(e)}"}), 400

    # Convert with ffmpeg (add timeout)
    output_name = f"{uuid.uuid4()}.{output_format}"
    output_file = os.path.join(OUTPUT_DIR, output_name)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_file, "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", output_file],
            check=True,
            timeout=120  # kill ffmpeg if it runs too long
        )
    except subprocess.TimeoutExpired:
        os.remove(input_file)
        return jsonify({"error": "Conversion timeout"}), 504
    except subprocess.CalledProcessError:
        os.remove(input_file)
        return jsonify({"error": "Conversion failed"}), 500
    finally:
        if os.path.exists(input_file):
            os.remove(input_file)

    return jsonify({"output": f"http://{request.host}/download/{output_name}"})

@app.route("/download/<filename>", methods=["GET"])
def download(filename):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
