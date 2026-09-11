import os
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def format_script_for_shorts(title, body):
    """Pass Reddit text to Gemini to clean and reformat for TTS & YouTube Shorts."""
    prompt = f"""
    You are a viral YouTube Shorts scriptwriter. 
    Rewrite the following Reddit post into a high-retention 40-second script optimized for Text-to-Speech (TTS).

    STRICT RULES:
    1. Target length: around 200 words. Make it detailed, dramatic, and engaging.
    2. Expand all Reddit acronyms (e.g., AITA -> "Am I the asshole", 26M -> "26-year-old male").
    3. Strip all URLs, markdown formatting, "EDIT:" sections, and "TL;DR" tags.
    4. Censor explicit words to prevent YouTube monetization bans (e.g., replace heavy curses with mild alternatives).
    5. Hook (First 3 seconds): Start immediately with an urgent, dramatic statement or question. Never say "Reddit post" or "Today on AskReddit".
    6. Output ONLY the raw spoken script. Do NOT include scene notes, section labels like "[Hook:]", or brackets.

    REDDIT TITLE:
    {title}

    REDDIT POST BODY:
    {body}
    """

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        if not response or not response.text:
            raise Exception("Gemini API returned an empty response.")
    except Exception as e:
        raise Exception(f"Gemini API request failed: {e}")

    return response.text.strip()
