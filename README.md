# sub2dub 📺🗣️

**sub2dub** is a lightweight, automated Python/FFmpeg pipeline designed to generate English AI dubs for foreign-language video content. It leverages Microsoft Edge's high-quality Neural TTS to transform subtitles into natural-sounding speech, mixed seamlessly with the original background audio.

Perfect for converting subbed content into an accessible "dubbed" experience when you'd rather listen than read.

## ✨ Key Features

- **Neural AI Voices**: Uses `edge-tts` for state-of-the-art, human-like narration.
- **Intelligent Audio Mixing**: Automatically ducks original audio to 20% volume during speech to preserve music and SFX.
- **Robust Syncing**: Employs `aresample=async=1` to handle Opus/AV1 synchronization and negative start times.
- **Recursive Batch Processing**: Process entire series at once with a single command.
- **Subtitle Pre-processing**: Automatically strips HTML, ASS override tags, and special characters (`\h`) to ensure clean TTS reading.
- **High-Quality Output**: Maps mono TTS to stereo (`pan=stereo|c0=c0|c1=c0`) and preserves all original subtitle tracks in the final MKV.

## 🛠️ Prerequisites

1. **Python 3.10+** (Optimized for 3.14+)
2. **FFmpeg** (Must be installed and in your system PATH)
   - **Mac**: `brew install ffmpeg`
   - **Windows**: `winget install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mezzie/sub2dub.git
   cd sub2dub
   ```

2. **Set up a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

### 📂 Batch Processing (Recommended)
Automatically extract subtitles, clean them, and generate dubbed videos for every file in a directory:
```bash
python3 batch_process.py <input_dir> <output_dir>
```
*Note: This script is recursive and will skip files already present in the output directory.*

### 🎬 Single File Dubbing
```bash
python3 dub.py <video_file> <srt_file> --output "dubbed_video.mkv"
```

### 🧹 Subtitle Cleaning Only
```bash
python3 clean_srt.py <input_raw.srt> <output_cleaned.srt>
```

## ⚙️ Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--voice` | Edge-TTS voice model (e.g., `en-US-ChristopherNeural`) | `en-US-ChristopherNeural` |
| `--ducking`| Background audio volume multiplier (0.0 - 1.0) | `0.20` |
| `--speed`  | TTS rate adjustment (e.g., `+10%%`, `-5%%`) | `+0%%` |

## 🗣️ Recommended Voices
Check all available voices using: `edge-tts --list-voices`.
- **Male**: `en-US-ChristopherNeural`, `en-US-GuyNeural`, `en-AU-WilliamNeural`
- **Female**: `en-US-AriaNeural`, `en-US-EmmaNeural`, `en-GB-SoniaNeural`

## 🛡️ License
MIT License. Feel free to use and improve!
