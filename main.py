from flask import Flask, request, Response, jsonify
import yt_dlp
import os
import subprocess

app = Flask(__name__)

def stream_youtube_audio(video_id):
    """
    Streams audio from a YouTube video using yt-dlp.

    Args:
        video_id (str): The YouTube video ID.

    Yields:
        bytes: Audio data chunks for streaming.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': 'bestaudio/best',  # Get the best audio quality
        'quiet': True,               # Suppress yt-dlp output
    }

    try:
        # Use yt-dlp to get the direct audio URL (no download)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)  # Don't download, just get info
            audio_url = info['url']  # Direct URL to the audio stream

        # Use subprocess to stream the audio data (like piping to VLC)
        # ffmpeg is used here to convert the stream to MP3 on-the-fly
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', audio_url,          # Input is the YouTube audio URL
            '-f', 'mp3',              # Output format is MP3
            '-acodec', 'mp3',         # Audio codec
            '-ab', '192k',            # Bitrate (adjustable)
            '-',                      # Output to stdout (pipe)
        ]

        # Start the subprocess and stream the output
        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Yield audio chunks as they come
        while True:
            chunk = process.stdout.read(1024)  # Read in 1KB chunks
            if not chunk:
                break
            yield chunk

        process.wait()  # Ensure the process completes
        if process.returncode != 0:
            raise Exception("FFmpeg streaming failed")

    except Exception as e:
        print(f"Error streaming: {e}")
        yield b"Error: Could not stream audio"  # Yield an error message for the client

@app.route('/stream_audio', methods=['GET'])
def stream_audio():
    video_id = request.args.get('video_id')

    if not video_id:
        return jsonify({"error": "Missing video_id parameter"}), 400

    # Return a streaming response
    return Response(
        stream_youtube_audio(video_id),
        mimetype='audio/mpeg',  # MP3 MIME type
        headers={
            'Content-Disposition': 'inline',  # Stream inline, not as a download
            'Cache-Control': 'no-cache',      # Prevent caching
        }
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'  # Bind to all interfaces for Render
    print(f"Starting Flask app on {host}:{port}")
    app.run(host=host, port=port, debug=False)
