from flask import Flask, render_template, request, send_file
from utils import extract_video_id, get_transcript, generate_article, save_pdf

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    article = None

    if request.method == "POST":
        url = request.form["url"]

        video_id = extract_video_id(url)
        if not video_id:
            return "Invalid YouTube URL"

        transcript = get_transcript(video_id)
        article = generate_article(transcript)

        save_pdf(article)

    return render_template("index.html", article=article)


@app.route("/download")
def download():
    return send_file("output.pdf", as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)