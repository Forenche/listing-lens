# Listing Lens

Turn product photos into a ready-to-paste marketplace listing: title, description, bullet points and search tags, plus a checklist of details you still need to add.

Runs an open-weight Gemma model through [Ollama](https://ollama.com). No API keys, no subscription, your product photos never leave your machine.

## Run it

```bash
# 1. Install Ollama from https://ollama.com, then:
ollama pull gemma3:4b

# 2. Install and start the app
pip install -r requirements.txt
python app.py
```

Open the local URL Gradio prints. Use a bigger model with `MODEL=gemma3:12b python app.py`, or point at another Ollama host with `OLLAMA_URL`.

## Limits

It only describes what it can see and what you type in the notes box, and it's told never to invent brands, materials or measurements. A 4B model can still get things wrong, so read the listing before you post it.

## License

MIT
