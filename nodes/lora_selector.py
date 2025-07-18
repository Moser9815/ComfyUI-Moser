import os
import folder_paths
from server import PromptServer
from aiohttp import web
import logging
import re

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MoserLoRASelector:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "lora": (s.get_loras(), ),
                "strength": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "keyword": ("STRING", {"multiline": True}),
            },
            "optional": {
                "Combined": ("STRING", {"forceInput": True}),
                "Lora": ("STRING", {"forceInput": True}),
                "Positive": ("STRING", {"forceInput": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("Combined", "Lora", "Positive")
    FUNCTION = "generate_strings"
    CATEGORY = "Moser"

    # Add this class attribute to identify it as a LoRA node
    TYPES = ["LoRA"]

    def __init__(self):
        self.lora_dir = folder_paths.get_folder_paths("loras")[0]

    def generate_strings(self, lora, strength, keyword, Combined="", Lora="", Positive=""):
        # Strip the folder name from the lora path
        lora_filename = os.path.basename(lora) if lora != "None" else ""
        new_lora_string = f"<lora:{lora_filename}:{strength}>" if lora != "None" else ""
        new_keyword_string = keyword.strip()

        def separate_loras_and_text(input_string):
            lora_pattern = r'<lora:[^>]+>'
            loras = re.findall(lora_pattern, input_string)
            
            # Split the input string by LoRAs
            text_parts = re.split(lora_pattern, input_string)
            
            # Remove empty strings and strip whitespace
            text_parts = [part.strip() for part in text_parts if part.strip()]
            
            return loras, text_parts

        # Process all inputs
        all_loras = set()
        all_text_parts = []

        for input_str in [Combined, Lora, Positive]:
            loras, text_parts = separate_loras_and_text(input_str)
            all_loras.update(loras)
            all_text_parts.extend(text_parts)

        # Add new LoRA and keyword
        if new_lora_string:
            all_loras.add(new_lora_string)
        if new_keyword_string:
            all_text_parts.append(new_keyword_string)

        # Create output strings
        Lora = ', '.join(sorted(all_loras))
        Positive = ', '.join(filter(bool, all_text_parts))  # Remove any empty strings
        new_combined_string = f"{Lora}, {Positive}" if Positive else Lora

        # Remove any double commas and leading/trailing commas and spaces
        new_combined_string = re.sub(r',\s*,', ',', new_combined_string).strip(', ')
        Lora = Lora.strip(', ')
        Positive = Positive.strip(', ')

        return (new_combined_string, Lora, Positive)

    @classmethod
    def get_loras(s):
        lora_dir = folder_paths.get_folder_paths("loras")[0]
        loras = ["None"]  # Add "None" as the first option
        for root, dirs, files in os.walk(lora_dir):
            for file in files:
                if file.endswith(('.safetensors', '.ckpt', '.pt')):
                    loras.append(os.path.relpath(os.path.join(root, file), lora_dir))
        return sorted(loras)

    @classmethod
    def IS_CHANGED(s, lora, strength, keyword, Combined="", Lora="", Positive=""):
        return float(strength)

    @classmethod
    def VALIDATE_INPUTS(s, lora, strength, keyword, Combined="", Lora="", Positive=""):
        if lora != "None" and not lora:
            return "No LoRA selected"
        try:
            strength_float = float(strength)
            if strength_float < -10.0 or strength_float > 10.0:
                return f"Strength must be between -10.0 and 10.0, got {strength_float}"
        except ValueError:
            return f"Invalid strength value: {strength}"
        return True

# Add custom node mappings
NODE_CLASS_MAPPINGS = {
    "MoserLoRASelector": MoserLoRASelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MoserLoRASelector": "Moser LoRA Selector",
}
