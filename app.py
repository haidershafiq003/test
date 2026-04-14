from flask import Flask, request, render_template_string, send_file
import yt_dlp
import os

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Private Video Downloader</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>
body {
    margin: 0;
    font-family: Arial;
    color: white;
    text-align: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #6e1dab, #290d41, #61168a);
}

h1 { margin-top: 60px; font-size: 42px; }

input {
    padding: 12px;
    width: 60%;
    max-width: 400px;
    border-radius: 10px;
    border: none;
}

button {
    padding: 12px 18px;
    border: none;
    border-radius: 10px;
    background: linear-gradient(90deg, #ff416c, #ff4b2b);
    color: white;
    cursor: pointer;
}

.main {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-top: 30px;
    flex-wrap: wrap;
}

.left, .right {
    width: 320px;
    background: rgba(255,255,255,0.08);
    padding: 15px;
    border-radius: 15px;
}

.left img {
    width: 100%;
    border-radius: 12px;
}

.section { margin-bottom: 20px; }

.flex-form {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

select {
    flex: 1;
    padding: 10px;
    border-radius: 10px;
    border: none;
}

/* MESSAGE */
.msg {
    margin-top: 10px;
    font-weight: bold;
    color: #ff4b4b;
}

.success {
    color: #00ff99;
}

</style>
</head>

<body>

<h1>Private Video Downloader</h1>

<form method="POST">
    <input type="text" name="url" placeholder="Paste YouTube link" required value="{{ url }}">
    <button name="action" value="fetch">Fetch</button>
</form>

{% if error %}
<p class="msg">{{ error }}</p>
{% endif %}

{% if thumbnail %}

<div class="main">

    <div class="left">
        <img src="{{ thumbnail }}">
    </div>

    <div class="right">

        <div class="section">
            <h3>Video Quality</h3>
            <form method="POST" class="flex-form">
                <input type="hidden" name="url" value="{{ url }}">

                <select name="format">
                    {% for f in formats.video %}
                    <option value="{{ f.format_id }}">{{ f.resolution }}</option>
                    {% endfor %}
                </select>

                <button name="action" value="download_video">Download Video</button>
            </form>
        </div>

        <div class="section">
            <h3>Audio Quality</h3>
            <form method="POST" class="flex-form">
                <input type="hidden" name="url" value="{{ url }}">

                <select name="format">
                    {% for f in formats.audio %}
                    <option value="{{ f.format_id }}">{{ f.abr }} kbps</option>
                    {% endfor %}
                </select>

                <button name="action" value="download_audio">Download Audio</button>
            </form>
        </div>

    </div>

</div>

{% endif %}

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    formats = None
    url = ""
    thumbnail = None
    error = None

    if request.method == "POST":
        url = request.form.get("url", "")
        action = request.form.get("action")

        # ---------------- FETCH ----------------
        if action == "fetch":
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(url, download=False)

                thumbnail = info.get("thumbnail")

                video_formats = []
                audio_formats = []

                for f in info["formats"]:
                    if f.get("vcodec") != "none" and f.get("acodec") == "none" and f.get("height"):
                        video_formats.append({
                            "format_id": f["format_id"],
                            "resolution": f"{f.get('height')}p"
                        })

                    if f.get("acodec") != "none" and f.get("vcodec") == "none":
                        audio_formats.append({
                            "format_id": f["format_id"],
                            "abr": f.get("abr") or "audio"
                        })

                video_formats = sorted(
                    video_formats,
                    key=lambda x: int(x["resolution"].replace("p","")),
                    reverse=True
                )

                formats = {"video": video_formats, "audio": audio_formats}

            except Exception:
                return render_template_string(
                    HTML,
                    formats=None,
                    url="",
                    thumbnail=None,
                    error="❌ Wrong or invalid link!"
                )

            return render_template_string(
                HTML,
                formats=formats,
                url=url,
                thumbnail=thumbnail,
                error=None
            )

        # ---------------- DOWNLOAD VIDEO ----------------
        if action == "download_video":
            try:
                fmt = request.form["format"]

                ydl_opts = {
                    'format': f'{fmt}+bestaudio',
                    'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s_%(format_id)s.%(ext)s',
                    'merge_output_format': 'mp4',
                    'ffmpeg_location': 'ffmpeg',
                    'noplaylist': True
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                files = [os.path.join(DOWNLOAD_FOLDER, f) for f in os.listdir(DOWNLOAD_FOLDER)]
                latest = max(files, key=os.path.getctime)

                return send_file(latest, as_attachment=True)

            except Exception:
                return render_template_string(HTML, formats=None, url="", thumbnail=None, error="❌ Download failed!")

        # ---------------- DOWNLOAD AUDIO ----------------
        if action == "download_audio":
            try:
                fmt = request.form["format"]

                ydl_opts = {
                    'format': fmt,
                    'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s_%(format_id)s.%(ext)s',
                    'ffmpeg_location': 'ffmpeg',
                    'noplaylist': True
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                files = [os.path.join(DOWNLOAD_FOLDER, f) for f in os.listdir(DOWNLOAD_FOLDER)]
                latest = max(files, key=os.path.getctime)

                return send_file(latest, as_attachment=True)

            except Exception:
                return render_template_string(HTML, formats=None, url="", thumbnail=None, error="❌ Audio download failed!")

    return render_template_string(HTML, formats=formats, url=url, thumbnail=thumbnail, error=error)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
