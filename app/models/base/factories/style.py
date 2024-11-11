from ....models.content.styles import Style, StyleRegistry


def create_style(style_name: str = "default") -> Style:
    """Creates a Style instance with the specified name

    Available styles: default, formal, casual, technical, simple, elaborate
    """
    registry = StyleRegistry()

    if style_name == "default":
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

    # This already handles invalid style names
    return registry.get_style(style_name)
