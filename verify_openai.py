import os
from pathlib import Path
from openai import OpenAI


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file(Path(__file__).resolve().parent / ".env")

openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN")

if os.getenv("OPENAI_API_KEY"):
    client = OpenAI(api_key=openai_key)
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
else:
    client = OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=openai_key,
    )
    model = os.getenv("OPENAI_MODEL", "gpt-4o")

print("key present", bool(openai_key))
try:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say hello in one word."}],
        timeout=60,
    )
    print("ok", response.choices[0].message.content)
except Exception as e:
    print(type(e).__name__)
    print(e)
