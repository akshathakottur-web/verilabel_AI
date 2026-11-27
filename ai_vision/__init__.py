from .analyze import analyze_image
"""AI vision package (Member 2)."""


def analyze_image(image_path):
    """Contract entry point: ai_vision.analyze_image(image_path).
    Imported lazily so that importing the package stays fast."""
    from ai_vision.analyze import analyze_image as _analyze_image
    return _analyze_image(image_path)