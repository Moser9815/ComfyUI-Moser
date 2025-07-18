import os
from PIL import Image
import torch
import numpy as np
import json
from PIL.PngImagePlugin import PngInfo
from datetime import datetime
import comfy.sd
import folder_paths
import logging
import piexif
import piexif.helper

from .prompt_metadata_extractor import PromptMetadataExtractor
from .utils import get_sha256

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SaveImageWithMetadata:
    def __init__(self):
        self.civitai_sampler_map = {
            'euler_ancestral': 'Euler a',
            'euler': 'Euler',
            'lms': 'LMS',
            'heun': 'Heun',
            'dpm_2': 'DPM2',
            'dpm_2_ancestral': 'DPM2 a',
            'dpmpp_2s_ancestral': 'DPM++ 2S a',
            'dpmpp_2m': 'DPM++ 2M',
            'dpmpp_sde': 'DPM++ SDE',
            'dpmpp_2m_sde': 'DPM++ 2M SDE',
            'dpmpp_3m_sde': 'DPM++ 3M SDE',
            'dpm_fast': 'DPM fast',
            'dpm_adaptive': 'DPM adaptive',
            'ddim': 'DDIM',
            'plms': 'PLMS',
            'uni_pc_bh2': 'UniPC',
            'uni_pc': 'UniPC',
            'lcm': 'LCM',
        }

    @classmethod
    def INPUT_TYPES(cls):
        checkpoint_files = folder_paths.get_filename_list("checkpoints")
        return {
            "required": {
                "images": ("IMAGE",),
                "name": ("STRING", {"default": "image"}),
                "destination": (["Sketchbook", "Playground"],),
                "plot": (["yes", "no", "both"],),
                "extension": (["png", "jpeg", "webp", "gif"],),
                "Stage_One": (checkpoint_files,),
                "Sampler": (comfy.samplers.KSampler.SAMPLERS,),
                "Scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
            },
            "optional": {
                "Stage_Two": (checkpoint_files,{"default": None}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 100.0}),
                "positive": ("STRING", {"default": "", "multiline": True}),
                "negative": ("STRING", {"default": "", "multiline": True}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "quality": ("INT", {"default": 100, "min": 1, "max": 100}),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0}),
                "Loras": ("STRING", {"default": "", "multiline": True}),
                "gif_duration": ("INT", {"default": 500, "min": 100, "max": 5000}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_image"
    OUTPUT_NODE = True
    CATEGORY = "Moser"

    def save_image(self, images, name, destination, plot, extension, Stage_One, Sampler, 
                  Scheduler, Stage_Two=None, steps=20, cfg=7.0, positive="", negative="", 
                  seed=0, quality=100, denoise=1.0, Loras="", gif_duration=500, prompt=None, extra_pnginfo=None):
        
        # Safety check for None images
        if images is None:
            logger.error("No images provided to SaveImageWithMetadata node")
            return ()
        
        # Safety check for empty images tensor
        if images.shape[0] == 0:
            logger.error("Empty images tensor provided to SaveImageWithMetadata node")
            return ()
        
        # Calculate file hash only once per checkpoint
        checkpoint_hashes = {}
        def get_checkpoint_hash(checkpoint):
            if checkpoint not in checkpoint_hashes:
                ckpt_path = folder_paths.get_full_path("checkpoints", checkpoint)
                if ckpt_path:
                    checkpoint_hashes[checkpoint] = get_sha256(ckpt_path)[:10]
            return checkpoint_hashes.get(checkpoint, "")

        # Base directories setup - do once
        base_dirs = {
            "Sketchbook": r"C:\Users\rober\OneDrive\Documents\Sketchbook",
            "Playground": r"C:\Users\rober\OneDrive\Documents\Playground"
        }
        base_dir = base_dirs[destination]
        
        # Determine save directories based on plot selection
        save_dirs = []
        if plot in ["yes", "both"]:
            save_dirs.append(os.path.join(base_dir, "Contact Sheets"))
        if plot in ["no", "both"]:
            save_dirs.append(os.path.join(base_dir, "Images", name))

        # Create all necessary directories
        for save_dir in save_dirs:
            os.makedirs(save_dir, exist_ok=True)

        # Add Loras to positive prompt if provided - do once
        if Loras:
            positive = f"{positive}, {Loras}"

        # Get model hashes - do once
        model_hashes = []
        checkpoints = {
            "Stage_One": Stage_One,
            "Stage_Two": Stage_Two
        }
        
        # Build model hashes string - do once
        for stage, checkpoint in checkpoints.items():
            if checkpoint:
                hash_value = get_checkpoint_hash(checkpoint)
                if hash_value:
                    model_name = os.path.splitext(os.path.basename(checkpoint))[0]
                    model_hashes.append(f"Model hash: {hash_value}")
                    model_hashes.append(f"Model: {model_name}")

        # Extract metadata once
        metadata_extractor = PromptMetadataExtractor([positive, negative])
        embeddings = metadata_extractor.get_embeddings()
        loras = metadata_extractor.get_loras()

        # Get primary model hash for extension_hashes - do once
        primary_hash = get_checkpoint_hash(Stage_One)
        extension_hashes = json.dumps(embeddings | loras | {"model": primary_hash})

        # Create metadata string once
        height, width = images.shape[1], images.shape[2]
        positive_params = self.handle_whitespace(positive)
        negative_params = f"\nNegative prompt: {self.handle_whitespace(negative)}"
        a111_params = (
            f"{positive_params}{negative_params}\n"
            f"Steps: {steps}, Sampler: {self.get_civitai_sampler_name(Sampler.replace('_gpu', ''), Scheduler)}, "
            f"CFG scale: {cfg}, Seed: {seed}, Size: {width}x{height}, "
            f"{', '.join(model_hashes)}, "
            f"Hashes: {extension_hashes}, Version: ComfyUI"
        )

        # Handle multiple images as GIF or individual files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if images.shape[0] > 1:
            # Create GIF from multiple images regardless of extension setting
            filename = f"{name}_{timestamp}.gif"
            
            # Convert all images to PIL format
            pil_images = []
            for i in range(images.shape[0]):
                img = Image.fromarray(np.clip(255. * images[i].cpu().numpy(), 0, 255).astype(np.uint8))
                pil_images.append(img)
            
            # Save GIF to each directory
            for save_dir in save_dirs:
                filepath = os.path.join(save_dir, filename)
                pil_images[0].save(
                    filepath,
                    save_all=True,
                    append_images=pil_images[1:],
                    duration=gif_duration,
                    loop=0,
                    optimize=True
                )
                
                # Add metadata as a comment in the GIF (GIF doesn't support extensive metadata like PNG)
                # The metadata is already included in the filename and can be stored separately if needed
                logger.info(f"Saved GIF with {len(pil_images)} frames to {filepath}")
                
        else:
            # Save individual image (original behavior)
            filename = f"{name}_{timestamp}.{extension}"
            
            # Convert image once for all saves
            img = Image.fromarray(np.clip(255. * images[0].cpu().numpy(), 0, 255).astype(np.uint8))

            # Save to each directory
            for save_dir in save_dirs:
                filepath = os.path.join(save_dir, filename)
                
                if extension == 'png':
                    metadata = PngInfo()
                    metadata.add_text("parameters", a111_params)
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for k, v in extra_pnginfo.items():
                            metadata.add_text(k, json.dumps(v))
                    img.save(filepath, pnginfo=metadata, optimize=True)
                else:
                    img.save(filepath, quality=quality, optimize=True)
                    exif_bytes = piexif.dump({
                        "Exif": {
                            piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(
                                a111_params, 
                                encoding="unicode"
                            )
                        },
                    })
                    piexif.insert(exif_bytes, filepath)

        return ()

    def get_civitai_sampler_name(self, sampler_name, scheduler):
        if sampler_name in self.civitai_sampler_map:
            civitai_name = self.civitai_sampler_map[sampler_name]
            if scheduler == "karras":
                civitai_name += " Karras"
            elif scheduler == "exponential":
                civitai_name += " Exponential"
            return civitai_name
        return f"{sampler_name}_{scheduler}" if scheduler != 'normal' else sampler_name

    @staticmethod
    def handle_whitespace(string):
        return string.strip().replace("\n", " ").replace("\r", " ").replace("\t", " ")

NODE_CLASS_MAPPINGS = {
    "SaveImageWithMetadata": SaveImageWithMetadata
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageWithMetadata": "Save Image With Metadata"
}
