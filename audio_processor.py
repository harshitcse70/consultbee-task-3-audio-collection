from pydub import AudioSegment
import subprocess
import json


def extract_audio_metadata(file_path):
    """
    Extract audio metadata using FFmpeg and pydub.

    Returns:
        dict containing:
        - duration_seconds
        - sample_rate_khz
        - bitrate_kbps
        - loudness_db
    """

    # Get technical metadata using FFprobe
    command = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True
    )

    metadata = json.loads(result.stdout)

    audio_stream = next(
        stream
        for stream in metadata["streams"]
        if stream["codec_type"] == "audio"
    )

    # Duration
    duration = float(
        metadata["format"].get("duration", 0)
    )

    # Sample rate
    sample_rate = int(
        audio_stream.get("sample_rate", 0)
    )

    # Bitrate
    bitrate = audio_stream.get("bit_rate")

    if bitrate is None:
        bitrate = metadata["format"].get("bit_rate")

    bitrate_kbps = (
        float(bitrate) / 1000
        if bitrate
        else 0
    )

    # Loudness approximation using pydub
    audio = AudioSegment.from_file(file_path)

    loudness_db = audio.dBFS

     # Rough quality estimate based on loudness.
    # This is a heuristic, not professional noise analysis.
    if -30 <= loudness_db <= -12:
        quality_score = 1.0
    elif -40 <= loudness_db < -30 or -12 < loudness_db <= -6:
        quality_score = 0.7
    else:
        quality_score = 0.4

    return {
        "duration_seconds": round(duration, 2),
        "sample_rate_khz": round(sample_rate / 1000, 2),
        "bitrate_kbps": round(bitrate_kbps, 2),
        "loudness_db": round(loudness_db, 2),
        "quality_score": quality_score
    }