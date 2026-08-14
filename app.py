import os

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
)
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from audio_processor import extract_audio_metadata
from database import get_db_connection


app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"wav", "mp3", "m4a", "ogg", "flac"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit_audio():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    audio_file = request.files.get("audio")

    if not name or not phone or not audio_file:
        return "Name, phone number, and audio file are required.", 400

    if audio_file.filename == "":
        return "Please select an audio file.", 400

    if not allowed_file(audio_file.filename):
        return "Unsupported audio format.", 400

    original_filename = secure_filename(audio_file.filename)

    name, extension = os.path.splitext(original_filename)

    filename = f"{phone}_{name}_{os.urandom(8).hex()}{extension}"

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename,
    )

    audio_file.save(file_path)

    metadata = extract_audio_metadata(file_path)

    connection = get_db_connection()

    entity = connection.execute(
        """
        SELECT entity_id
        FROM entities
        WHERE phone = ?
        LIMIT 1
        """,
        (phone,),
    ).fetchone()

    if entity is None:
        connection.close()
        return "No matching worker found for this phone number.", 404

    connection.execute(
        """
        INSERT INTO audio_submissions (
            entity_id,
            audio_filename,
            audio_path,
            duration_seconds,
            sample_rate_khz,
            bitrate_kbps,
            loudness_db,
            quality_score
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entity["entity_id"],
            filename,
            file_path,
            metadata["duration_seconds"],
            metadata["sample_rate_khz"],
            metadata["bitrate_kbps"],
            metadata["loudness_db"],
            metadata["quality_score"],
        ),
    )

    connection.commit()
    connection.close()

    return redirect(url_for("submissions"))


@app.route("/submissions")
def submissions():
    connection = get_db_connection()

    rows = connection.execute(
        """
        SELECT
            a.submission_id,
            e.name,
            e.phone,
            a.audio_filename,
            a.audio_path,
            a.duration_seconds,
            a.sample_rate_khz,
            a.bitrate_kbps,
            a.loudness_db,
            a.quality_score,
            a.created_at
        FROM audio_submissions a
        JOIN entities e
            ON a.entity_id = e.entity_id
        ORDER BY a.submission_id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "submissions.html",
        submissions=rows,
    )


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
    )


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    return "Audio file is too large. Maximum allowed size is 25 MB.", 413


if __name__ == "__main__":
    app.run(debug=True)