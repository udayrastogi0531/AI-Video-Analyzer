import os
from pathlib import Path
import shutil

import yt_dlp
# directory whre downloaded audio files will be stored
DOWNLOAD_DIR = 'downloades'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _find_ffmpeg_path() -> str | None:
    if shutil.which("ffmpeg"):
        return None

    local_appdata = os.getenv("LOCALAPPDATA", "")
    if not local_appdata:
        return None

    winget_root = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
    if not winget_root.exists():
        return None

    matches = list(winget_root.glob("Gyan.FFmpeg_*\\ffmpeg-*\\bin\\ffmpeg.exe"))
    if not matches:
        return None

    ffmpeg_path = matches[0]
    bin_dir = str(ffmpeg_path.parent)
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    return str(ffmpeg_path)


_ffmpeg_path = _find_ffmpeg_path()

from pydub import AudioSegment

if _ffmpeg_path:
    AudioSegment.converter = _ffmpeg_path
    ffprobe_path = str(Path(_ffmpeg_path).with_name("ffprobe.exe"))
    if os.path.exists(ffprobe_path):
        AudioSegment.ffprobe = ffprobe_path

def download_youtube_audio(url :str) ->str:
    node_path = shutil.which("node")
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        #  supressed download logs in the terminal
    }
    if node_path:
        ydl_opts["js_runtimes"] = {"node": {"path": node_path}}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).replace(".webm", ".wav").replace(".m4a", ".wav")
    return filename



def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    # automatically convert to mono and 16kHz for better compatibil ity with speech recognition models
    audio = AudioSegment.from_file(input_path)
    # automatically convert to mono and 16kHz for better compatibility with speech recognition models

    audio = audio.set_channels(1).set_frame_rate(16000) #16khz
    # monoaudio
    audio.export(output_path, format="wav")
    return output_path



def chunk_audio(wav_path : str , chunk_minutes : int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000 

    chunks = []

    for i, start in enumerate(range(0,len(audio),chunk_ms)):
        chunk = audio[start : start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path , format = "wav")

        chunks.append(chunk_path)
    
    return chunks

def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks


