import importlib.util
import os
from pathlib import Path


os.environ.setdefault("GITHUB_TOKEN", "test-token")

MODULE_PATH = Path(__file__).resolve().parents[1] / "examples" / "chat-basic" / "app.py"

spec = importlib.util.spec_from_file_location("chat_app", MODULE_PATH)
chat_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat_app)


def test_iter_stream_text_chunks_skips_empty_choices():
    class FakeDelta:
        def __init__(self, content):
            self.content = content

    class FakeChoice:
        def __init__(self, delta=None, finish_reason=None):
            self.delta = delta
            self.finish_reason = finish_reason

    class FakeChunk:
        def __init__(self, choices):
            self.choices = choices

    stream = iter(
        [
            FakeChunk([]),
            FakeChunk([FakeChoice(delta=FakeDelta("Hello"))]),
            FakeChunk([FakeChoice(finish_reason="stop")]),
        ]
    )

    assert list(chat_app.iter_stream_text_chunks(stream)) == ["Hello"]
