import os
import json
import folder_paths
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import numpy as np
from datetime import datetime
import piexif
import piexif.helper
import comfy.sd
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import from local files
from .prompt_metadata_extractor import PromptMetadataExtractor
from .utils import get_sha256, civitai_embedding_key_name, civitai_lora_key_name, full_embedding_path_for, full_lora_path_for

class CivitaiImageSaver:
    def __init__(self):
        self.output_dir = folder_paths.output_directory
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
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "image(s) to save"}),
                "path": ("STRING", {"default": '', "multiline": False, "tooltip": "path to save the images (under Comfy's save directory)"}),
                "extension": (["png", "jpeg", "webp"], {"tooltip": "file extension/type to save image as"}),
                "Checkpoint": (folder_paths.get_filename_list("checkpoints"), {"tooltip": "checkpoint to use"}),
                "Sampler": (comfy.samplers.KSampler.SAMPLERS, {"tooltip": "sampler to use"}),
                "Scheduler": (comfy.samplers.KSampler.SCHEDULERS, {"tooltip": "scheduler to use"}),
            },
            "optional": {
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000, "tooltip": "number of steps"}),
                "cfg": ("FLOAT", {"default": 7.0, "min": 0.0, "max": 100.0, "tooltip": "CFG value"}),
                "positive": ("STRING", {"default": 'unknown', "multiline": True, "tooltip": "positive prompt"}),
                "negative": ("STRING", {"default": 'unknown', "multiline": True, "tooltip": "negative prompt"}),
                "seed_value": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "seed"}),
                "quality_jpeg_or_webp": ("INT", {"default": 100, "min": 1, "max": 100, "tooltip": "quality setting of JPEG/WEBP"}),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "tooltip": "denoise value"}),
                "Loras": ("STRING", {"default": "", "multiline": True, "tooltip": "Additional LoRAs to add to the prompt"}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "lossless_webp": ("BOOLEAN", {"default": True}),
                "optimize_png": ("BOOLEAN", {"default": False}),
                "counter": ("INT", {"default": 0}),
                "time_format": ("STRING", {"default": "%Y-%m-%d-%H%M%S"}),
                "save_workflow_as_json": ("BOOLEAN", {"default": False}),
                "embed_workflow_in_png": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_files"
    OUTPUT_NODE = True
    CATEGORY = "Moser"
    DESCRIPTION = "Save images with civitai-compatible generation metadata"

    def save_files(self, images, Checkpoint, Sampler, Scheduler, steps, cfg, positive, negative, seed_value, quality_jpeg_or_webp, denoise, path, extension, Loras="", prompt=None, extra_pnginfo=None, lossless_webp=True, optimize_png=False, counter=0, time_format="%Y-%m-%d-%H%M%S", save_workflow_as_json=False, embed_workflow_in_png=True):
        # Add Loras to the positive prompt if provided
        if Loras:
            positive = f"{positive}, {Loras}"

        # Calculate width and height from the input image
        height, width = images.shape[1], images.shape[2]

        # Generate filename using the convention from send to sketchbook node
        timestamp = datetime.now().strftime(time_format)
        filename = f"{timestamp}_{Checkpoint.split('.')[0]}_{seed_value}"

        ckpt_path = folder_paths.get_full_path("checkpoints", Checkpoint)

        modelhash = self.get_sha256(ckpt_path)[:10] if ckpt_path else ""
        logger.debug(f"Model hash: {modelhash}")

        metadata_extractor = PromptMetadataExtractor([positive, negative])
        embeddings = metadata_extractor.get_embeddings()
        loras = metadata_extractor.get_loras()
        logger.debug(f"Extracted embeddings: {embeddings}")
        logger.debug(f"Extracted LoRAs: {loras}")

        civitai_sampler_name = self.get_civitai_sampler_name(Sampler.replace('_gpu', ''), Scheduler)
        logger.debug(f"Civitai sampler name: {civitai_sampler_name}")

        extension_hashes = json.dumps(embeddings | loras | {"model": modelhash})
        logger.debug(f"Extension hashes: {extension_hashes}")

        basemodelname = self.parse_checkpoint_name_without_extension(Checkpoint)
        logger.debug(f"Base model name: {basemodelname}")

        positive_a111_params = self.handle_whitespace(positive)
        negative_a111_params = f"\nNegative prompt: {self.handle_whitespace(negative)}"
        a111_params = f"{positive_a111_params}{negative_a111_params}\nSteps: {steps}, Sampler: {civitai_sampler_name}, CFG scale: {cfg}, Seed: {seed_value}, Size: {width}x{height}, Model hash: {modelhash}, Model: {basemodelname}, Hashes: {extension_hashes}, Version: ComfyUI"
        logger.debug(f"A1111 parameters: {a111_params}")

        output_path = os.path.join(self.output_dir, path)

        if output_path.strip() != '':
            if not os.path.exists(output_path.strip()):
                logger.info(f'The path `{output_path.strip()}` specified doesn\'t exist! Creating directory.')
                os.makedirs(output_path, exist_ok=True)

        filenames = self.save_images(images, output_path, filename, a111_params, extension, quality_jpeg_or_webp, lossless_webp, optimize_png, prompt, extra_pnginfo, save_workflow_as_json, embed_workflow_in_png)

        subfolder = os.path.normpath(path)
        return {"ui": {"images": [{"filename": filename, "subfolder": subfolder if subfolder != '.' else '', "type": 'output'} for filename in filenames]}}

    def save_images(self, images, output_path, filename_prefix, a111_params, extension, quality_jpeg_or_webp, lossless_webp, optimize_png, prompt, extra_pnginfo, save_workflow_as_json, embed_workflow_in_png):
        paths = []
        for i, image in enumerate(images):
            img = Image.fromarray(np.clip(255. * image.cpu().numpy(), 0, 255).astype(np.uint8))
            current_filename_prefix = f"{filename_prefix}_{i+1:02d}" if images.shape[0] > 1 else filename_prefix

            if extension == 'png':
                metadata = PngInfo()
                metadata.add_text("parameters", a111_params)
                if embed_workflow_in_png:
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))
                filename = f"{current_filename_prefix}.png"
                img.save(os.path.join(output_path, filename), pnginfo=metadata, optimize=optimize_png)
            else:
                filename = f"{current_filename_prefix}.{extension}"
                file = os.path.join(output_path, filename)
                img.save(file, optimize=True, quality=quality_jpeg_or_webp, lossless=lossless_webp)
                exif_bytes = piexif.dump({
                    "Exif": {
                        piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(a111_params, encoding="unicode")
                    },
                })
                piexif.insert(exif_bytes, file)

            if save_workflow_as_json:
                self.save_json(extra_pnginfo, os.path.join(output_path, current_filename_prefix))

            paths.append(filename)
        return paths

    def get_civitai_sampler_name(self, sampler_name, scheduler):
        if sampler_name in self.civitai_sampler_map:
            civitai_name = self.civitai_sampler_map[sampler_name]
            if scheduler == "karras":
                civitai_name += " Karras"
            elif scheduler == "exponential":
                civitai_name += " Exponential"
            return civitai_name
        else:
            return f"{sampler_name}_{scheduler}" if scheduler != 'normal' else sampler_name

    @staticmethod
    def make_filename(filename, seed, modelname, counter, time_format, sampler_name, steps, cfg, scheduler, denoise):
        filename = filename.replace("%date", CivitaiImageSaver.get_timestamp("%Y-%m-%d"))
        filename = filename.replace("%time", CivitaiImageSaver.get_timestamp(time_format))
        filename = filename.replace("%model", CivitaiImageSaver.parse_checkpoint_name(modelname))
        filename = filename.replace("%seed", str(seed))
        filename = filename.replace("%counter", str(counter))
        filename = filename.replace("%sampler_name", sampler_name)
        filename = filename.replace("%steps", str(steps))
        filename = filename.replace("%cfg", str(cfg))
        filename = filename.replace("%scheduler", scheduler)
        filename = filename.replace("%basemodelname", CivitaiImageSaver.parse_checkpoint_name_without_extension(modelname))
        filename = filename.replace("%denoise", str(denoise))
        return CivitaiImageSaver.get_timestamp(time_format) if filename == "" else filename

    @staticmethod
    def make_pathname(path, seed, modelname, counter, time_format, sampler_name, steps, cfg, scheduler, denoise):
        return CivitaiImageSaver.make_filename(path, seed, modelname, counter, time_format, sampler_name, steps, cfg, scheduler, denoise)

    @staticmethod
    def get_timestamp(time_format):
        now = datetime.now()
        try:
            timestamp = now.strftime(time_format)
        except:
            timestamp = now.strftime("%Y-%m-%d-%H%M%S")
        return timestamp

    @staticmethod
    def parse_checkpoint_name(ckpt_name):
        return os.path.basename(ckpt_name)

    @staticmethod
    def parse_checkpoint_name_without_extension(ckpt_name):
        return os.path.splitext(CivitaiImageSaver.parse_checkpoint_name(ckpt_name))[0]

    @staticmethod
    def handle_whitespace(string):
        return string.strip().replace("\n", " ").replace("\r", " ").replace("\t", " ")

    @staticmethod
    def get_sha256(filename):
        return get_sha256(filename)

    @staticmethod
    def save_json(image_info, filename):
        try:
            workflow = (image_info or {}).get('workflow')
            if workflow is None:
                print('No image info found, skipping saving of JSON')
            with open(f'{filename}.json', 'w') as workflow_file:
                json.dump(workflow, workflow_file)
                print(f'Saved workflow to {filename}.json')
        except Exception as e:
            print(f'Failed to save workflow as json due to: {e}, proceeding with the remainder of saving execution')

NODE_CLASS_MAPPINGS = {
    "CivitaiImageSaver": CivitaiImageSaver
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CivitaiImageSaver": "Civitai Image Saver"
}
