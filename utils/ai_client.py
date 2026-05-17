import requests, config

HF_API_URL = "https://api-inference.huggingface.co/models/"
HEADERS = {"Authorization": f"Bearer {config.HF_TOKEN}"}

def classify_text(text: str, labels: list[str]) -> dict:
    """Zero-shot classification via HuggingFace free inference."""
    payload = {
        "inputs": text[:512],
        "parameters": {"candidate_labels": labels},
    }
    r = requests.post(
        HF_API_URL + "facebook/bart-large-mnli",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )
    if r.status_code == 200:
        data = r.json()
        return dict(zip(data["labels"], data["scores"]))
    return {}

def summarize_text(text: str) -> str:
    """Summarize a README into 2-3 sentences."""
    payload = {"inputs": text[:1024]}
    r = requests.post(
        HF_API_URL + "facebook/bart-large-cnn",
        headers=HEADERS,
        json=payload,
        timeout=30,
    )
    if r.status_code == 200:
        return r.json()[0].get("summary_text", "")
    return ""