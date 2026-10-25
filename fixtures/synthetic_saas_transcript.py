"""Original synthetic 40-turn SaaS cold call; never use as a real-call example."""

from __future__ import annotations


def build_transcript() -> dict[str, object]:
    """Build a four-minute, deliberately flawed fixture without any private data."""
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
    turns: list[dict[str, object]] = []
    for number in range(1, 41):
        speaker = "Rep" if number % 2 else "Prospect"
        role = "agent" if speaker == "Rep" else "customer"
        start = float((number - 1) * 6)
        text = themes[(number - 1) % len(themes)]
        turns.append(
            {
                "id": f"T{number:03d}",
                "speaker": speaker,
                "role": role,
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
    return {
        "label": "Synthetic fixture — original fictional SaaS cold call.",
        "duration_s": 240.0,
        "language": "en",
        "source_model": "fixture",
        "timing": "word",
        "speakers": ["Rep", "Prospect"],
        "speaker_roles": {"Rep": "agent", "Prospect": "customer"},
        "turns": turns,
    }
