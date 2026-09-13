import os
import json
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)
model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def format_script_for_shorts(title, body, target_words=200, use_sfx=False, available_sfx=None) -> tuple[str, str, str]:
    """Pass text to Gemini to clean and reformat for TTS & YouTube Shorts, generating title and description."""
    
    prompt = f"""
    You are a viral YouTube Shorts scriptwriter. 
    Write a hilarious, fast-paced dialogue where Stewie Griffin explains the following concept/story to Peter Griffin.

    STRICT RULES:
    1. Stewie should be intelligent, condescending, British-sounding, and exasperated with Peter.
    2. Peter should be somewhat clueless and naive, but not overwhelmingly stupid. He should ask genuine (if slightly misguided or goofy) questions to help Stewie explain the concept.
    3. They should talk exactly like they do in the TV show Family Guy and be very funny.
    4. Target length: EXACTLY {target_words} words (approx {target_words // 15} sentences combined). You MUST expand or summarize to hit this exact length.
    5. Censor explicit words to prevent YouTube monetization bans.
    6. Hook (First 3 seconds): Start immediately with Stewie trying to explain something urgently to Peter.
    7. NO scene notes, NO descriptions, NO sfx tags. ONLY spoken dialogue.
    8. Format the script EXACTLY as:
    Stewie: <text>
    Peter: <text>
    (Ensure alternating or appropriate dialogue flow)
    9. The very last line of the script MUST be Stewie saying "Like and subscribe for more videos like these!"

    CONCEPT/STORY TITLE:
    {title}

    CONCEPT/STORY BODY:
    {body}
    """

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "script": {"type": "STRING"},
                        "youtube_title": {"type": "STRING"},
                        "youtube_description": {"type": "STRING"},
                    },
                    "required": ["script", "youtube_title", "youtube_description"],
                },
            ),
        )

        if not response or not response.text:
            raise Exception("Gemini API returned an empty response.")

        data = json.loads(response.text)
        return data["script"].strip(), data["youtube_title"], data["youtube_description"]
    except Exception as e:
        raise Exception(f"Gemini API request failed: {e}")
