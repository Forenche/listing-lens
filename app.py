"""
Listing Lens: turn product photos into a ready-to-paste marketplace listing.
Runs an open-weight Gemma model locally through Ollama. Photos never leave your machine.
"""
import base64
import io
import json
import os
import urllib.error
import urllib.request

import gradio as gr

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("MODEL", "gemma4:e4b")

PROMPT = """You write product listings for small online sellers.
Look at the product photo(s). Marketplace: {platform}. Tone: {tone}.
Seller's notes (trust these over what you see): {notes}

Rules:
- Only describe what is visible or stated in the notes. Never invent brand names,
  materials, measurements, certifications or condition details you cannot see.
- If something a buyer would need is unknown (size, material, condition), list it
  under "missing_info" so the seller can fill it in.
- Write in plain, honest language. No fake urgency, no ALL CAPS.

Respond ONLY with JSON:
{{"title": "listing title, max 80 characters",
  "description": "2-3 short paragraphs",
  "bullets": ["key feature", "..."],
  "tags": ["search keyword", "..."],
  "missing_info": ["thing the seller should add", "..."]}}"""


def to_b64(path: str) -> str:
    from PIL import Image
    img = Image.open(path).convert("RGB")
    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def call_ollama(prompt: str, images: list[str]) -> dict:
    payload = {
        "model": MODEL,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.4},
        "messages": [{"role": "user", "content": prompt, "images": images}],
    }
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = json.load(resp)
    return json.loads(body["message"]["content"])


def as_list(x) -> list[str]:
    if isinstance(x, list):
        return [str(i).strip() for i in x if str(i).strip()]
    return [s.strip() for s in str(x or "").split(",") if s.strip()]


def write_listing(files, platform: str, tone: str, notes: str):
    if not files:
        return "Add at least one product photo.", ""
    paths = [f if isinstance(f, str) else f.name for f in files][:4]
    try:
        r = call_ollama(
            PROMPT.format(platform=platform, tone=tone, notes=notes.strip() or "none"),
            [to_b64(p) for p in paths],
        )
    except urllib.error.URLError:
        return f"Can't reach Ollama at {OLLAMA_URL}. Run `ollama serve` and `ollama pull {MODEL}`.", ""
    except (json.JSONDecodeError, KeyError, OSError):
        return "The model returned something unreadable. Press Write listing again.", ""

    title = str(r.get("title", "")).strip()[:80]
    bullets = as_list(r.get("bullets"))
    tags = as_list(r.get("tags"))
    missing = as_list(r.get("missing_info"))

    listing = f"{title}\n\n{str(r.get('description', '')).strip()}"
    if bullets:
        listing += "\n\n" + "\n".join(f"• {b}" for b in bullets)
    if tags:
        listing += "\n\nTags: " + ", ".join(tags)

    check = "**Fill these in before posting:**\n" + "\n".join(f"- {m}" for m in missing) if missing \
        else "**Nothing obviously missing.** Still double-check size and condition."
    check += f"\n\n<sub>Written offline by {MODEL}. Check every detail before you publish.</sub>"
    return check, listing


with gr.Blocks(title="Listing Lens") as demo:
    gr.Markdown("# Listing Lens\nDrop in product photos, get a listing you can paste into your shop. Runs on your own machine.")
    with gr.Row():
        with gr.Column():
            photos = gr.File(label="Product photos (up to 4)", file_count="multiple", file_types=["image"])
            platform = gr.Dropdown(["Etsy", "eBay", "Instagram shop", "Meesho", "Generic"], value="Etsy", label="Marketplace")
            tone = gr.Radio(["Friendly", "Professional", "Minimal"], value="Friendly", label="Tone")
            notes = gr.Textbox(label="Your notes (size, material, condition, price...)", lines=3)
            btn = gr.Button("Write listing", variant="primary")
        with gr.Column():
            checklist = gr.Markdown()
            listing = gr.Textbox(label="Listing (copy and paste)", lines=16)
    btn.click(write_listing, inputs=[photos, platform, tone, notes], outputs=[checklist, listing])

if __name__ == "__main__":
    demo.launch(share=os.getenv("SHARE") == "1")
