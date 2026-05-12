# AI Video Analyzer

AI Video Analyzer is a Streamlit app and CLI pipeline that turns YouTube videos or local media files into meeting intelligence. It downloads or converts audio, transcribes with Whisper or Sarvam, summarizes with Mistral, extracts action items/decisions/questions, and lets you chat with the transcript via a local RAG index (Chroma + HuggingFace embeddings).

## Features
- YouTube or local file input
- Audio chunking and preprocessing
- Transcription: local Whisper (English) or Sarvam (Hinglish -> English)
- Title and summary generation (Mistral)
- Action items, key decisions, open questions extraction
- RAG chat over the meeting transcript
- Streamlit UI and CLI pipeline

## Tech Stack
- Streamlit for UI
- yt-dlp + ffmpeg + pydub for audio
- Whisper (local) and Sarvam for transcription
- LangChain + Mistral for LLM tasks
- Chroma + sentence-transformers for RAG

## Project Structure
- app.py - Streamlit UI
- main.py - CLI pipeline and RAG chat
- core/ - Summarizer, extractor, RAG, vector store
- utils/ - Audio processing utilities

## Requirements
- Python 3.10+ (recommended)
- ffmpeg installed and on PATH

Install dependencies:

```bash
pip install -r Requirements.txt
```

## Environment Variables
Create a `.env` file (do not commit it):

```bash
MISTRAL_API_KEY=your_mistral_api_key
SARVAM_API_KEY=your_sarvam_api_key
WHISPER_MODEL=base
SARVAM_STT_MODEL=saaras:v2.5
```

Notes:
- `MISTRAL_API_KEY` is required for summarization, extraction, and RAG answers.
- `SARVAM_API_KEY` is required only for Hinglish mode.
- `WHISPER_MODEL` defaults to `base` on CPU and `small` on GPU.

## Run the App (Streamlit)

```bash
streamlit run app.py
```

Open the browser UI, paste a YouTube URL or a local file path, choose language, and click Analyze.

## Run the CLI

```bash
python main.py
```

The CLI prompts for a source and language, prints the title/summary/action items, and starts a chat loop.

## RAG Storage
The vector index is persisted in `vector_db/`. You can delete this folder to rebuild the index.

## Troubleshooting
- If transcription fails, ensure ffmpeg is installed and visible in PATH.
- If Mistral calls fail, verify `MISTRAL_API_KEY` in `.env`.
- Large uploads or slow YouTube links may take time to process.

## License
Add a license if you plan to publish this project.
