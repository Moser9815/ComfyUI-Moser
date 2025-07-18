import json
import os
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import torch
import numpy as np
import csv
from pathlib import Path

import folder_paths

class CCustomMetadataSaver:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "Workflow": ("STRING", {"default": ""}),
                "S1_Checkpoint": ("STRING", {"default": ""}),
                "S1_Sampler": ("STRING", {"default": ""}),
                "S1_Scheduler": ("STRING", {"default": ""}),
                "S1_Seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "S1_Steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "S1_CFG": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "S2_Checkpoint": ("STRING", {"default": ""}),
                "S2_Sampler": ("STRING", {"default": ""}),
                "S2_Scheduler": ("STRING", {"default": ""}),
                "S2_Seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "S2_Steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "S2_CFG": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "S2_Flux_Guidance": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "S2_Denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "Detailer_Checkpoint": ("STRING", {"default": ""}),
                "Upscaler_Checkpoint": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_image_with_custom_metadata"
    OUTPUT_NODE = True
    CATEGORY = "Moser/Savers"

    def save_image_with_custom_metadata(self, images, filename_prefix, Workflow, S1_Checkpoint, S1_Sampler, S1_Scheduler, S1_Seed, S1_Steps, S1_CFG,
                                        S2_Checkpoint, S2_Sampler, S2_Scheduler, S2_Seed, S2_Steps, S2_CFG, S2_Flux_Guidance, S2_Denoise,
                                        Detailer_Checkpoint, Upscaler_Checkpoint):
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        results = list()

        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            custom_metadata = {
                "Workflow": Workflow,
                "S1 Checkpoint": S1_Checkpoint,
                "S1 Sampler": S1_Sampler,
                "S1 Scheduler": S1_Scheduler,
                "S1 Seed": S1_Seed,
                "S1 Steps": S1_Steps,
                "S1 CFG": S1_CFG,
                "S2 Checkpoint": S2_Checkpoint,
                "S2 Sampler": S2_Sampler,
                "S2 Scheduler": S2_Scheduler,
                "S2 Seed": S2_Seed,
                "S2 Steps": S2_Steps,
                "S2 CFG": S2_CFG,
                "S2 Flux Guidance": S2_Flux_Guidance,
                "S2 Denoise": S2_Denoise,
                "Detailer Checkpoint": Detailer_Checkpoint,
                "Upscaler Checkpoint": Upscaler_Checkpoint
            }

            file = f"{filename}_{counter:05}_.png"
            img.save(os.path.join(full_output_folder, file), pnginfo=self.create_pnginfo(custom_metadata))
            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1

        return {"ui": {"images": results}}

    def create_pnginfo(self, metadata):
        pnginfo = PngInfo()
        pnginfo.add_text("CustomMetadata", json.dumps(metadata))
        return pnginfo

class MoserStylesLoader:
    """Load styles from a selected CSV file"""

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = Path(folder_paths.base_path) / "styles"
        if not input_dir.exists():
            input_dir.mkdir(parents=True, exist_ok=True)
        
        csv_files = [f.name for f in input_dir.glob("*.csv")]
        if not csv_files:
            print("No CSV files found in the styles folder. Place at least one csv file in ComfyUI/styles/")
            csv_files = [""]

        return {
            "required": {
                "csv_file": (csv_files,),
                "style_name": ("STRING", {"default": ""}),
            }
        }

    CATEGORY = "Moser"

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "load_style"

    def load_style(self, csv_file, style_name):
        if not csv_file:
            print("No CSV file selected")
            return ("", "")

        input_dir = Path(folder_paths.base_path) / "styles"
        file_path = input_dir / csv_file

        options = {}
        encodings = ['utf-8', 'ISO-8859-1', 'utf-16', 'windows-1252']
        for encoding in encodings:
            try:
                with open(file_path, encoding=encoding) as f:
                    parsed = csv.reader(f)
                    for row in parsed:
                        name, positive, negative = (row + [None] * 3)[:3]
                        name = name.strip() if name else None
                        positive = positive.strip() if positive else ""
                        negative = negative.strip() if negative else ""

                        if name is not None:
                            options[name] = (positive, negative)
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading file {file_path}: {str(e)}")
                return ("", "")

        if style_name not in options:
            print(f"Style '{style_name}' not found in the selected CSV file")
            return ("", "")

        return options[style_name]

NODE_CLASS_MAPPINGS = {
    "CCustomMetadataSaver": CCustomMetadataSaver,
    "MoserStylesLoader": MoserStylesLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CCustomMetadataSaver": "Custom Metadata Saver",
    "MoserStylesLoader": "Moser Styles Loader",
}