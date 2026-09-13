import json
from datetime import datetime
from pathlib import Path
import re
import argparse
import logging
import warnings
import dotenv

warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.ERROR)

dotenv.load_dotenv()
from yta import *


def parse_script_into_lines(script: str) -> list[tuple[str, str]]:
    # Split by Stewie: or Peter: anywhere in the text
    pattern = r'(?i)\b(Stewie|Peter):'
    parts = re.split(pattern, script)
    
    dialogue = []
    current_char = "Stewie"  # Default in case it doesn't start with a name
    
    if parts and not re.match(r'(?i)^(Stewie|Peter)$', parts[0].strip()):
        text = parts.pop(0).strip()
        if text:
            dialogue.append((current_char, text))
            
    for i in range(0, len(parts), 2):
        char_name = parts[i].capitalize()
        text = parts[i+1].strip() if i+1 < len(parts) else ""
        if text:
            dialogue.append((char_name, text))
            
    return dialogue


def main():
    parser = argparse.ArgumentParser(
        description="YTA - Youtube Shorts Text-to-Video Automation (Family Guy Edition)"
    )
    parser.add_argument(
        "--video", "-v", type=str, help="Path to input background video (MP4)"
    )
    parser.add_argument(
        "--bgm", "-b", type=str, help="Path to background music audio (MP3/WAV)"
    )
    parser.add_argument(
        "--post",
        "-p",
        type=str,
        help="Specific Reddit post ID to fetch",
    )
    parser.add_argument(
        "--subreddit",
        "-r",
        type=str,
        help="Specific Reddit subreddit to fetch posts from",
    )
    parser.add_argument(
        "--text",
        "-t",
        type=str,
        help="Specific text file to use for the video instead of fetching from Reddit (First line is title, rest is body)",
    )
    parser.add_argument(
        "--topic",
        type=str,
        help="Provide a topic directly for the AI to explain (e.g., 'Hashmaps in programming')",
    )
    parser.add_argument(
        "--words",
        "-w",
        type=int,
        default=200,
        help="Target word count for the video script (default: 200)",
    )
    args = parser.parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not args.video:
        parser.print_help()
        return

    if args.topic:
        title = f"Explaining {args.topic}"
        body = f"Explain the concept of '{args.topic}' in detail."
    elif args.text:
        with open(args.text, "r", encoding="utf-8") as f:
            title = f.readline().strip()
            body = f.read().strip()
    else:
        story = reddit.get_story(post_id=args.post, subreddit_name=args.subreddit)
        if story is None:
            print("No story found.")
            return

        title, body = story

    output_dir = Path(f"output/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating Script via Gemini...")
    clean_script, yt_title, yt_desc = inference.format_script_for_shorts(
        title,
        body,
        target_words=args.words,
        use_sfx=False,
    )

    print(f"\n[Generated Script]:\n{clean_script}\n")

    with open(output_dir / "metadata.txt", "w", encoding="utf-8") as f:
        f.write(f"Title: {yt_title}\n\nDescription:\n{yt_desc}\n")

    print("Generating Voiceover...")

    dialogue_lines = parse_script_into_lines(clean_script)
    
    from pydub import AudioSegment
    combined_audio = AudioSegment.empty()
    combined_events = []
    character_events = []
    
    current_time_offset = 0.0
    
    char_voices = {
        "Stewie": "en-GB-RyanNeural", 
        "Peter": "en-US-GuyNeural"
    }
    
    char_rvc_models = {
        "Stewie": "assets/voice/stewiev4.0.pth",
        "Peter": "assets/voice/peter_griffin_rvcv2_fittest.pth"
    }

    for i, (char_name, text) in enumerate(dialogue_lines):
        print(f"Generating TTS for {char_name}: {text[:30]}...")
        line_audio = str(output_dir / f"line_{i}.mp3")
        line_json = str(output_dir / f"line_{i}.json")
        line_rvc = str(output_dir / f"line_{i}_rvc.wav")
        
        tts.create_tts(
            text,
            audio_path=line_audio,
            json_path=line_json,
            voice=char_voices.get(char_name, "en-US-AndrewNeural"),
        )
        
        # Apply RVC
        tts.apply_rvc(
            input_audio=line_audio,
            output_audio=line_rvc,
            model_path=char_rvc_models.get(char_name, ""),
            device="cuda:0"
        )
        
        # Load audio and JSON
        seg = AudioSegment.from_file(line_rvc)
        duration_sec = len(seg) / 1000.0
        
        with open(line_json, "r", encoding="utf-8") as f:
            events = json.load(f)
            
        for event in events:
            event["start"] = round(event["start"] + current_time_offset, 3)
            event["end"] = round(event["end"] + current_time_offset, 3)
            combined_events.append(event)
            
        character_events.append({
            "character": char_name,
            "start": current_time_offset,
            "end": current_time_offset + duration_sec
        })
            
        combined_audio += seg
        current_time_offset += duration_sec

    final_audio_path = str(output_dir / "voiceover.wav")
    final_json_path = str(output_dir / "word_timestamps.json")
    
    combined_audio.export(final_audio_path, format="wav")
    with open(final_json_path, "w", encoding="utf-8") as f:
        json.dump(combined_events, f, indent=2, ensure_ascii=False)

    print("\nGenerating Subtitles...")
    sub_path = str(output_dir / "subtitles.ass")
    subtitles.generate_ass(final_json_path, sub_path)

    if args.video:
        print("\nProcessing Video...")
        video.create_short_video(
            input_video_path=args.video,
            audio_path=final_audio_path,
            bgm_path=args.bgm,
            subtitles_path=sub_path,
            character_events=character_events,
            output_path=str(output_dir / "final_short.mp4"),
        )


if __name__ == "__main__":
    main()
