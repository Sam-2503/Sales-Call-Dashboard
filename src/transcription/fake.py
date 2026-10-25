"""Network-free transcriber for tests and local fake-mode operation."""

from ingest import AudioAsset
from schemas import Transcript


def _default_fixture() -> Transcript:
    themes = [
        "Hi, I wanted to tell you about our platform",
        "I have only two minutes",
        "We help teams save time",
        "What problem are you trying to solve",
        "Our reporting is manual and slow",
        "That sounds difficult",
        "We automate reporting workflows",
        "How would that work for us",
        "It is easy to configure",
        "What does it cost",
        "Pricing depends on the package",
        "That is more than we expected",
        "Maybe we can discuss it later",
        "We also need compliance assurance",
        "Our customers like the product",
        "Do you meet our data requirements",
        "I can send a brochure",
        "That does not answer my question",
        "Would a demo be useful",
        "Perhaps after we compare options",
        "I will follow up sometime",
        "Please send details first",
    ]
    turns = []
    for number in range(1, 41):
        speaker = "Rep" if number % 2 else "Prospect"
        start = float((number - 1) * 6)
        text = themes[(number - 1) % len(themes)]
        turns.append(
            {
                "id": f"T{number:03d}",
                "speaker": speaker,
                "role": "agent" if speaker == "Rep" else "customer",
                "start_s": start,
                "end_s": start + 6,
                "text": text,
                "words": [
                    {
                        "text": text.split()[0],
                        "speaker": speaker,
                        "start_s": start,
                        "end_s": start + 1,
                    }
                ],
            }
        )
    return Transcript.model_validate(
        {
            "label": "Synthetic fixture — fictional SaaS cold call.",
            "duration_s": 240.0,
            "language": "en",
            "source_model": "fixture",
            "timing": "word",
            "speakers": ["Rep", "Prospect"],
            "speaker_roles": {"Rep": "agent", "Prospect": "customer"},
            "turns": turns,
        }
    )


class FakeTranscriber:
    def __init__(self, transcript: Transcript | None = None) -> None:
        self.fixture = transcript or _default_fixture()

    async def transcribe(self, asset: AudioAsset) -> Transcript:
        return self.fixture.model_copy(
            deep=True, update={"duration_s": asset.duration_s, "source_model": "fake"}
        )
