import os
import shutil
import time
from pathlib import Path

import yt_dlp

DOWNLOAD_DIR = "downloads"
TEMP_DIR = os.path.join(DOWNLOAD_DIR, "tmp")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


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
    ffprobe_exe = str(Path(_ffmpeg_path).with_name("ffprobe.exe"))
    if os.path.exists(ffprobe_exe):
        AudioSegment.ffprobe = ffprobe_exe


def _cleanup_partial_downloads() -> None:
    for part_file in Path(DOWNLOAD_DIR).glob("*.part"):
        try:
            part_file.unlink()
        except OSError:
            pass


def download_youtube_audio(url: str) -> str:
    _cleanup_partial_downloads()
    output_template = os.path.join(DOWNLOAD_DIR, "%(id)s_%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "paths": {"home": DOWNLOAD_DIR, "temp": TEMP_DIR},
        "noplaylist": True,
        "overwrites": True,
        "continuedl": False,
        "nopart": True,
        "restrictfilenames": True,
        "windowsfilenames": True,
        "concurrent_fragment_downloads": 1,
        "retries": 5,
        "fragment_retries": 5,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
    }
    node_path = shutil.which("node")
    if node_path:
        ydl_opts["js_runtimes"] = {"node": {"path": node_path}}

    last_error = None
    for _ in range(3):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # yt-dlp postprocessor converts to .wav — replace any extension safely
                wav_filename = str(Path(filename).with_suffix(".wav"))
            return wav_filename
        except Exception as exc:
            last_error = exc
            _cleanup_partial_downloads()
            time.sleep(1)
    raise last_error


def convert_to_wav(input_path: str) -> str:
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
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
