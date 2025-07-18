import csv
from pathlib import Path
import folder_paths

class ValueOverrideNode:
    """Load a specific value from a CSV file based on prompt number and column name"""

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
                "prompt_number": ("INT", {"default": 0}),
                "column_name": ("STRING", {"default": ""}),
            }
        }

    CATEGORY = "Value Override"

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("value",)
    FUNCTION = "get_value"

    def get_value(self, csv_file, prompt_number, column_name):
        if not csv_file:
            print("No CSV file selected")
            return ("",)

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
            return ("",)

        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for i, row in enumerate(reader):
                    if i == prompt_number:
                        return (row.get(column_name, ""),)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except Exception as e:
            print(f"An error occurred: {e}")
        
        return ("",)

NODE_CLASS_MAPPINGS = {
    'ValueOverrideNode': ValueOverrideNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    'ValueOverrideNode': 'Value Override Node'
}
