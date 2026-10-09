// State
let selectedVideo = null;
let selectedPdf = null;
let currentLectureId = null;
let pollInterval = null;

// DOM Elements
const dropZone = document.getElementById('drop-zone');
const videoInput = document.getElementById('video-input');
const pdfInput = document.getElementById('pdf-input');
const selectedFilesDiv = document.getElementById('selected-files');
const uploadBtn = document.getElementById('upload-btn');
const uploadSection = document.getElementById('upload-section');
const progressSection = document.getElementById('progress-section');
const lecturesSection = document.getElementById('lectures-section');
const detailSection = document.getElementById('detail-section');
const lecturesList = document.getElementById('lectures-list');
const backBtn = document.getElementById('back-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupDropZone();
    setupFileInputs();
    setupButtons();
    loadLectures();
});

// Drag and Drop
function setupDropZone() {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');

        const files = Array.from(e.dataTransfer.files);
        files.forEach(file => {
            if (isVideoFile(file)) {
                selectedVideo = file;
            } else if (isPdfFile(file)) {
                selectedPdf = file;
            }
        });

        updateSelectedFiles();
    });
}

// File Inputs
function setupFileInputs() {
    videoInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            selectedVideo = e.target.files[0];
            updateSelectedFiles();
        }
    });

    pdfInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            selectedPdf = e.target.files[0];
            updateSelectedFiles();
        }
    });
}

// Buttons
function setupButtons() {
    uploadBtn.addEventListener('click', uploadFiles);
    backBtn.addEventListener('click', showList);
}

// File Type Checks
function isVideoFile(file) {
    const videoTypes = ['video/mp4', 'video/x-matroska', 'video/avi', 'video/quicktime', 'video/webm',
        'audio/mp4', 'audio/x-m4a', 'audio/mpeg', 'audio/wav', 'audio/x-wav'];
    const videoExtensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.m4a', '.mp3', '.wav'];
    return videoTypes.includes(file.type) || videoExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
}

function isPdfFile(file) {
    return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
}

// Update Selected Files Display
function updateSelectedFiles() {
    selectedFilesDiv.innerHTML = '';

    if (selectedVideo) {
        selectedFilesDiv.appendChild(createFileElement(selectedVideo, 'video'));
    }

    if (selectedPdf) {
        selectedFilesDiv.appendChild(createFileElement(selectedPdf, 'pdf'));
    }

    uploadBtn.disabled = !selectedVideo;
}

function createFileElement(file, type) {
    const div = document.createElement('div');
    div.className = 'selected-file';
    div.innerHTML = `
        <span class="filename">${type === 'video' ? '🎥' : '📄'} ${file.name}</span>
        <button class="remove-btn" onclick="removeFile('${type}')">&times;</button>
    `;
    return div;
}

function removeFile(type) {
    if (type === 'video') {
        selectedVideo = null;
        videoInput.value = '';
    } else {
        selectedPdf = null;
        pdfInput.value = '';
    }
    updateSelectedFiles();
}

// Upload Files
async function uploadFiles() {
    if (!selectedVideo) return;

    const formData = new FormData();
    formData.append('video', selectedVideo);
    if (selectedPdf) {
        formData.append('pdf', selectedPdf);
    }

    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Uploading...';

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            currentLectureId = data.lecture_id;
            showProgress(selectedVideo.name);
            startPolling();

            // Reset file selection
            selectedVideo = null;
            selectedPdf = null;
            videoInput.value = '';
            pdfInput.value = '';
            updateSelectedFiles();
        } else {
            alert('Upload failed: ' + data.error);
        }
    } catch (error) {
        alert('Upload failed: ' + error.message);
    }

    uploadBtn.disabled = false;
    uploadBtn.textContent = 'Upload & Process';
}

// Progress Display
function showProgress(title) {
    progressSection.style.display = 'block';
    document.getElementById('progress-title').textContent = title;
    updateProgressStatus('pending', 0);
}

function hideProgress() {
    progressSection.style.display = 'none';
}

function updateProgressStatus(status, progress) {
    const statusEl = document.getElementById('progress-status');
    const fillEl = document.getElementById('progress-fill');

    let message = '';
    let width = '0%';

    if (status === 'pending') {
        message = 'Queued for processing...';
        width = '2%';
    } else if (status === 'transcribing') {
        message = `Transcribing video with Whisper... ${progress}%`;
        width = progress + '%';
    } else if (status === 'extracting') {
        message = 'Extracting content from slides...';
        width = '100%';
    } else if (status === 'summarizing') {
        message = `Generating summary with AI... ${progress}%`;
        width = progress + '%';
    } else if (status === 'complete') {
        message = 'Complete!';
        width = '100%';
    } else if (status === 'error') {
        message = 'An error occurred';
        width = '100%';
    }

    statusEl.textContent = message;
    fillEl.style.width = width;

    if (status === 'error') {
        fillEl.style.backgroundColor = '#e74c3c';
    } else if (status === 'complete') {
        fillEl.style.backgroundColor = '#2ecc71';
    } else {
        fillEl.style.backgroundColor = '#3498db';
    }
}

