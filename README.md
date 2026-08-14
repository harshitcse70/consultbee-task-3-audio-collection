# ConsultBae Task 3 — Mini Audio Collection App

A miniature audio collection system built for the ConsultBae AI Automation assignment.

The application allows workers to submit an audio recording along with their name and phone number. The uploaded audio is stored locally, analyzed automatically using FFmpeg, and the extracted properties are stored in the SQLite database used by Task 1.

## Features

- Worker name and phone number input
- Audio file upload
- Supported formats:
  - WAV
  - MP3
  - M4A
  - OGG
  - FLAC
- 25 MB upload size limit
- Unique filenames to prevent upload collisions
- Automatic audio metadata extraction:
  - Duration
  - Sample rate
  - Bitrate
  - Loudness
- Rough audio quality score
- SQLite database integration
- Submission history page
- Browser-based audio playback
- Simple responsive UI

## Architecture

```text
                    ┌─────────────────────┐
                    │     Web Browser     │
                    │                     │
                    │ Name + Phone        │
                    │ Audio Upload        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       Flask         │
                    │                     │
                    │ Upload validation   │
                    │ Worker lookup       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Audio Processor    │
                    │                     │
                    │ FFmpeg / FFprobe    │
                    │ pydub               │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
      ┌───────────────┐                 ┌────────────────┐
      │ uploads/      │                 │ SQLite         │
      │               │                 │                │
      │ Audio files   │                 │ entities       │
      │               │                 │ entity_sources │
      └───────────────┘                 │ audio_submissions
                                        └────────────────┘
                                                  │
                                                  ▼
                                      ┌────────────────────┐
                                      │ Submissions View   │
                                      │                    │
                                      │ Audio Player       │
                                      │ Metadata           │
                                      │ Quality Score      │
                                      └────────────────────┘
```

## Project Structure

```text
consultbee-task-3-audio-collection/
│
├── app.py
├── audio_processor.py
├── database.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   └── consultbae.db
│
├── uploads/
│   └── .gitkeep
│
├── static/
│   └── style.css
│
└── templates/
    ├── index.html
    └── submissions.html
```

## Database

The application uses SQLite.

The database contains the Task 1 tables:

* `entities`
* `entity_sources`

Task 3 adds:

* `audio_submissions`

### `audio_submissions`

| Column             | Description                            |
| ------------------ | --------------------------------------- |
| `submission_id`    | Unique submission ID                   |
| `entity_id`        | Links the recording to a Task 1 entity |
| `audio_filename`   | Stored audio filename                  |
| `audio_path`       | Local audio path                       |
| `duration_seconds` | Audio duration                         |
| `sample_rate_khz`  | Sample rate in kHz                     |
| `bitrate_kbps`     | Audio bitrate                          |
| `loudness_db`      | Measured loudness                      |
| `quality_score`    | Rough quality estimate                 |
| `created_at`       | Submission timestamp                   |

## Audio Processing

FFmpeg/FFprobe is used to extract technical audio information.

For each uploaded audio file the application extracts:

### Duration

Total length of the recording in seconds.

### Sample Rate

The sampling frequency of the audio, stored in kHz.

Example:

```text
44.1 kHz
```

### Bitrate

The audio bitrate, stored in kbps.

Example:

```text
705.6 kbps
```

### Loudness

The audio signal level is estimated using pydub.

Example:

```text
-5.01 dB
```

## Quality Estimate

The application includes a simple quality heuristic based on the measured loudness.

This is intentionally a rough estimate rather than a professional noise-detection system.

Current scoring:

```text
Good range:
-30 dB to -12 dB → 1.0

Acceptable range:
-40 dB to below -30 dB
or
above -12 dB to -6 dB → 0.7

Outside these ranges → 0.4
```

This was implemented as a bonus feature because the assignment describes noise/quality estimation as optional.

## Task 1 Integration

Task 3 reuses the SQLite database created in Task 1.

When a worker submits audio:

```text
Phone Number
     ↓
entities table
     ↓
entity_id
     ↓
audio_submissions
```

This keeps the audio submission connected to an existing worker/entity instead of creating duplicate worker records.

## Installation

### 1. Clone the repository

```bash
git clone 
cd consultbee-task-3-audio-collection
```

### 2. Create a virtual environment

Windows:

```cmd
python -m venv venv
```

Activate:

```cmd
venv\Scripts\activate
```

### 3. Install Python dependencies

```cmd
pip install -r requirements.txt
```

### 4. Install FFmpeg

FFmpeg must be installed separately and available in the system PATH.

Verify:

```cmd
ffmpeg -version
```

and:

```cmd
ffprobe -version
```

## Run the Application

Start Flask:

```cmd
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Application Pages

### Submission Page

```text
/
```

Allows a worker to enter:

* Name
* Phone number
* Audio file

### Submissions Page

```text
/submissions
```

Displays:

* Worker name
* Phone number
* Audio player
* Duration
* Sample rate
* Bitrate
* Loudness
* Quality score
* Submission timestamp

## Upload Safety

The application includes:

* Allowed audio extensions
* Secure filename handling
* 25 MB upload limit
* Unique stored filenames

Unique filenames prevent two workers uploading files with the same original filename from overwriting each other.

## Technology Stack

* Python
* Flask
* SQLite
* FFmpeg
* FFprobe
* pydub
* HTML
* CSS
* Git / GitHub

## Assignment Requirement Mapping

| Requirement             | Implementation             |
| ------------------------ | --------------------------- |
| Web page                | Flask application          |
| Name input              | HTML form                  |
| Phone input             | HTML form                  |
| Record or upload audio  | Audio file upload          |
| Store audio             | `uploads/`                 |
| Store database record   | SQLite `audio_submissions` |
| Duration                | FFprobe                    |
| Sample rate             | FFprobe                    |
| Bitrate                 | FFprobe                    |
| Loudness                | pydub                      |
| Quality/noise estimate  | Loudness-based heuristic   |
| Second submissions view | `/submissions`             |
| Play button             | HTML5 audio player         |
| Extracted properties    | Submissions page           |
| Free/local demo         | Flask local server         |

## Design Decisions

### Why Flask?

The application is intentionally small, so Flask provides enough functionality without adding unnecessary framework complexity.

### Why SQLite?

SQLite was already used in Task 1, making it practical to reuse the same database and maintain a consistent entity relationship.

### Why FFmpeg?

FFmpeg provides reliable audio format handling and FFprobe exposes technical metadata such as duration, sample rate and bitrate.

### Why upload instead of browser recording?

The assignment allows either browser recording or audio upload. Uploading provides a simpler and reliable implementation while satisfying the requirement.

## Limitations

This is a miniature demonstration application rather than a production-scale audio platform.

Current limitations include:

* Local file storage
* SQLite database
* Basic authentication/security
* Basic quality heuristic
* No cloud object storage
* No background processing queue

For a production implementation, audio files could be stored in object storage such as S3 and audio processing could be moved to asynchronous workers.

## Development History

The project was developed incrementally using Git commits.

Major milestones include:

* Database integration
* Audio metadata extraction
* Audio submission workflow
* Quality estimation
* Upload validation
* UI improvements
* Filename collision prevention
