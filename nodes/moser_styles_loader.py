import csv
from pathlib import Path
import folder_paths
import os

class MoserStylesLoader:
    """Load styles from a selected CSV file"""

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
        
        if not csv_files:
            print("No CSV files found in the styles folder or Sketchbook. Place at least one csv file in ComfyUI/styles/ or C:\\Users\\rober\\OneDrive\\Documents\\Sketchbook\\")
            csv_files = [""]

        return {
            "required": {
                "csv_file": (csv_files,),
                "style_number": ("STRING", {"default": ""}),
            }
        }

    CATEGORY = "Moser"

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "name", "number", "lora")
    FUNCTION = "load_style"

    def load_style(self, csv_file, style_number):
        if not csv_file:
            print("No CSV file selected")
            return ("", "", "", "", "")

        input_dirs = [
            Path(folder_paths.base_path) / "styles",
            Path(r"C:\Users\rober\OneDrive\Documents\Sketchbook")
        ]
        
        file_path = None
        for input_dir in input_dirs:
            temp_path = input_dir / csv_file
            if temp_path.exists():
                file_path = temp_path
                break

        if not file_path:
            print(f"CSV file '{csv_file}' not found in any of the search directories.")
            print(f"Searched directories: {[str(d) for d in input_dirs]}")
            return ("", "", "", "", "")

        options = {}
        encodings = ['utf-8', 'ISO-8859-1', 'utf-16', 'windows-1252']
        for encoding in encodings:
            try:
                with open(file_path, encoding=encoding) as f:
                    parsed = csv.DictReader(f)
                    for row in parsed:
                        number = row.get("Number", "").strip()
                        name = row.get("Name", "").strip()
                        positive = row.get("Positive", "").strip()
                        negative = row.get("Negative", "").strip()
                        lora = row.get("Lora", "").strip()  # New column for Lora

                        if number:
                            options[number] = (positive, negative, name, number, lora)
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading file {file_path}: {str(e)}")
                return ("", "", "", "", "")  # Added an empty string for Lora

        if style_number not in options:
            print(f"Style number '{style_number}' not found in the selected CSV file")
            return ("", "", "", "", "")  # Added an empty string for Lora

        return options[style_number]

NODE_CLASS_MAPPINGS = {
    "MoserStylesLoader": MoserStylesLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MoserStylesLoader": "Moser Styles Loader",
}
