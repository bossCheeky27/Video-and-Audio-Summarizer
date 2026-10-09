import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Web server port - macOS 12+ uses 5000 for AirPlay Receiver, so default to 5001 there
PORT = int(os.getenv('PORT') or (5001 if sys.platform == 'darwin' else 5000))

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
EXTRACTED_FOLDER = os.path.join(UPLOAD_FOLDER, 'extracted')
DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'lectures.db')

# Whisper model - 'base' is good for 4-8GB RAM
WHISPER_MODEL = 'tiny'

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
