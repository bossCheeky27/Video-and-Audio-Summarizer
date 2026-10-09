import os
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

import database as db
from config import UPLOAD_FOLDER, EXTRACTED_FOLDER, PORT
from services.transcriber import transcribe_video
from services.pdf_processor import process_pdf
from services.summarizer import generate_summary_chunked

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB max upload

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mkv', 'avi', 'mov', 'webm', 'm4a', 'mp3', 'wav'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}


def allowed_video(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def allowed_pdf(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PDF_EXTENSIONS


def process_lecture(lecture_id, video_path, pdf_path):
    """Background task to process a lecture."""
    try:
        # Reuse existing transcript if available
        existing = db.get_lecture(lecture_id)
        transcript = existing['transcript'] or "" if existing else ""
        slide_text = ""
        image_paths = []

        # Transcribe video (skipped if transcript already exists)
        if video_path and not transcript:
            db.update_lecture_status(lecture_id, 'transcribing')
            print(f"Transcribing video for lecture {lecture_id}...")
            transcript = transcribe_video(video_path, lecture_id=lecture_id)
            db.update_lecture_transcript(lecture_id, transcript)
            print(f"Transcription complete for lecture {lecture_id}")

        # Process PDF
        if pdf_path:
            db.update_lecture_status(lecture_id, 'extracting')
            print(f"Processing PDF for lecture {lecture_id}...")
            slide_text, image_paths = process_pdf(pdf_path, lecture_id)

            # Save image references to database
            for img in image_paths:
                db.add_slide_image(lecture_id, img['path'], img['page'])

            print(f"PDF processing complete for lecture {lecture_id}")

        # Generate summary
        if transcript or slide_text:
            db.update_lecture_status(lecture_id, 'summarizing')
            db.update_lecture_progress(lecture_id, 0)
            print(f"Generating summary for lecture {lecture_id}...")
            summary = generate_summary_chunked(transcript, slide_text, lecture_id=lecture_id)
            db.update_lecture_summary(lecture_id, summary)
            print(f"Summary complete for lecture {lecture_id}")
        else:
            db.update_lecture_status(lecture_id, 'error')

    except Exception as e:
        print(f"Error processing lecture {lecture_id}: {e}")
        db.update_lecture_status(lecture_id, 'error')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    video_file = request.files['video']
    pdf_file = request.files.get('pdf')

    if video_file.filename == '':
        return jsonify({'error': 'No video file selected'}), 400

    if not allowed_video(video_file.filename):
        return jsonify({'error': 'Invalid video format'}), 400

    # Save video file
    video_filename = secure_filename(video_file.filename)
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
    video_file.save(video_path)

    # Save PDF file if provided
    pdf_path = None
    if pdf_file and pdf_file.filename != '' and allowed_pdf(pdf_file.filename):
        pdf_filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        pdf_file.save(pdf_path)

    # Create lecture title from video filename
    title = os.path.splitext(video_filename)[0]

    # Create database record
    lecture_id = db.create_lecture(title, video_path, pdf_path)

    # Start background processing
    thread = threading.Thread(
        target=process_lecture,
        args=(lecture_id, video_path, pdf_path)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'lecture_id': lecture_id,
        'message': 'Processing started'
    })


@app.route('/status/<int:lecture_id>')
def get_status(lecture_id):
    lecture = db.get_lecture(lecture_id)
    if not lecture:
        return jsonify({'error': 'Lecture not found'}), 404

    return jsonify({
        'id': lecture['id'],
        'title': lecture['title'],
        'status': lecture['status'],
        'progress': lecture.get('progress', 0) or 0
    })


@app.route('/lectures')
def get_lectures():
    lectures = db.get_all_lectures()
    return jsonify(lectures)


@app.route('/lecture/<int:lecture_id>')
def get_lecture(lecture_id):
    lecture = db.get_lecture(lecture_id)
    if not lecture:
        return jsonify({'error': 'Lecture not found'}), 404

    return jsonify(lecture)


@app.route('/lecture/<int:lecture_id>/retry', methods=['POST'])
def retry_lecture(lecture_id):
    lecture = db.get_lecture(lecture_id)
    if not lecture:
        return jsonify({'error': 'Lecture not found'}), 404

    if lecture['status'] != 'error':
        return jsonify({'error': 'Lecture is not in error state'}), 400

    # Resume from where it left off
    video_path = lecture['video_path'] if not lecture['transcript'] else None
    pdf_path = lecture['pdf_path']

    db.update_lecture_status(lecture_id, 'pending')
    db.update_lecture_progress(lecture_id, 0)

    thread = threading.Thread(
        target=process_lecture,
        args=(lecture_id, video_path, pdf_path)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'success': True, 'lecture_id': lecture_id})


@app.route('/lecture/<int:lecture_id>', methods=['DELETE'])
def delete_lecture(lecture_id):
    lecture = db.get_lecture(lecture_id)
    if not lecture:
        return jsonify({'error': 'Lecture not found'}), 404

    # Delete associated files
    if lecture['video_path'] and os.path.exists(lecture['video_path']):
        os.remove(lecture['video_path'])
    if lecture['pdf_path'] and os.path.exists(lecture['pdf_path']):
        os.remove(lecture['pdf_path'])

    # Delete extracted images folder
    lecture_images_folder = os.path.join(EXTRACTED_FOLDER, str(lecture_id))
    if os.path.exists(lecture_images_folder):
        import shutil
        shutil.rmtree(lecture_images_folder)

    # Delete from database
    db.delete_lecture(lecture_id)

    return jsonify({'success': True})


@app.route('/static/uploads/extracted/<path:filename>')
def serve_extracted_image(filename):
    return send_from_directory(EXTRACTED_FOLDER, filename)


if __name__ == '__main__':
    db.init_db()
    print("Starting Lecture Summarizer...")
    print(f"Open http://localhost:{PORT} in your browser")
    app.run(debug=True, port=PORT)
