import os
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    Response,
    stream_with_context,
    jsonify,
)
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


load_env_file(Path(__file__).resolve().parents[2] / ".env")


def create_client():
    openai_key = os.getenv("OPENAI_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")

    if openai_key:
        return OpenAI(api_key=openai_key)

    if github_token:
        return OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=github_token,
        )

    raise RuntimeError(
        "No API key configured. Add OPENAI_API_KEY or GITHUB_TOKEN to the project .env file."
    )


client = create_client()
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")

app = Flask(__name__)

chat_history = [
    {"role": "system", "content": "You are a helpful assistant."},
]


def iter_stream_text_chunks(stream):
    for chunk in stream:
        choices = getattr(chunk, "choices", None) or []
        if not choices:
            continue

        choice = choices[0]
        delta = getattr(choice, "delta", None)
        content = getattr(delta, "content", None)
        if content:
            yield content


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", chat_history=chat_history)


@app.route("/chat", methods=["POST"])
def chat():
    content = request.json["message"]
    chat_history.append({"role": "user", "content": content})
    return jsonify(success=True)


@app.route("/stream", methods=["GET"])
def stream():
    def generate():
        assistant_response_content = ""

        try:
            with client.chat.completions.create(
                model=MODEL_NAME,
                messages=chat_history,
                stream=True,
            ) as stream:
                for content in iter_stream_text_chunks(stream):
                    assistant_response_content += content
                    yield f"data: {content}\n\n"
        except Exception as exc:
            assistant_response_content = (
                f"Sorry, I couldn't generate a response right now. {exc}"
            )
            yield f"data: {assistant_response_content}\n\n"
        finally:
            chat_history.append(
                {"role": "assistant", "content": assistant_response_content}
            )

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@app.route("/reset", methods=["POST"])
def reset_chat():
    global chat_history
    chat_history = [{"role": "system", "content": "You are a helpful assistant."}]
    return jsonify(success=True)


if __name__ == "__main__":
    app.run(debug=True)
