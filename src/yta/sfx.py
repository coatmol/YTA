import re
import os
import json

def get_available_sfx(sfx_dir: str = "assets/sound") -> list[str]:
    """Returns a list of available sound effect names (without extensions) from the sfx directory."""
    if not os.path.exists(sfx_dir):
        return []
        
    sfx_names = []
    for filename in os.listdir(sfx_dir):
        if filename.endswith(".mp3") or filename.endswith(".wav"):
            name = os.path.splitext(filename)[0]
            sfx_names.append(name.lower())
    return sfx_names

def parse_script_for_sfx(script: str) -> tuple[str, list[dict]]:
    """
    Extracts [SFX:name] tags from the script.
    Returns the clean script and a list of {"name": name, "word_index": index}.
    """
    pattern = r'\[SFX:([a-zA-Z0-9_-]+)\]'
    
    # Add spaces around tags to isolate them as tokens
    spaced_script = re.sub(r'(\[SFX:[a-zA-Z0-9_-]+\])', r' \1 ', script)
    
    tokens = spaced_script.split()
    
    clean_words = []
    sfx_events = []
    
    for token in tokens:
        match = re.match(pattern, token, re.IGNORECASE)
        if match:
            sfx_name = match.group(1).lower()
            sfx_events.append({
                "name": sfx_name,
                "word_index": max(0, len(clean_words) - 1)
            })
        else:
            clean_words.append(token)
            
    clean_script = " ".join(clean_words)
    return clean_script, sfx_events

def resolve_sfx_timestamps(sfx_events: list[dict], word_timestamps_path: str, sfx_dir: str = "assets/sound") -> list[dict]:
    """
    Reads the word timestamps and maps word_index to exact time (seconds).
    Also filters out SFX that don't have a matching file in assets/sound.
    """
    if not sfx_events or not os.path.exists(word_timestamps_path):
        return []
        
    with open(word_timestamps_path, "r", encoding="utf-8") as f:
        word_timestamps = json.load(f)
        
    resolved_events = []
    for event in sfx_events:
        idx = event["word_index"]
        # If the tag is at the beginning, time is 0. Otherwise, use the end of the previous word.
        if idx < len(word_timestamps):
            time_sec = word_timestamps[idx]["end"]
        else:
            # Fallback if out of bounds
            time_sec = word_timestamps[-1]["end"] if word_timestamps else 0.0
            
        # Find file (support mp3 or wav)
        name = event["name"]
        mp3_path = os.path.join(sfx_dir, f"{name}.mp3")
        wav_path = os.path.join(sfx_dir, f"{name}.wav")
        
        file_path = None
        if os.path.exists(mp3_path):
            file_path = mp3_path
        elif os.path.exists(wav_path):
            file_path = wav_path
            
        if file_path:
            resolved_events.append({
                "name": name,
                "time": time_sec,
                "file_path": file_path
            })
            
    return resolved_events
