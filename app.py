from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import json
import time

app = Flask(__name__)

# Global variable to store download progress data
download_progress = {}

# Progress hook function to track the progress of downloading
def progress_hook(d):
    if d['status'] == 'downloading':
        download_info = {
            'status': 'downloading',
            'filename': d.get('filename', 'Unknown'),
            'progress': d.get('downloaded_bytes', 0),
            'total_bytes': d.get('total_bytes', 1),  # Avoid division by zero
            'percent': d.get('percent', 0),
        }
        # Update global variable for progress
        download_progress['filename'] = download_info['filename']
        download_progress['percent'] = download_info['percent']
        download_progress['progress'] = download_info['progress']
        download_progress['total_bytes'] = download_info['total_bytes']

# Function to download the video with the best possible quality
def download_video(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Ensure we get both the best video and audio quality
        'outtmpl': 'downloads/%(title)s.%(ext)s',  # Save the video with its title
        'merge_output_format': 'mp4',  # Merge video and audio into mp4 format
        'quiet': False,  # Suppresses unnecessary output
        'progress_hooks': [progress_hook],  # Hook to track progress
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=True)
            return info_dict['title'], 'downloads/' + info_dict['title'] + '.' + info_dict['ext']
        except Exception as e:
            raise Exception(f"Error downloading the video: {str(e)}")

# SSE endpoint for sending download progress to client
@app.route('/progress')
def progress():
    def generate():
        while True:
            if 'percent' in download_progress:
                yield f"data: {json.dumps(download_progress)}\n\n"
            time.sleep(1)  # Sends progress every second

    return Response(generate(), content_type='text/event-stream')

@app.route('/')
def index():
    return render_template('.\templates\index.html')

@app.route('/download', methods=['POST'])
def download():
    video_url = request.form['url']
    try:
        title, file_path = download_video(video_url)
        return jsonify({'status': 'success', 'message': f'Video "{title}" downloaded successfully!', 'file_path': file_path})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
