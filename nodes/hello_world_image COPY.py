from PIL import Image, ImageDraw, ImageFont, ImageOps  # Add ImageOps here
import torch
import numpy as np  # Import numpy
import os

class HelloWorldImageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "The input image to add text to."}),
                "prompt": ("STRING", {"default": "Your prompt here", "tooltip": "The prompt text to add to the image."}),
                "negative": ("STRING", {"default": "Your negative prompt here", "tooltip": "The negative prompt text to add to the image."}),
                "font_size": ("INT", {"default": 20, "min": 1, "tooltip": "The font size of the text."}),
                "color": ("STRING", {"default": "black", "tooltip": "The color of the text."})
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "process"

    @staticmethod
    def process(image, prompt, negative, font_size, color):
        # Check if image is None or empty
        if image is None or len(image) == 0:
            print("Warning: Received empty or None image input")
            # Create a blank image as a fallback
            blank_image = Image.new("RGB", (512, 512), color="white")
            draw = ImageDraw.Draw(blank_image)
            
            # Load a font (use default if Arial is not available)
            try:
                font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 40)
            except IOError:
                font = ImageFont.load_default()
            
            # Get the size of the text
            text = "No Image"
            text_width, text_height = draw.textsize(text, font=font)
            
            # Calculate the position to center the text
            position = ((512 - text_width) // 2, (512 - text_height) // 2)
            
            # Draw the text
            draw.text(position, text, font=font, fill="black")
            
            input_image = blank_image
        else:
            # Convert the input image tensor to a PIL image
            input_image = Image.fromarray((image[0].cpu().numpy() * 255).astype('uint8'))

        # Constants for the page layout
        page_width, page_height = 2550, 3300  # 8.5 x 11 inches at 300 DPI
        border = 150  # 0.5 inch border at 300 DPI
        gutter = 30  # Reduced gutter for 5 columns
        column_width = (page_width - 2 * border - 4 * gutter) // 5
        text_image_width = column_width * 4 + 3 * gutter  # Four columns width for text and image
        text_height = 300  # 1 inch for text above the image

        # Calculate scaling factor to fit within constraints while maintaining aspect ratio
        width_ratio = text_image_width / input_image.width
        height_ratio = (page_height - 2 * border - text_height) / input_image.height
        scale_factor = min(width_ratio, height_ratio)

        # Calculate new dimensions
        new_width = int(input_image.width * scale_factor)
        new_height = int(input_image.height * scale_factor)

        # Scale the input image
        input_image = input_image.resize((new_width, new_height), Image.LANCZOS)

        # Add black border to the image
        border_width = 2  # Width of the border in pixels
        input_image = ImageOps.expand(input_image, border=border_width, fill='black')

        # Create a new image with white background
        new_image = Image.new("RGB", (page_width, page_height), "white")

        # Calculate column positions
        prompt_x = border + column_width + gutter
        negative_x = border + 3 * column_width + 3 * gutter

        # Initialize ImageDraw
        draw = ImageDraw.Draw(new_image)

        # Define the fonts
        try:
            # Try to load Arial with different styles
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            font_bold_path = "C:\\Windows\\Fonts\\arialbd.ttf"
            font_italic_path = "C:\\Windows\\Fonts\\ariali.ttf"
            
            if os.path.exists(font_bold_path):
                font_bold = ImageFont.truetype(font_bold_path, font_size)
            else:
                font_bold = ImageFont.truetype(font_path, font_size)
            
            if os.path.exists(font_italic_path):
                font_italic = ImageFont.truetype(font_italic_path, font_size)
            else:
                font_italic = ImageFont.truetype(font_path, font_size)
        except IOError:
            # Fallback to default font if Arial is not available
            font_bold = ImageFont.load_default()
            font_italic = ImageFont.load_default()

        # Draw "Prompt:" in bold
        draw.text((prompt_x, border), "Prompt:", font=font_bold, fill=color)

        # Draw "Negative:" in bold
        draw.text((negative_x, border), "Negative:", font=font_bold, fill=color)

        # Helper function to wrap and draw text
        def wrap_and_draw_text(text, start_x, max_width):
            lines = []
            words = text.split()
            line = []
            h = draw.textsize("Tg", font=font_italic)[1]  # Get a default height
            for word in words:
                line.append(word)
                w, new_h = draw.textsize(' '.join(line), font=font_italic)
                if w > max_width:
                    line.pop()
                    lines.append(' '.join(line))
                    line = [word]
                h = max(h, new_h)  # Update h with the maximum height encountered
            lines.append(' '.join(line))

            text_y = border + font_size + 10  # Start below the label
            for line in lines:
                draw.text((start_x, text_y), line, font=font_italic, fill=color)
                text_y += h

        # Draw the prompt text
        wrap_and_draw_text(prompt, prompt_x, 2 * column_width + gutter)

        # Draw the negative prompt text
        wrap_and_draw_text(negative, negative_x, 2 * column_width + gutter)

        # Calculate position for the image (bottom of the page, spanning right 4 columns)
        image_x = border + column_width + gutter  # Start from the second column
        image_y = page_height - border - input_image.height

        # Paste the input image
        new_image.paste(input_image, (image_x, image_y))

        # Convert the new image back to a tensor
        output_image = torch.from_numpy(np.array(new_image).astype(np.float32) / 255.0).unsqueeze(0)
        
        return (output_image,)

# Node class mappings
NODE_CLASS_MAPPINGS = {
    'HelloWorldImageNode': HelloWorldImageNode
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    'HelloWorldImageNode': 'Hello World Image Node'
}