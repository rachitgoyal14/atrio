import os
import base64
import cv2
from dotenv import load_dotenv

# ✅ LOAD .env VARIABLES
load_dotenv()

_client = None
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")


def _get_client():
    """Lazy-load Azure client so missing env vars don't crash app import."""
    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    if not api_key or not endpoint or not api_version or not DEPLOYMENT:
        return None
    from openai import AzureOpenAI
    _client = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version,
    )
    return _client

def encode_image(img):
    _, buffer = cv2.imencode(".png", img)
    return base64.b64encode(buffer).decode("utf-8")

def detect_artery_name(roi_with_box):
    """Return artery name, or 'Unknown' when Azure Vision is unconfigured/failing."""
    client = _get_client()
    if client is None:
        return "Unknown"
    try:
        image_b64 = encode_image(roi_with_box)

        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "This is a coronary angiography image. "
                                "Identify the coronary artery shown "
                                "(LAD, RCA, LCX, Left Main, or Other). "
                                "Reply with only the artery name."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=100
        )

        return (response.choices[0].message.content or "Unknown").strip()
    except Exception:
        return "Unknown"
