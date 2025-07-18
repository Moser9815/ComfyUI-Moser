import os
from PIL import Image
import torch
import numpy as np
import re
import json
from PIL.PngImagePlugin import PngInfo
from datetime import datetime

class SaveImageToSketchbook:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "name": ("STRING", {"default": "image"}),
                "plot": (["yes", "no"],),
                "destination": (["Sketchbook", "Playground"],),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_image"
    OUTPUT_NODE = True

    CATEGORY = "Moser"

    @staticmethod
    def save_image(image, name, plot, destination, prompt=None, extra_pnginfo=None):
        # Define the base directories
        base_dirs = {
            "Sketchbook": r"C:\Users\rober\OneDrive\Documents\Sketchbook",
            "Playground": r"C:\Users\rober\OneDrive\Documents\Playground"
        }

        # Select the base directory based on the destination
        base_dir = base_dirs[destination]

        # Determine the save directory based on the "plot" toggle
        if plot == "yes":
            save_dir = os.path.join(base_dir, "Contact Sheets")
        else:
            save_dir = os.path.join(base_dir, "Images", name)

        # Ensure the directory exists
        os.makedirs(save_dir, exist_ok=True)

        # Get the number of images in the batch
        num_images = image.shape[0]

        for i in range(num_images):
            # Create the base filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"{name}_{timestamp}.png"
            
            # Construct the full file path
            file_path = os.path.join(save_dir, base_filename)
            
            # Check if the file already exists, and if so, add or increment an instance number
            instance = 0
            while os.path.exists(file_path):
                # Extract the current instance number if it exists
                match = re.search(r'_(\d+)\.png$', file_path)
                if match:
                    instance = int(match.group(1))
                instance += 1
                file_path = os.path.join(save_dir, f"{name}_{timestamp}_{instance:04d}.png")

            # Convert the image tensor to a PIL Image
            img_array = 255. * image[i].cpu().numpy()
            img = Image.fromarray(np.clip(img_array, 0, 255).astype(np.uint8))

            # Prepare metadata
            metadata = PngInfo()
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for k, v in extra_pnginfo.items():
                    metadata.add_text(k, json.dumps(v))

            # Save the image with metadata
            img.save(file_path, pnginfo=metadata, optimize=True)

            print(f"Image {i+1}/{num_images} saved to: {file_path}")

        return ()

class PreviewUpdate:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "destination": (["Sketchbook", "Playground"],),
                "pass_type": (["First Pass", "Second Pass", "Detailer", "Flux"],),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_preview"
    OUTPUT_NODE = True
    CATEGORY = "Moser"

    def save_preview(self, images, destination, pass_type, prompt=None, extra_pnginfo=None):
        # Define the base directories
        base_dirs = {
            "Sketchbook": r"C:\Users\rober\OneDrive\Documents\Sketchbook",
            "Playground": r"C:\Users\rober\OneDrive\Documents\Playground"
        }

        # Select the base directory based on the destination
        base_dir = base_dirs[destination]

        # Set the filename based on the selected pass_type
        filename_map = {
            "First Pass": "1 First Pass.png",
            "Second Pass": "2 Second Pass.png",
            "Detailer": "3 Detailer.png",
            "Flux": "4 Flux.png"
        }
        filename = filename_map[pass_type]
        full_path = os.path.join(base_dir, filename)
        
        # Ensure the output folder exists
        os.makedirs(base_dir, exist_ok=True)
        
        # Save the image
        i = 255. * images[0].cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        
        metadata = PngInfo()
        if prompt is not None:
            metadata.add_text("prompt", json.dumps(prompt))
        if extra_pnginfo is not None:
            for k, v in extra_pnginfo.items():
                metadata.add_text(k, json.dumps(v))
        
        img.save(full_path, pnginfo=metadata, compress_level=4)
        
        print(f"Preview image saved to: {full_path}")
        
        return ()

# Add the new node to NODE_CLASS_MAPPINGS
NODE_CLASS_MAPPINGS = {
    "SaveImageToSketchbook": SaveImageToSketchbook,
    "PreviewUpdate": PreviewUpdate
}

# Update NODE_DISPLAY_NAME_MAPPINGS if you want a different display name
NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageToSketchbook": "Save Image To Sketchbook",
    "PreviewUpdate": "Preview Update"
}