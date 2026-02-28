import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
SUMMARY_MODEL = "llama3.2:3b"


def generate_structured_summary(interactions):

    if not interactions:
        return ""

    print("Preparing transcript...")

    transcript = ""
    for i, (orig, rephrased) in enumerate(interactions, 1):
        transcript += f"Turn {i}:\nUser: {orig}\nNormalized: {rephrased}\n\n"

    prompt = f"""
You are a strict summarization engine.

Summarize the following conversation into this exact structure:

Topic:
Intent:
Keywords:
Condensed Summary:

Keep it concise.
Do not add explanations.
Do not hallucinate.
Only summarize what is present.

Conversation:
{transcript}
"""

    print("Sending request to Ollama...")

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": SUMMARY_MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0,
            "num_predict": 200
        },
        timeout=60
    )

    print("Response received.")

    response.raise_for_status()

    data = response.json()

    if "response" not in data:
        raise RuntimeError("Invalid response from Ollama")

    print("Summary generated.")

    return data["response"].strip()