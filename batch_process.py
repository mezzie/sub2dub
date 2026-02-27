import os
import subprocess
import sys
import argparse

# Script names (expected to be in the same directory)
CLEAN_SCRIPT = "clean_srt.py"
DUB_SCRIPT = "dub.py"

def main():
    parser = argparse.ArgumentParser(description="sub2dub: Batch process video files for AI dubbing.")
    parser.add_argument("input_dir", help="Directory containing video files to process.")
    parser.add_argument("output_dir", help="Directory to save the dubbed output files.")
    
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get all video files recursively
    video_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.mkv', '.mp4')):
                video_files.append(os.path.join(root, file))
    video_files.sort()
    
    if not video_files:
        print("No MKV or MP4 files found in '{}'".format(input_dir))
        sys.exit(1)

    print("Found {} episodes to process.".format(len(video_files)))

    for video_path in video_files:
        filename = os.path.basename(video_path)
        base_name = os.path.splitext(filename)[0]
        
        raw_srt = os.path.join(output_dir, "{}_raw.srt".format(base_name))
        clean_srt = os.path.join(output_dir, "{}.srt".format(base_name))
        final_video = os.path.join(output_dir, "{}_dubbed.mkv".format(base_name))
        
        if os.path.exists(final_video):
            print("\n--- Skipping: {} (already dubbed) ---".format(filename))
            continue
            
        print("\n--- Processing: {} ---".format(filename))
        
        # 1. Extract Subtitles
        print("Extracting subtitles to {}...".format(raw_srt))
        try:
            subprocess.run([
                "ffmpeg", "-y", "-v", "error", 
                "-i", video_path, 
                "-map", "0:s:0", 
                raw_srt
            ], check=True)
        except subprocess.CalledProcessError as e:
            print("Error: Failed to extract subtitles from {}: {}. Skipping.".format(filename, e))
            continue

        # 2. Clean Subtitles
        print("Cleaning subtitles...")
        try:
            subprocess.run([
                sys.executable, CLEAN_SCRIPT, 
                raw_srt, 
                clean_srt
            ], check=True)
        except subprocess.CalledProcessError as e:
            print("Error: Failed to clean subtitles for {}: {}. Skipping.".format(filename, e))
            continue

        # 3. Dub Video
        print("Dubbing video (this will take a while)...")
        try:
            cmd = [
                sys.executable, DUB_SCRIPT, 
                video_path, 
                clean_srt, 
                "-o", final_video
            ]
            subprocess.run(cmd, check=True)
            print("Success! Output saved to: {}".format(final_video))
            
            if os.path.exists(raw_srt): os.remove(raw_srt)
            
        except subprocess.CalledProcessError as e:
            print("Error: Failed to dub {}: {}.".format(filename, e))
            continue

    print("\nBatch processing complete!")

if __name__ == "__main__":
    main()
