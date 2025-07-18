import os
import folder_paths
from PIL import Image
import numpy as np

class SendToController:
    def __init__(self):
        self.output_dir = r"C:\Users\rober\OneDrive\Documents\Playground\Controller\images"
        os.makedirs(self.output_dir, exist_ok=True)
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename": ("STRING", {"default": "image"}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "Moser"

    def save_images(self, images, filename):
        # Ensure filename doesn't include extension
        filename = os.path.splitext(filename)[0]
        
        # Convert image
        i = 0
        img = Image.fromarray(np.clip(255. * images[i].cpu().numpy(), 0, 255).astype(np.uint8))
        
        # Save image
        filepath = os.path.join(self.output_dir, f"{filename}.png")
        img.save(filepath)

        return ()

NODE_CLASS_MAPPINGS = {
    "SendToController": SendToController
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SendToController": "Send to Controller"
} 