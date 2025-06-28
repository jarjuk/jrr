import pytest
import os

from PIL import Image, ImageDraw, ImageFont

def calculate_text_bbox(text, font_path, font_size):
    """
    Calculate the bounding box of a text string for a given font.

    Args:
        text (str): The text string to measure.
        font_path (str): Path to the TrueType font (.ttf) file.
        font_size (int): Size of the font.

    Returns:
        tuple: Bounding box of the text (left, top, right, bottom).
    """
    # Create a dummy image
    dummy_image = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy_image)

    # Load the font
    font = ImageFont.truetype(font_path, font_size)

    # Calculate the bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    
    return bbox


# Example usage
def test_bbox():
    # Replace with the path to your .ttf font file
    # font_path = "/home/jj/work/järviradio-radio/src/pic/Font.ttc"
    font_path = os.path.join(os.path.dirname(__file__), "../src/pic/Font.ttc")
    print(f"{font_path=}")
    font_size = 20
    text = "01234"

    bbox = calculate_text_bbox(text, font_path, font_size)
    print(f"Bounding box for text '{text}' with {font_size=}: {bbox}")
    # Assert false to see output
    assert True
