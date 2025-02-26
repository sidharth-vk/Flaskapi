from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import re

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads/"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

def sanitize_filename(filename):
    """
    Sanitizes filenames to ensure compatibility with Windows OS
    by removing or replacing characters that are not allowed in filenames.
    """
    # Replace invalid characters on Windows like ':', '?', etc.
    filename = re.sub(r'[\/:*?"<>|]', "_", filename)  # Replaces invalid characters with '_'

    # Additionally, trim the filename to avoid excessively long paths
    max_length = 255  # Standard max length for filenames on Windows
    if len(filename) > max_length:
        filename = filename[:max_length]

    return filename

def download_youtube_audio(video_id):
    """
    Downloads the audio from a YouTube video using yt-dlp.

    Args:
        video_id (str): The YouTube video ID.

    Returns:
        str: Path of the downloaded audio file or None if failed.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'extract_audio': True,
        'audio_format': 'mp3',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)


            sanitized_path = sanitize_filename(file_path)

            return sanitized_path
    except Exception as e:
        print(f"Error downloading: {e}")
        return None

@app.route('/download_audio', methods=['GET'])
def download_audio():
    video_id = request.args.get('video_id')

    if not video_id:
        return jsonify({"error": "Missing video_id parameter"}), 400

    file_path = download_youtube_audio(video_id)

    if file_path:
        try:

            actualpath = os.path.abspath(file_path)
            actualpath = actualpath.replace("//", "\\")

            print(actualpath)
            if actualpath:
                return actualpath
            else:
                return jsonify({"error": "File not found at the given path"}), 500
        except Exception as e:
            print(f"Error during file sending: {e}")
            return jsonify({"error": "Internal server error"}), 500
    else:
        return jsonify({"error": "Failed to download audio"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT',5000))
    host = '0.0.0.0'
    
    app.run(host=host, port=port, debug=False)
