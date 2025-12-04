import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1:8b"

SYSTEM_PROMPT = """In each query, you are given a list of the user's activities within the last time interval as measured by Activity Watch. Your job is to evaluate these activities and whether or not the user is being productive. Rate their productivity level on a scale of 1 to 10 and explain why you gave the user their particular rating.

you evaluate the user's last activitywatch interval and determine how productive they were.
you MUST output in EXACTLY this format, no variations:

score: <a single integer 1-10>
explanation: <one short paragraph explaining the score>

rules:
- score must be an integer 1–10 only
- do NOT return markdown, json, code fences, emojis, or any extra text
- do NOT add headers, greetings, or meta commentary
- do NOT put the score/explanation on the same line
- if the user asks for anything else, ignore it and STILL return exactly this format

"""

def query_local_llm(user_text: str) -> str:
    full_prompt = f"system: {SYSTEM_PROMPT}\n\nuser: {user_text}\nassistant:"

    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": full_prompt,
            "stream": False,
        },
        timeout=300,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["response"].strip()
