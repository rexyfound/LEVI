import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def analyze_image(path, prompt):

    with open(path, "rb") as f:
        image = f.read()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(
                data=image,
                mime_type="image/png"
            ),
            prompt
        ]
    )

    return response.text