import csv
import os
import random
import re
from pathlib import Path
import folder_paths

class MoserPromptMixer:
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
                "prompt_number1": ("INT", {"default": 1, "min": 1, "max": 9999, "step": 1}),
                "prompt_number2": ("INT", {"default": 2, "min": 1, "max": 9999, "step": 1}),
                "num_tags": ("INT", {"default": 5, "min": 1, "max": 50, "step": 1}),
            },
            "optional": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("mixed_prompt", "original_prompt")
    FUNCTION = "mix_prompts"
    CATEGORY = "Moser"

    def mix_prompts(self, csv_file, prompt_number1, prompt_number2, num_tags, seed=0):
        if not csv_file:
            print("No CSV file selected")
            return ("", "")

        # Set the random seed if provided
        if seed != 0:
            random.seed(seed)

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
            return ("", "")

        prompts = self.load_prompts_from_csv(file_path)
        if not prompts:
            return ("", "")

        if prompt_number1 not in prompts:
            print(f"Prompt number {prompt_number1} not found in the CSV file.")
            return ("", "")

        if prompt_number2 not in prompts:
            print(f"Prompt number {prompt_number2} not found in the CSV file.")
            return ("", "")

        current_prompt = prompts[prompt_number1]
        second_prompt = prompts[prompt_number2]

        # Split prompts into long sections and short tags
        long_sections, short_tags = self.split_long_and_short(current_prompt)
        _, second_short_tags = self.split_long_and_short(second_prompt)

        # Combine short tags from both prompts
        all_short_tags = short_tags + second_short_tags

        # Randomly select tags from short tags
        selected_tags = random.sample(all_short_tags, min(num_tags, len(all_short_tags)))

        # Combine long sections and selected short tags
        mixed_prompt = ", ".join(long_sections + selected_tags)

        return (mixed_prompt, current_prompt)

    def load_prompts_from_csv(self, file_path):
        prompts = {}
        encodings = ['utf-8', 'ISO-8859-1', 'utf-16', 'windows-1252']
        for encoding in encodings:
            try:
                with open(file_path, encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if 'Number' in row and 'Positive' in row:
                            try:
                                number = int(row['Number'])
                                prompts[number] = row['Positive'].strip()
                            except ValueError:
                                print(f"Invalid number format in row: {row['Number']}")
                return prompts
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading file {file_path}: {str(e)}")
                return {}
        print(f"Unable to read the CSV file with any of the attempted encodings.")
        return {}

    def split_long_and_short(self, prompt):
        # Split the prompt into sections
        sections = [section.strip() for section in re.split(r',\s*', prompt) if section.strip()]
        
        # Separate long sections (more than 3 words) and short tags
        long_sections = [section for section in sections if len(section.split()) > 3]
        short_tags = [section for section in sections if len(section.split()) <= 3]
        
        return long_sections, short_tags

    @classmethod
    def IS_CHANGED(s, csv_file, prompt_number1, prompt_number2, num_tags, seed=0):
        return float(prompt_number1) + float(prompt_number2) + float(num_tags) + float(seed)

# Add custom node mappings
NODE_CLASS_MAPPINGS = {
    "MoserPromptMixer": MoserPromptMixer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MoserPromptMixer": "Moser Prompt Mixer",
}
