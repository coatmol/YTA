import os
import json
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
client = genai.Client(api_key=GEMINI_API_KEY)
model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def format_script_for_shorts(title, body, target_words=200, use_sfx=False, available_sfx=None) -> tuple[str, str, str, str]:
    """Pass Reddit text to Gemini to clean and reformat for TTS & YouTube Shorts, generating title and description."""
    
    sfx_rule = ""
    if use_sfx:
        sfx_rule = "9. Add sound effect tags like [SFX:knock] within the script at appropriate moments to enhance the atmosphere."
        if available_sfx:
            sfx_rule += f" You MUST ONLY use the following available sound effects: {', '.join(available_sfx)}."
        else:
            sfx_rule += " (No specific sound effects provided, use generic names)."

    prompt = f"""
    You are a viral YouTube Shorts scriptwriter. 
    Rewrite the following Reddit post into a high-retention script optimized for Text-to-Speech (TTS).
    Also generate a catchy YouTube Shorts video title and a description with relevant hashtags.

    STRICT RULES:
    1. Target length: around {target_words} words. Make it detailed, dramatic, and engaging.
    2. Expand all Reddit acronyms (e.g., AITA -> "Am I the asshole", 26M -> "26-year-old male").
    3. Strip all URLs, markdown formatting, "EDIT:" sections, and "TL;DR" tags.
    4. Censor explicit words to prevent YouTube monetization bans (e.g., replace heavy curses with mild alternatives).
    5. Hook (First 3 seconds): Start immediately with an urgent, dramatic statement or question. Never say "Reddit post" or "Today on AskReddit".
    6. Do not include scene notes or section labels like "[Hook:]" in the script.
    7. End with a cliffhanger or a question to encourage viewers to comment.
    8. Say "Like and Subscribe for more stories!" at the end of the script.
    {sfx_rule}

    REDDIT TITLE:
    {title}

    REDDIT POST BODY:
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
                        "gender": {
                            "type": "STRING",
                            "enum": ["male", "female", "unknown"],
                        },
                        "youtube_title": {"type": "STRING"},
                        "youtube_description": {"type": "STRING"},
                    },
                    "required": ["script", "gender", "youtube_title", "youtube_description"],
                },
            ),
        )

        if not response or not response.text:
            raise Exception("Gemini API returned an empty response.")

        data = json.loads(response.text)
        return data["script"].strip(), data["gender"], data["youtube_title"], data["youtube_description"]
    except Exception as e:
        raise Exception(f"Gemini API request failed: {e}")
