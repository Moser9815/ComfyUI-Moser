# Import other modules
from .nodes import metadata_saver
from .nodes import latent_nodes
from .nodes import moser_styles_loader
from .nodes import hello_world_image
from .nodes import save_image_to_sketchbook
from .nodes import civitai_metadata_saver
from .nodes import lora_selector
from .nodes import prompt_mixer
from .nodes import extract_positive_prompt
from .nodes import value_override
from .nodes import moser_styles_full
from .nodes import save_image_with_metadata  # Add new import
from .nodes import send_to_controller  # Add this import
from .nodes import first_non_empty_segm  # Add new import
from .nodes import segs_compare  # Add new import
from .nodes import image_fallback  # Add new import

import os
import shutil
import folder_paths

NODE_CLASS_MAPPINGS = {
    **metadata_saver.NODE_CLASS_MAPPINGS,
    **latent_nodes.NODE_CLASS_MAPPINGS,
    **moser_styles_loader.NODE_CLASS_MAPPINGS,
    **hello_world_image.NODE_CLASS_MAPPINGS,
    **save_image_to_sketchbook.NODE_CLASS_MAPPINGS,
    **civitai_metadata_saver.NODE_CLASS_MAPPINGS,
    **lora_selector.NODE_CLASS_MAPPINGS,
    **prompt_mixer.NODE_CLASS_MAPPINGS,
    **extract_positive_prompt.NODE_CLASS_MAPPINGS,
    **value_override.NODE_CLASS_MAPPINGS,
    **moser_styles_full.NODE_CLASS_MAPPINGS,
    **save_image_with_metadata.NODE_CLASS_MAPPINGS,  # Add new mapping
    **send_to_controller.NODE_CLASS_MAPPINGS,  # Add this line
    **first_non_empty_segm.NODE_CLASS_MAPPINGS,  # Add new mapping
    **segs_compare.NODE_CLASS_MAPPINGS,  # Add new mapping
    **image_fallback.NODE_CLASS_MAPPINGS,  # Add new mapping
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **metadata_saver.NODE_DISPLAY_NAME_MAPPINGS,
    **latent_nodes.NODE_DISPLAY_NAME_MAPPINGS,
    **moser_styles_loader.NODE_DISPLAY_NAME_MAPPINGS,
    **hello_world_image.NODE_DISPLAY_NAME_MAPPINGS,
    **save_image_to_sketchbook.NODE_DISPLAY_NAME_MAPPINGS,
    **civitai_metadata_saver.NODE_DISPLAY_NAME_MAPPINGS,
    **lora_selector.NODE_DISPLAY_NAME_MAPPINGS,
    **prompt_mixer.NODE_DISPLAY_NAME_MAPPINGS,
    **extract_positive_prompt.NODE_DISPLAY_NAME_MAPPINGS,
    **value_override.NODE_DISPLAY_NAME_MAPPINGS,
    **moser_styles_full.NODE_DISPLAY_NAME_MAPPINGS,
    **save_image_with_metadata.NODE_DISPLAY_NAME_MAPPINGS,  # Add new mapping
    **send_to_controller.NODE_DISPLAY_NAME_MAPPINGS,  # Add this line
    **first_non_empty_segm.NODE_DISPLAY_NAME_MAPPINGS,  # Add new mapping
    **segs_compare.NODE_DISPLAY_NAME_MAPPINGS,  # Add new mapping
    **image_fallback.NODE_DISPLAY_NAME_MAPPINGS,  # Add new mapping
}

# Copy the JavaScript file to the appropriate location
js_src = os.path.join(os.path.dirname(__file__), "js", "moser_styles_full.js")
js_dest = os.path.join(folder_paths.base_path, "web", "extensions", "moser_styles_full.js")

# Create a symbolic link for the JSON file
json_src = os.path.join(os.path.dirname(__file__), "data", "moser_styles_full_data.json")
json_dest = os.path.join(folder_paths.base_path, "web", "moser_styles_full_data.json")

# Ensure the destination directory exists
os.makedirs(os.path.dirname(js_dest), exist_ok=True)

# Copy the JavaScript file
if not os.path.exists(js_dest) or os.path.getmtime(js_src) > os.path.getmtime(js_dest):
    shutil.copy2(js_src, js_dest)
    print(f"Copied {js_src} to {js_dest}")

# Create symbolic link for JSON file
if os.path.exists(json_dest):
    os.remove(json_dest)
try:
    os.symlink(json_src, json_dest)
    print(f"Created symbolic link from {json_src} to {json_dest}")
except OSError as e:
    # If symlink fails, try to copy the file
    shutil.copy2(json_src, json_dest)
    print(f"Copied {json_src} to {json_dest}")

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
