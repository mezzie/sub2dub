import re
import sys

def clean_srt(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove HTML tags (e.g., <font ...>, </font>, <i>, <b>)
    cleaned_content = re.sub(r'<[^>]+>', '', content)

    # Optional: Remove ASS/SSA style override tags if present (e.g., {\an8})
    cleaned_content = re.sub(r'\{[^}]+\}', '', cleaned_content)

    # Remove \h (hard space) and replace with standard space
    cleaned_content = cleaned_content.replace(r'\h', ' ')
    
    # Collapse multiple spaces into one
    cleaned_content = re.sub(r' +', ' ', cleaned_content)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"Cleaned SRT saved to: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 clean_srt.py <input.srt> <output.srt>")
        sys.exit(1)
    
    clean_srt(sys.argv[1], sys.argv[2])
