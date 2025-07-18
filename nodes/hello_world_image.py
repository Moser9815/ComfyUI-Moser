from PIL import Image, ImageDraw, ImageFont, ImageOps
import torch
import numpy as np
import os
import textwrap
from datetime import datetime

class HelloWorldImageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {"tooltip": "The input image to add text to."}),
                "prompt": ("STRING", {"default": "Your prompt here", "tooltip": "The prompt text to add to the image."}),
                "negative": ("STRING", {"default": "Your negative prompt here", "tooltip": "The negative prompt text to add to the image."}),
                "font_size": ("INT", {"default": 20, "min": 1, "tooltip": "The font size of the text."}),
                "color": ("STRING", {"default": "black", "tooltip": "The color of the text."}),
                "name": ("STRING", {"default": "", "tooltip": "Name of the image"}),
                "prompt_number": ("STRING", {"default": "", "tooltip": "Prompt number"}),
                "initial_checkpoint": (cls.get_checkpoint_list(), {"default": "None", "tooltip": "Initial checkpoint"}),
                "initial_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Initial seed"}),
                "initial_loras": ("STRING", {"default": "", "tooltip": "Initial LoRAs"}),
                "initial_sampler": ("STRING", {"default": "", "tooltip": "Initial sampler"}),
                "initial_scheduler": ("STRING", {"default": "", "tooltip": "Initial scheduler"}),
                "initial_cfg": ("STRING", {"default": "", "tooltip": "Initial CFG"}),
                "initial_steps": ("STRING", {"default": "", "tooltip": "Initial steps"}),
                "refiner_checkpoint": (cls.get_checkpoint_list(), {"default": "None", "tooltip": "Refiner checkpoint"}),
                "refiner_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Refiner seed"}),
                "refiner_loras": ("STRING", {"default": "", "tooltip": "Refiner LoRAs"}),
                "refiner_sampler": ("STRING", {"default": "", "tooltip": "Refiner sampler"}),
                "refiner_scheduler": ("STRING", {"default": "", "tooltip": "Refiner scheduler"}),
                "refiner_cfg": ("STRING", {"default": "", "tooltip": "Refiner CFG"}),
                "refiner_steps": ("STRING", {"default": "", "tooltip": "Refiner steps"}),
                "flux_checkpoint": (cls.get_flux_checkpoint_list(), {"default": "None", "tooltip": "Flux checkpoint"}),
                "flux_seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Flux seed"}),
                "flux_guidance": ("STRING", {"default": "", "tooltip": "Flux guidance"}),
                "flux_steps": ("STRING", {"default": "", "tooltip": "Flux steps"}),
            }
        }
    
    @classmethod
    def get_checkpoint_list(cls):
        checkpoints_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "models", "checkpoints")
        checkpoint_list = ["None"]
        if os.path.exists(checkpoints_dir):
            checkpoint_list.extend([file for file in os.listdir(checkpoints_dir) if file.endswith((".ckpt", ".safetensors"))])
        return checkpoint_list

    @classmethod
    def get_flux_checkpoint_list(cls):
        unet_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "models", "unet")
        flux_checkpoint_list = ["None"]
        if os.path.exists(unet_dir):
            flux_checkpoint_list.extend([file for file in os.listdir(unet_dir) if file.endswith((".ckpt", ".safetensors", ".gguf", ".GGUF"))])
        return flux_checkpoint_list

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "process"
    CATEGORY = "Moser/Savers"

    @staticmethod
    def process(image, prompt, negative, font_size, color, name, prompt_number,
                initial_checkpoint, initial_seed, initial_loras, initial_sampler, initial_scheduler, initial_cfg, initial_steps,
                refiner_checkpoint, refiner_seed, refiner_loras, refiner_sampler, refiner_scheduler, refiner_cfg, refiner_steps,
                flux_checkpoint, flux_seed, flux_guidance, flux_steps):
        # Check if image is None or empty
        if image is None or len(image) == 0:
            print("Warning: Received empty or None image input")
            blank_image = Image.new("RGB", (512, 512), color="white")
            draw = ImageDraw.Draw(blank_image)
            try:
                font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 40)
            except IOError:
                font = ImageFont.load_default()
            text = "No Image"
            text_width, text_height = draw.textsize(text, font=font)
            position = ((512 - text_width) // 2, (512 - text_height) // 2)
            draw.text(position, text, font=font, fill="black")
            input_image = blank_image
        else:
            input_image = Image.fromarray((image[0].cpu().numpy() * 255).astype('uint8'))

        # Layout constants
        page_width, page_height = 2550, 3300  # 8.5" x 11" at 300 DPI
        border = 150  # 1/2 inch border
        gutter = 75  # 1/4 inch gutter
        first_row_height = 450  # 1.5 inches (300 DPI * 1.5)
        cell_width = int((page_width - 2 * border - 4 * gutter) / 5)
        remaining_height = page_height - 2 * border - first_row_height - 3 * gutter
        cell_height = int(remaining_height / 3)  # Divide remaining space into 3 equal rows

        new_image = Image.new("RGB", (page_width, page_height), "white")
        draw = ImageDraw.Draw(new_image)

        # Remove grid lines drawing code

        try:
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            font_bold_path = "C:\\Windows\\Fonts\\arialbd.ttf"
            font = ImageFont.truetype(font_path, font_size)
            font_bold = ImageFont.truetype(font_bold_path, font_size)
        except IOError:
            font = ImageFont.load_default()
            font_bold = ImageFont.load_default()

        # Remove draw_rounded_rectangle function as it's no longer needed

        def wrap_and_draw_text(text, start_x, start_y, max_width, font, font_bold, fill_color, max_height=None, line_spacing=4):
            if text.startswith("Positive:") or text.startswith("Negative:"):
                label, content = text.split(":", 1)
                label += ":"
                
                # Draw the bold label
                draw.text((start_x, start_y), label, font=font_bold, fill=fill_color)
                label_width = font_bold.getsize(label)[0]
                
                # Wrap and draw the content
                lines = textwrap.wrap(content, width=int((max_width - label_width) / font.getsize('A')[0]))
                y = start_y
                for i, line in enumerate(lines):
                    if i == 0:
                        x = start_x + label_width
                    else:
                        x = start_x
                    if max_height and y + font.getsize(line)[1] > start_y + max_height:
                        break
                    draw.text((x, y), line, font=font, fill=fill_color)
                    y += font.getsize(line)[1] + line_spacing
            else:
                lines = textwrap.wrap(text, width=int(max_width / font.getsize('A')[0]))
                y = start_y
                for line in lines:
                    if max_height and y + font.getsize(line)[1] > start_y + max_height:
                        break
                    draw.text((start_x, y), line, font=font, fill=fill_color)
                    y += font.getsize(line)[1] + line_spacing
            return y

        # Top-left cell (black with white text, merging with gutter to its right)
        draw.rectangle([border, border, border + cell_width + gutter, border + first_row_height], fill="black")
        padding = 20
        y = border + padding

        # Load fonts
        try:
            name_font = ImageFont.truetype(font_bold_path, 60)
            prompt_number_font = ImageFont.truetype(font_path, 60)  # Not bold, size 60
            regular_font = ImageFont.truetype(font_path, font_size)
        except IOError:
            name_font = ImageFont.load_default()
            prompt_number_font = ImageFont.load_default()
            regular_font = ImageFont.load_default()

        # Wrap and draw the name
        name_lines = textwrap.wrap(name, width=int(cell_width / name_font.getsize('A')[0]))
        for line in name_lines:
            draw.text((border + padding, y), line, font=name_font, fill="white")
            y += name_font.getsize(line)[1] + 5

        # Draw prompt number with larger, non-bold font
        y += 10  # Add some space after the name
        draw.text((border + padding, y), prompt_number, font=prompt_number_font, fill="white")

        # Add date and time at the bottom of the black box, centered horizontally
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_width, time_height = regular_font.getsize(current_time)
        time_x = border + (cell_width + gutter - time_width) // 2
        time_y = border + first_row_height - padding - time_height
        draw.text((time_x, time_y), current_time, font=regular_font, fill="white")

        # Positive prompt (top row, columns 2-3)
        positive_x = border + cell_width + gutter
        positive_y = border
        positive_width = 2 * cell_width + 1.5 * gutter
        draw.rectangle([positive_x, positive_y, positive_x + positive_width, border + first_row_height], fill="white")
        wrap_and_draw_text("Positive: " + prompt, positive_x + 20, positive_y + 20, 4*cell_width-160, font, font_bold, "black", max_height=first_row_height - 40)

        # Negative prompt (top row, columns 4-5)
        negative_x = border + 3 * cell_width + 2.5 * gutter
        negative_y = border
        negative_width = 2 * cell_width + 1.5 * gutter
        draw.rectangle([negative_x, negative_y, page_width - border, border + first_row_height], fill="white")
        wrap_and_draw_text("Negative: " + negative, negative_x + 20, negative_y + 20, 4*cell_width-160, font, font_bold, "black", max_height=first_row_height - 40)

        # Draw outline around the group of name, positive, and negative boxes
        draw.rectangle([border, border, page_width - border, border + first_row_height], outline="black", width=2)

        # Update draw_info_box function
        def draw_info_box(title, info, x, y, width, height):
            # Create the box image
            box_image = Image.new('RGBA', (width, height), (255, 255, 255, 255))
            box_draw = ImageDraw.Draw(box_image)
            
            # Calculate the maximum height for rotated text (which is the width of the box)
            max_text_height = width - 20  # Leave some padding
            
            # Create a temporary image for all text
            text_image = Image.new('RGBA', (height, max_text_height), (255, 255, 255, 0))
            text_draw = ImageDraw.Draw(text_image)
            
            # Draw title with larger font
            title_font = ImageFont.truetype(font_bold_path, int(font_size * 1.5))
            text_draw.text((0, 0), title, font=title_font, fill="black")
            y_offset = title_font.getsize(title)[1] + 10
            
            # Draw info
            for item in info:
                heading, value = item.split(': ', 1)
                if value.strip():  # Only draw if the value is not empty
                    heading += ':'
                    
                    # Draw heading in bold
                    text_draw.text((0, y_offset), heading, font=font_bold, fill="black")
                    heading_width = font_bold.getsize(heading)[0]
                    
                    # Clip and draw value
                    max_value_width = height - heading_width - 10  # Leave some padding
                    clipped_value = value
                    while font.getsize(clipped_value)[0] > max_value_width and len(clipped_value) > 0:
                        clipped_value = clipped_value[:-1]
                    if clipped_value != value:
                        clipped_value += '...'
                    
                    text_draw.text((heading_width, y_offset), ' ' + clipped_value, font=font, fill="black")
                    y_offset += font.getsize(clipped_value)[1] + 5
            
            # Rotate the text image
            rotated_text = text_image.rotate(90, expand=True)
            
            # Paste the rotated text onto the box image, moved up by 20 pixels
            box_image.paste(rotated_text, (10, -10), rotated_text)
            
            # Paste the box image onto the main image
            new_image.paste(box_image, (x, y), box_image)
            
            # Draw a line along the bottom edge of the cell
            draw.line([(x, y + height), (x + width, y + height)], fill="black", width=1)

        # Draw Initial, Refiner, and Flux boxes
        box_width = cell_width
        box_height = cell_height
        box_x = border

        info_boxes = [
            ("Flux", [
                f"Checkpoint: {flux_checkpoint}",
                f"Seed: {flux_seed}",
                f"Guidance: {flux_guidance}",
                f"Steps: {flux_steps}"
            ]),
            ("Refiner", [
                f"Checkpoint: {refiner_checkpoint}",
                f"Seed: {refiner_seed}",
                f"LoRA: {refiner_loras}",
                f"Sampler: {refiner_sampler}",
                f"Scheduler: {refiner_scheduler}",
                f"CFG: {refiner_cfg}",
                f"Steps: {refiner_steps}"
            ]),
            ("Initial", [
                f"Checkpoint: {initial_checkpoint}",
                f"Seed: {initial_seed}",
                f"LoRA: {initial_loras}",
                f"Sampler: {initial_sampler}",
                f"Scheduler: {initial_scheduler}",
                f"CFG: {initial_cfg}",
                f"Steps: {initial_steps}"
            ])
        ]

        for i, (title, info) in enumerate(info_boxes):
            box_y = border + first_row_height + gutter + i * (cell_height + gutter)
            draw_info_box(title, info, box_x, box_y, box_width, box_height)

        # Calculate image position and size
        image_width = int(4 * cell_width + 3 * gutter)
        image_height = int(3 * cell_height + 2 * gutter)
        image_x = int(border + cell_width + gutter)
        image_y = int(border + first_row_height + gutter)

        # Scale the input image to fit the combined cell
        aspect_ratio = input_image.width / input_image.height
        if aspect_ratio > image_width / image_height:
            new_width = image_width
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = image_height
            new_width = int(new_height * aspect_ratio)

        input_image = input_image.resize((new_width, new_height), Image.LANCZOS)

        # Center the image in the combined cell
        paste_x = image_x + (image_width - new_width) // 2
        paste_y = image_y + (image_height - new_height) // 2
        new_image.paste(input_image, (paste_x, paste_y))

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