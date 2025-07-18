import csv
import json
from pathlib import Path
import folder_paths
import os
import re

class MoserStylesFull:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.json_path = os.path.join(self.data_dir, "moser_styles_full_data.json")
        self.load_persistent_data()

    def load_persistent_data(self):
        try:
            with open(self.json_path, 'r') as f:
                self.persistent_data = json.load(f)
        except FileNotFoundError:
            self.persistent_data = {
                "current_number": 1,
                "last_mode": None,
                "last_min": 1,
                "last_max": 100
            }
            self.save_persistent_data()

    def save_persistent_data(self):
        with open(self.json_path, 'w') as f:
            json.dump(self.persistent_data, f)
        
        web_json_path = os.path.join(folder_paths.base_path, "web", "moser_styles_full_data.json")
        with open(web_json_path, 'w') as f:
            json.dump(self.persistent_data, f)

    @classmethod
    def INPUT_TYPES(cls):
        input_dirs = [
            Path(folder_paths.base_path) / "styles",
            Path(r"C:\Users\rober\OneDrive\Documents\Sketchbook")
        ]
        
        csv_files = []
        for input_dir in input_dirs:
            if input_dir.exists():
                csv_files.extend([f.name for f in input_dir.glob("*.csv")])
        
        if not csv_files: csv_files = [""]

        return {
            "required": {
                "prompt_file": (csv_files,),
                "mode": (["Manual", "Random", "Increment", "Decrement"],),
                "previous_prompt": ("INT", {"default": 1, "min": 1, "max": 9999}),
                "next_prompt": ("INT", {"default": 1, "min": 1, "max": 9999}),
                "minimum": ("INT", {"default": 1, "min": 1, "max": 9999}),
                "maximum": ("INT", {"default": 100, "min": 1, "max": 9999}),
            }
        }

    CATEGORY = "Moser"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = ("Positive", "Negative", "PDXL Positive", "PDXL Negative", "PDXL Loras", "Prompt Number", "Prompt Name")
    FUNCTION = "load_style"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN") if kwargs.get("mode") == "Random" else False

    def load_style(self, prompt_file, mode, previous_prompt, next_prompt, minimum, maximum):
        print(f"Executing node with Next Prompt value: {next_prompt}")
        if not prompt_file:
            return ("", "", "", "", "", 0, "")

        # Define default PDXL prefixes
        pdxl_positive_prefix = "score_9, score_8_up, score_8, score_7_up, score_7, RAW, photo, photorealistic, HD, dynamic lighting, masterpiece, rating_explicit, rating_questionable, (realistic:1.3),"
        
        pdxl_negative_prefix = "score_1, score_2, score_3, score_4, score_5, score_6, glitched, distorted, blurry face, low quality, bad quality, low-res, error, jpeg artefacts, cropped, poorly drawn, censored, text, signature, watermark, username, artist name, chibi, ugly face, ugly eyes, bad eyes, deformed eyes, cross-eyed, deformed, disfigured, bad anatomy, wrong anatomy, closed eyes, extra fingers, extra hands, bad hands, low detail, line art, monochrome, grayscale, face asymmetry, eyes asymmetry, multiple eyelids, deformed limbs, deformed body"

        input_dirs = [
            Path(folder_paths.base_path) / "styles",
            Path(r"C:\Users\rober\OneDrive\Documents\Sketchbook")
        ]
        
        file_path = next((p for d in input_dirs if d.exists() for p in [d / prompt_file] if p.exists()), None)
        if not file_path:
            return ("", "", "", "", "", 0, "")

        options = {}
        for encoding in ['utf-8', 'ISO-8859-1', 'utf-16', 'windows-1252']:
            try:
                with open(file_path, encoding=encoding) as f:
                    for row in csv.DictReader(f):
                        number = int(row.get("Number", "0").strip())
                        if number:
                            # Extract loras from positive prompt
                            positive = row.get("Positive", "").strip()
                            pdxl_positive = row.get("Positive", "").strip()
                            pdxl_negative = row.get("Negative", "").strip()
                            pdxl_loras = row.get("PDXL Loras", "").strip()
                            
                            # Find all lora entries in positive string
                            lora_pattern = r'<lora:[^>]+>'
                            loras = re.findall(lora_pattern, positive)
                            
                            # Remove loras from positive string
                            for lora in loras:
                                positive = positive.replace(lora, '')
                            
                            # Add found loras to PDXL loras
                            if loras:
                                pdxl_loras = pdxl_loras + ', ' + ', '.join(loras) if pdxl_loras else ', '.join(loras)
                            
                            # Clean up any double spaces and leading/trailing commas
                            positive = ' '.join(positive.split())
                            pdxl_loras = ' '.join(pdxl_loras.split()).strip(' ,')

                            # Add prefixes to PDXL prompts
                            pdxl_positive = f"{pdxl_positive_prefix}, {pdxl_positive}"
                            pdxl_negative = f"{pdxl_negative_prefix}, {pdxl_negative}"

                            options[number] = (
                                positive,
                                row.get("Negative", "").strip(),
                                pdxl_positive,
                                pdxl_negative,
                                pdxl_loras,
                                number,
                                row.get("Name", "").strip()
                            )
                break
            except UnicodeDecodeError:
                continue
            except Exception:
                return ("", "", "", "", "", 0, "")

        if not options:
            return ("", "", "", "", "", 0, "")

        self.persistent_data.update({
            "current_number": next_prompt,
            "last_mode": mode,
            "last_min": minimum,
            "last_max": maximum
        })
        self.save_persistent_data()

        closest_number = min(options.keys(), key=lambda x: abs(x - next_prompt))
        return options.get(closest_number, ("", "", "", "", "", 0, ""))

NODE_CLASS_MAPPINGS = {"MoserStylesFull": MoserStylesFull}
NODE_DISPLAY_NAME_MAPPINGS = {"MoserStylesFull": "Moser Styles Full"}
