import asyncio
import json
import edge_tts
import torch

_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _original_load(*args, **kwargs)
torch.load = _patched_load



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

    # Restore punctuation by aligning with the original text
    original_tokens = text.split()
    token_idx = 0
    for event in word_events:
        event_clean = "".join(c for c in event["word"].lower() if c.isalnum())
        if not event_clean:
            continue

        # Search ahead up to 5 tokens to find a match
        for offset in range(5):
            check_idx = token_idx + offset
            if check_idx >= len(original_tokens):
                break

            token = original_tokens[check_idx]
            token_clean = "".join(c for c in token.lower() if c.isalnum())

            if (
                event_clean == token_clean
                or event_clean in token_clean
                or token_clean in event_clean
            ):
                event["word"] = token
                token_idx = check_idx + 1
                break

    # Save timestamps for video rendering
    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(word_events, f_json, indent=2, ensure_ascii=False)

    print(f"Successfully created {audio_path}")
    print(f"Saved {len(word_events)} word timestamps to {json_path}")

def apply_rvc(
    input_audio: str,
    output_audio: str,
    model_path: str,
    device: str = "cuda:0"
):
    from rvc_python.infer import RVCInference
    print(f"Applying RVC with model {model_path} on {input_audio}...")
    rvc = RVCInference(
        device=device,
        model_path=model_path,
        version="v2"
    )
    rvc.set_params(
        f0method="rmvpe",
        f0up_key=0,
        index_rate=0.66,
        filter_radius=3,
        resample_sr=0,
        rms_mix_rate=1,
        protect=0.33
    )
    rvc.infer_file(input_audio, output_audio)
    print(f"RVC output saved to {output_audio}")


def create_tts(
    text: str,
    audio_path: str,
    json_path: str,
    voice: str = "en-US-AndrewNeural",
):
    """Synchronous wrapper to generate audio and timestamps."""
    asyncio.run(generate_audio_and_timestamps(text, voice, audio_path, json_path))
