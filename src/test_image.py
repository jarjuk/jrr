from PIL import Image, ImageFont, ImageDraw
from typing import (List, Tuple, Dict, cast, Any)
import os

ALPHA_OPAQUE = 255
ALPHA_INVISIBLE = 0
BLACK = 0
WHITE = 255
ALPHA_VALUE = ALPHA_OPAQUE

COLOR_BLACK = "black"  # (BLACK, BLACK, BLACK, ALPHA_VALUE)
COLOR_WHITE = "white"  # (WHITE, WHITE, WHITE, ALPHA_VALUE)
IMAGE_MODE = "RGB"


class TstImage:

    @property
    def display_size(self) -> Tuple[int, int]:
        return (480, 320)

    def empty_image(self, color: int = COLOR_WHITE, size=None,
                    image_mode=IMAGE_MODE) -> Image.Image:
        """Return black&white image of 'size'  in 'color'.
        """
        if size is None:
            size = self.display_size
        img = Image.new(image_mode, size, color)
        return img

    @property
    def font(self):
        return ImageFont.truetype(os.path.join(os.path.dirname(__file__), 'pic/Font.ttc'), 30)

    def bbox(self, text, x, y):
        dummy_image = Image.new(IMAGE_MODE, self.display_size)
        draw = ImageDraw.Draw(dummy_image)
        box = draw.textbbox(
            (x, y),
            text,
            font=self.font,
            # anchor="lt"
        )
        return box

    def text_image(self, text: str, x: int, y: int, back_color=COLOR_WHITE, border=True) -> Image.Image:
        """Return 'Image' -object with rendered'text'."""
        himage = self.empty_image(color=back_color)
        draw_image = ImageDraw.Draw(himage)
        bbox = self.bbox(text=text, x=x, y=y)
        print(f"{bbox=}")

        if border:
            print("Draw border")
            draw_image.rectangle(bbox,
                                 outline=COLOR_BLACK)
        draw_image.text(
            (x, y),
            text,
            fill=COLOR_BLACK,
            font=self.font,
            stroke_width=1,
        )
        return himage


def tst_1():

    # Create an image of size 480 x 320 with a white background
    image = Image.new("RGB", (480, 320), "white")

    # Initialize the drawing context
    draw = ImageDraw.Draw(image)

    # Define text and position
    text = "hello world"
    position = (10, 20)

    # Draw the text onto the image
    draw.text(position, text, fill="black")

    # Save the image to a file
    output_path = "tmp/output_image.png"
    image.save(output_path)
    print(f"Image created and saved to {output_path}")


def tst_2():
    from PIL import Image, ImageDraw, ImageFont

    # Create an image of size 480 x 320 with a white background
    image = Image.new("RGBA", (480, 320), "white")

    # Initialize the drawing context
    draw = ImageDraw.Draw(image)

    # Define text and position for the first image
    text = "hello world"
    position = (10, 20)

    # Draw the text onto the image
    draw.text(position, text, fill="black")

    # Save the first image to a file
    output_path = "output_image.png"
    image.save("tmp/" + output_path)
    print(f"Image created and saved to {output_path}")

    # Create a second image of size 480 x 320 with a white background
    image2 = Image.new("RGBA", (480, 320), "white")

    # Initialize the drawing context for the second image
    draw2 = ImageDraw.Draw(image2)

    # Define text and position for the second image
    text2 = "Bonjour monde"
    position2 = (10, 100)

    # Draw the text onto the second image
    draw2.text(position2, text2, fill="black")

    # Save the second image to a file
    output_path2 = "output_image_bonjour.png"
    image2.save("tmp/" + output_path2)
    print(f"Second image created and saved to {output_path2}")

    # Combine the two images into a single image
    # Combine the two images by blending them
    # combined_image = Image.new("RGB", (480, 320), "white")
    # combined_image = Image.blend(image, image2, alpha=0.5)
    combined_image = Image.alpha_composite(image, image2)
    # combined_image.paste(image, (0, 0))
    # combined_image.paste(image2, (0, 0))

    # Save the combined image to a file
    output_combined_path = "combined_image.png"
    combined_image.save("tmp/" + output_combined_path)
    print(f"Combined image created and saved to {output_combined_path}")

def tst_3():
    
    # Create an image of size 480 x 320 with a white background
    image = Image.new("RGBA", (480, 320), "white")

    # Initialize the drawing context
    draw = ImageDraw.Draw(image)

    # Define text and position for the first image
    text = "hello world"
    position = (10, 20)

    # Draw the text onto the image
    draw.text(position, text, fill="black")

    # Save the first image to a file
    output_path = "output_image.png"
    image.save( "tmp/" + output_path)
    print(f"Image created and saved to {output_path}")

    # Create a second image of size 480 x 320 with a white background
    image2 = Image.new("RGBA", (480, 320), "white")

    # Initialize the drawing context for the second image
    draw2 = ImageDraw.Draw(image2)

    # Define text and position for the second image
    text2 = "Bonjour monde"
    position2 = (10, 100)

    # Draw the text onto the second image
    draw2.text(position2, text2, fill="black")

    # Save the second image to a file
    output_path2 = "output_image_bonjour.png"
    image2.save( "tmp/" + output_path2)
    print(f"Second image created and saved to {output_path2}")

    # Combine the two images using alpha_composite
    combined_image = Image.alpha_composite(image, image2)

    # Save the combined image to a file
    output_combined_path = "combined_image.png"
    combined_image.save( "tmp/" + output_combined_path)
    print(f"Combined image created and saved to {output_combined_path}")



def main():
    tst_1()
    # tst_2()
    tst_3()
    tst = TstImage()
    canvas = tst.empty_image()
    img = canvas
    img_name = "apu.png"
    img.save(f"tmp/{img_name}")

    text_img = tst.text_image(text="Hello world", x=10, y=10)
    print(f"{text_img=}")
    img_name = "apu_text.png"
    print(f"{img_name=}")
    text_img.save(f"tmp/{img_name}")

    text_img2 = tst.text_image(text="Hei maail", x=10, y=50)
    img_name = "apu2_text.png"
    print(f"{img_name=}")
    text_img2.save(f"tmp/{img_name}")

    canvas = tst.empty_image()
    canvas.paste(text_img)
    # canvas.paste(text_img2)
    # canvas.alpha_composite(text_img2)
    img_name = "canvas.png"
    canvas.save(f"tmp/{img_name}")
    print("done")


if __name__ == '__main__':
    main()
