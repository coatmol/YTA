import asyncio
import json
import edge_tts

AUDIO_OUTPUT = "output/voiceover.mp3"
JSON_OUTPUT = "output/word_timestamps.json"


async def generate_audio_and_timestamps(
    text: str, voice: str, audio_path: str, json_path: str
):
    """Streams edge-tts audio to MP3 and saves word-level timestamp offsets."""
    # Setting boundary="WordBoundary" emits word-level timing metadata
    communicate = edge_tts.Communicate(
        text, voice=voice, boundary="WordBoundary", rate="+8%", pitch="+0Hz"
    )

    word_events = []

    # Ensure output directories exist
    import os
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    if os.path.dirname(json_path):
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

    with open(audio_path, "wb") as f_audio:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                data = chunk.get("data")
                if data is not None:
                    f_audio.write(data)
            elif chunk["type"] == "WordBoundary":
                offset = chunk.get("offset")
                duration = chunk.get("duration")
                word_text = chunk.get("text")

                if (
                    offset is not None
                    and duration is not None
                    and word_text is not None
                ):
                    # Convert 100-nanosecond units (HNS) from Azure/Edge API into seconds
                    start_sec = offset / 10_000_000
                    duration_sec = duration / 10_000_000
                    end_sec = start_sec + duration_sec

                    word_events.append(
                        {
                            "word": word_text,
                            "start": round(start_sec, 3),
                            "end": round(end_sec, 3),
                            "duration": round(duration_sec, 3),
                        }
                    )

    # Save timestamps for video rendering
    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(word_events, f_json, indent=2, ensure_ascii=False)

    print(f"Successfully created {audio_path}")
    print(f"Saved {len(word_events)} word timestamps to {json_path}")


def create_tts(
    text: str,
    voice: str = "en-US-AndrewNeural",
    audio_path: str = AUDIO_OUTPUT,
    json_path: str = JSON_OUTPUT,
):
    """Synchronous wrapper to generate audio and timestamps."""
    asyncio.run(generate_audio_and_timestamps(text, voice, audio_path, json_path))
