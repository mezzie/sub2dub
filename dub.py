import argparse
import asyncio
import os
import shutil
import sys
import tempfile
import subprocess
import edge_tts
import pysrt
import numpy as np
import soundfile as sf

# Semaphores to prevent overwhelming the TTS service
CONCURRENCY_LIMIT = 5
SAMPLE_RATE = 44100

async def generate_clip(sem, text, output_file, voice, rate):
    async with sem:
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(output_file)
            return True
        except Exception as e:
            print(f"\nError generating '{text}': {e}")
            return False

async def generate_all_clips(subs, temp_dir, voice, rate):
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)
    tasks = []
    
    print(f"Generating audio for {len(subs)} subtitles...")
    
    for i, sub in enumerate(subs):
        text = sub.text.replace("\n", " ").strip()
        if not text:
            tasks.append(asyncio.sleep(0))
            continue
            
        safe_text = "".join(x for x in text[:15] if x.isalnum()) or "line"
        filename = os.path.join(temp_dir, f"{i:04d}_{safe_text}.mp3")
        sub.temp_audio_file = filename
        
        task = generate_clip(sem, text, filename, voice, rate)
        tasks.append(task)
    
    results = []
    total = len(tasks)
    for i, future in enumerate(asyncio.as_completed(tasks)):
        res = await future
        results.append(res)
        print(f"Progress: {len(results)}/{total}", end="\r")
    print("\nGeneration complete.")

def time_str_to_ms(t):
    return (t.hours * 3600 + t.minutes * 60 + t.seconds) * 1000 + t.milliseconds

def convert_mp3_to_wav_and_read(mp3_file, temp_dir):
    """
    Converts MP3 to WAV using ffmpeg and reads it into a numpy array.
    Returns: (data, samplerate)
    """
    wav_file = mp3_file.replace(".mp3", ".wav")
    try:
        # Convert to 44100Hz Mono WAV
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", 
            "-i", mp3_file, 
            "-ac", "1", 
            "-ar", str(SAMPLE_RATE), 
            wav_file
        ], check=True)
        
        data, samplerate = sf.read(wav_file)
        return data
    except Exception as e:
        print(f"Error processing {mp3_file}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="sub2dub: AI Voice Dubber using Edge-TTS")
    parser.add_argument("video_file", help="Input video file")
    parser.add_argument("srt_file", help="Input SRT subtitle file")
    parser.add_argument("--voice", default="en-US-ChristopherNeural", help="Edge-TTS voice")
    parser.add_argument("--output", "-o", default="dubbed_output.mkv", help="Output video file")
    parser.add_argument("--ducking", type=float, default=0.20, help="Volume of original audio (0.0 to 1.0)")
    parser.add_argument("--speed", default="+0%", help="Rate change (e.g. +10%%)")
    
    args = parser.parse_args()

    # Validations
    if not os.path.exists(args.video_file):
        print(f"Error: Video file {args.video_file} not found.")
        sys.exit(1)
    if not os.path.exists(args.srt_file):
        print(f"Error: SRT file {args.srt_file} not found.")
        sys.exit(1)
    if shutil.which("ffmpeg") is None:
        print("Error: ffmpeg is not installed.")
        sys.exit(1)

    subs = pysrt.open(args.srt_file)
    if not subs:
        print("No subtitles found.")
        sys.exit(1)

    temp_dir = tempfile.mkdtemp()
    try:
        # 1. Generate TTS
        asyncio.run(generate_all_clips(subs, temp_dir, args.voice, args.speed))

        # 2. Get Video Duration for Canvas
        print("Getting video duration...")
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", args.video_file]
            duration_sec = float(subprocess.check_output(cmd).decode().strip())
        except:
            duration_sec = (time_str_to_ms(subs[-1].end) + 10000) / 1000.0

        total_samples = int(duration_sec * SAMPLE_RATE)
        print(f"Total duration: {duration_sec:.2f}s ({total_samples} samples)")

        # 3. Assemble Audio (Numpy)
        master_track = np.zeros(total_samples, dtype=np.float32)
        
        print("Mixing audio...")
        for sub in subs:
            if hasattr(sub, 'temp_audio_file') and os.path.exists(sub.temp_audio_file):
                data = convert_mp3_to_wav_and_read(sub.temp_audio_file, temp_dir)
                if data is None:
                    continue
                
                start_ms = time_str_to_ms(sub.start)
                start_sample = int(start_ms * SAMPLE_RATE / 1000)
                end_sample = start_sample + len(data)

                # Handle bounds
                if end_sample > total_samples:
                    # Resize master track if needed (dynamic growth) or trim
                    # Let's grow it to be safe
                    pad_width = end_sample - total_samples
                    master_track = np.pad(master_track, (0, pad_width))
                    total_samples = len(master_track)
                
                # Mixing (Add)
                master_track[start_sample:end_sample] += data

        # Normalize if clipping occurs (simple limiter)
        max_val = np.max(np.abs(master_track))
        if max_val > 1.0:
            print("Clipping detected, normalizing...")
            master_track /= max_val

        mixed_audio_path = os.path.join(temp_dir, "full_dub.wav")
        print(f"Exporting to {mixed_audio_path}...")
        sf.write(mixed_audio_path, master_track, SAMPLE_RATE)

        # 4. Merge
        print("Merging...")
        cmd = [
            "ffmpeg", "-y",
            "-i", args.video_file,
            "-i", mixed_audio_path,
            "-filter_complex", (
                f"[0:a:0]aresample=async=1,volume={args.ducking}[bg];"
                f"[1:a:0]pan=stereo|c0=c0|c1=c0,volume=1.0[fg];"
                f"[bg][fg]amix=inputs=2:duration=first[aout]"
            ),
            "-map", "0:v:0",
            "-map", "[aout]",
            "-map", "0:s?", 
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-c:s", "copy",
            "-disposition:a:0", "default",
            "-metadata:s:a:0", "language=eng",
            "-metadata:s:a:0", "title=AI English Dub",
            "-shortest",
            args.output
        ]
        subprocess.run(cmd, check=True)
        print(f"\nDone! Output: {os.path.abspath(args.output)}")

    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()