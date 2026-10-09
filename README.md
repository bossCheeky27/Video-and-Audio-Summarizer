# Video and Audio Summarizer

Turn recorded lectures into transcripts and structured study notes.

This repo has two tools:

- **Lecture Summarizer** (`lecture_summarizer/`): a local web app. Upload a lecture recording, plus the slides PDF if you have it. The app transcribes the recording with [faster-whisper](https://github.com/SYSTRAN/faster-whisper), pulls the text and images out of the slides, and asks Google Gemini to write organised lecture notes.
- **Batch transcriber** (`transcribe.bat` / `transcribe.sh`): turns every recording in the repo folder into a `.txt` transcript with [OpenAI Whisper](https://github.com/openai/whisper). It doesn't need an API key.

Both tools run on Windows, macOS and Linux. Transcription runs locally on your CPU.

## Supported files

- **Video:** `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`
- **Audio:** `.m4a`, `.mp3`, `.wav`
- **Slides:** `.pdf` (optional, web app only)

The batch transcriber only handles `.mp4`, `.m4a`, `.mp3` and `.wav`.

## Requirements

- Python 3.9 or newer
- [FFmpeg](https://ffmpeg.org/). The setup script installs it if it's missing.
- A free [Gemini API key](https://aistudio.google.com/app/apikey). Only the web app's summaries need one.

## Setup

**Windows**

```bat
setup.bat
```

**macOS / Linux**

```bash
bash setup.sh
```

The setup script does the following:

- installs the Python packages (on macOS and Linux, into a `.venv` folder)
- installs FFmpeg if it's missing (winget on Windows, Homebrew on macOS, your package manager on Linux)
- creates `lecture_summarizer/.env` from `.env.example`

Then open `lecture_summarizer/.env` and set your key:

```
GEMINI_API_KEY=your_api_key_here
```

On Linux, `setup.sh` installs the CPU-only build of PyTorch to avoid a multi-GB download. Run `USE_CUDA=1 bash setup.sh` if you want the GPU build instead.

## Usage

### Web app

| | Windows | macOS / Linux |
|---|---|---|
| Start | `start.bat` | `./start.sh` |
| Stop | `stop.bat` (or close the window) | `./stop.sh` (or Ctrl+C) |

The browser opens automatically once the server is ready. The first start can take 30 seconds or more while the libraries load. By default the app runs at http://localhost:5000. On macOS it uses http://localhost:5001, because AirPlay Receiver uses port 5000 there.

Upload a recording, plus the slides PDF if you have one. Each lecture goes through **transcribing → extracting slides → summarizing**, and the page shows its progress. If the summary step fails, **Retry** reuses the existing transcript, so the recording isn't transcribed again.

### Batch transcriber

Put recordings in the repo's root folder, next to the script, and run it:

| Windows | macOS / Linux |
|---|---|
| `transcribe.bat` | `./transcribe.sh` |

Each file produces a `<name>.txt` transcript next to the script. Once a recording is transcribed, it's moved into `transcribed_lectures/`.

## Configuration

| Setting | Where | Default |
|---|---|---|
| `GEMINI_API_KEY` | `lecture_summarizer/.env` | required for summaries |
| `PORT` | `lecture_summarizer/.env` | `5000` (`5001` on macOS) |
| Whisper model (web app) | `WHISPER_MODEL` in `lecture_summarizer/config.py` | `tiny` |
| Whisper model and language (batch) | top of `transcribe.bat` / `transcribe.sh` | `tiny`, `en` |

Larger Whisper models (`base`, `small`, `medium`) give more accurate transcripts but run slower and use more RAM. `base` is a good choice with 4–8 GB of RAM.

## Project structure

```
├── lecture_summarizer/
│   ├── app.py              # Flask app, upload + background processing
│   ├── config.py           # paths, port, Whisper model, .env loading
│   ├── database.py         # SQLite storage (data/lectures.db)
│   ├── services/
│   │   ├── transcriber.py  # FFmpeg audio extraction + faster-whisper
│   │   ├── pdf_processor.py# slide text/image extraction
│   │   └── summarizer.py   # Gemini summaries (chunked for long lectures)
│   ├── templates/ static/  # web UI
│   └── stop_app.ps1        # used by stop.bat
├── setup.bat / setup.sh
├── start.bat / start.sh
├── stop.bat  / stop.sh
└── transcribe.bat / transcribe.sh
```

## Privacy

Transcription happens on your machine. To make the summaries, the app sends the transcript and the slide text to Google's Gemini API. Uploaded files, transcripts and the lecture database stay in `lecture_summarizer/static/uploads/` and `lecture_summarizer/data/`, and git ignores both folders.

## License

[MIT](LICENSE)
