import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

MODEL = "alibaba/qwen-image-3.0-pro"

if not ACCOUNT_ID:
    raise ValueError("CLOUDFLARE_ACCOUNT_ID is missing")

if not API_TOKEN:
    raise ValueError("CLOUDFLARE_API_TOKEN is missing")


# IMPORTANT:
# Model is NOT part of the URL.
url = (
    f"https://api.cloudflare.com/client/v4/"
    f"accounts/{ACCOUNT_ID}/ai/run"
)


prompt = """
Create a professional fintech marketing image for a banking
platform called Prism.

A premium modern banking environment with a glowing geometric
prism representing artificial intelligence and personalized
financial services. Blue, purple and cyan lighting, sophisticated
corporate fintech aesthetic, clean composition, premium banking
visual style, realistic 3D elements, high quality.

Do not include text, letters, logos or watermark.
"""


headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}


payload = {
    "model": MODEL,
    "input": {
        "prompt": prompt
    }
}


print("======================================")
print("PRISM IMAGE GENERATION TEST")
print("======================================")
print("Model:", MODEL)
print("Generating image...")
print()


try:

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=180
    )

    print("HTTP Status:", response.status_code)

    if response.status_code != 200:
        print("\nAPI ERROR:")
        print(response.text)
        raise SystemExit(1)

    data = response.json()

    print("\nAPI Response received.")

    if not data.get("success"):
        print("\nCloudflare returned an unsuccessful response:")
        print(data)
        raise SystemExit(1)

    result = data.get("result", {})

    print("\nResult keys:")
    print(result.keys())

    # Qwen image models may return image data in the result.
    image_base64 = result.get("image")

    if not image_base64:
        print("\nNo 'image' field found.")
        print("\nFull response:")
        print(data)
        raise SystemExit(1)

    image_data = base64.b64decode(image_base64)

    output_file = "prism_qwen_test.png"

    with open(output_file, "wb") as file:
        file.write(image_data)

    print()
    print("======================================")
    print("SUCCESS")
    print("======================================")
    print("Image saved as:", output_file)
    print(
        "Image size:",
        round(len(image_data) / 1024, 2),
        "KB"
    )


except requests.exceptions.Timeout:
    print("Request timed out.")

except requests.exceptions.RequestException as error:
    print("Request failed:")
    print(error)

except Exception as error:
    print("Unexpected error:")
    print(error)