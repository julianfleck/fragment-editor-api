from ....models.content.styles import Style


def create_style() -> Style:
    """Creates a default Style instance with neutral settings"""
    return Style(
        name="default",
        formality=0.5,  # neutral formality
        complexity=0.5,  # neutral complexity
        tone="neutral",
        characteristics={
            "vocabulary": "standard",
            "sentence_structure": "balanced",
            "neutral": True
        }
    )