// Polling for Status
function startPolling() {
    pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${currentLectureId}`);
            const data = await response.json();

            updateProgressStatus(data.status, data.progress);

            if (data.status === 'complete' || data.status === 'error') {
                stopPolling();
                setTimeout(() => {
                    hideProgress();
                    loadLectures();
                    if (data.status === 'complete') {
                        showLecture(currentLectureId);
                    }
                }, 1000);
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 2000);
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

// Load Lectures List
async function loadLectures() {
    try {
        const response = await fetch('/lectures');
        const lectures = await response.json();

        if (lectures.length === 0) {
            lecturesList.innerHTML = '<p class="empty-state">No lectures yet. Upload a video to get started.</p>';
            return;
        }

        lecturesList.innerHTML = lectures.map(lecture => `
            <div class="lecture-item" onclick="showLecture(${lecture.id})">
                <div class="lecture-info">
                    <h3>${escapeHtml(lecture.title)}</h3>
                    <span class="date">${formatDate(lecture.created_at)}</span>
                </div>
                <div class="lecture-status">
                    <span class="status-badge status-${lecture.status}">${lecture.status}</span>
                    ${lecture.status === 'error' ? `<button class="btn btn-primary retry-btn" onclick="retryLecture(event, ${lecture.id})">Retry</button>` : ''}
                    <button class="btn btn-danger delete-btn" onclick="deleteLecture(event, ${lecture.id})">Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading lectures:', error);
    }
}

// Show Lecture Detail
async function showLecture(lectureId) {
    try {
        const response = await fetch(`/lecture/${lectureId}`);
        const lecture = await response.json();

        if (lecture.status !== 'complete') {
            alert('This lecture is still processing. Please wait.');
            return;
        }

        document.getElementById('detail-title').textContent = lecture.title;
        document.getElementById('detail-content').innerHTML = markdownToHtml(lecture.summary || 'No summary available.');

        // Display images
        const imagesDiv = document.getElementById('detail-images');
        if (lecture.images && lecture.images.length > 0) {
            imagesDiv.innerHTML = `
                <h3>Slide Images</h3>
                <div class="images-grid">
                    ${lecture.images.map(img => `
                        <div class="slide-image">
                            <img src="/static/${img.path}" alt="Slide ${img.page}" loading="lazy">
                            <div class="page-label">Page ${img.page}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            imagesDiv.innerHTML = '';
        }

        uploadSection.style.display = 'none';
        lecturesSection.style.display = 'none';
        detailSection.style.display = 'block';
    } catch (error) {
        console.error('Error loading lecture:', error);
    }
}

// Show List View
function showList() {
    detailSection.style.display = 'none';
    uploadSection.style.display = 'block';
    lecturesSection.style.display = 'block';
    loadLectures();
}

// Delete Lecture
async function deleteLecture(event, lectureId) {
    event.stopPropagation();

    if (!confirm('Are you sure you want to delete this lecture?')) {
        return;
    }

    try {
        await fetch(`/lecture/${lectureId}`, { method: 'DELETE' });
        loadLectures();
    } catch (error) {
        console.error('Error deleting lecture:', error);
    }
}

// Simple Markdown to HTML converter
function markdownToHtml(markdown) {
    if (!markdown) return '';

    let html = markdown
        // Escape HTML
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        // Headers
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Code
        .replace(/`(.+?)`/g, '<code>$1</code>')
        // Unordered lists
        .replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>')
        // Ordered lists
        .replace(/^\s*\d+\.\s+(.+)$/gm, '<li>$1</li>')
        // Blockquotes
        .replace(/^>\s+(.+)$/gm, '<blockquote>$1</blockquote>')
        // Line breaks
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');

    // Wrap list items
    html = html.replace(/(<li>.*<\/li>)+/g, '<ul>$&</ul>');

    // Wrap in paragraph
    html = '<p>' + html + '</p>';

    // Clean up empty paragraphs
    html = html.replace(/<p><\/p>/g, '');
    html = html.replace(/<p>(<h[123]>)/g, '$1');
    html = html.replace(/(<\/h[123]>)<\/p>/g, '$1');
    html = html.replace(/<p>(<ul>)/g, '$1');
    html = html.replace(/(<\/ul>)<\/p>/g, '$1');
    html = html.replace(/<p>(<blockquote>)/g, '$1');
    html = html.replace(/(<\/blockquote>)<\/p>/g, '$1');

    return html;
}

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Make functions globally available
// Retry Failed Lecture
async function retryLecture(event, lectureId) {
    event.stopPropagation();

    try {
        const response = await fetch(`/lecture/${lectureId}/retry`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            currentLectureId = data.lecture_id;
            showProgress('Retrying...');
            startPolling();
            loadLectures();
        } else {
            alert('Retry failed: ' + data.error);
        }
    } catch (error) {
        console.error('Error retrying lecture:', error);
    }
}

window.showLecture = showLecture;
window.deleteLecture = deleteLecture;
window.retryLecture = retryLecture;
window.removeFile = removeFile;
