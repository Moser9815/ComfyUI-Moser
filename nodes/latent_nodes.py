import torch

class SetLatentNoiseMaskImproved:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"samples": ("LATENT",)},
                "optional": {"mask": ("MASK",)}}
    RETURN_TYPES = ("LATENT", "STRING")
    RETURN_NAMES = ("LATENT", "STATUS")
    FUNCTION = "set_mask"
    CATEGORY = "Moser/Latent"

    def set_mask(self, samples, mask=None):
        s = samples.copy()
        status_message = "Noise mask not added"
        
        if mask is None:
            # If no mask is provided, return the original samples
            return (s, status_message)
        
        # Check if mask is empty or has zero dimensions
        if mask.numel() == 0 or 0 in mask.shape:
            print("Warning: Empty or zero-dimensional mask provided. Returning original samples without modification.")
            return (s, status_message)
        
        try:
            # Ensure mask has at least 2 dimensions
            if mask.dim() < 2:
                mask = mask.unsqueeze(0).unsqueeze(0)
            elif mask.dim() == 2:
                mask = mask.unsqueeze(0)
            
            # Reshape the mask
            reshaped_mask = mask.reshape((-1, 1, mask.shape[-2], mask.shape[-1]))
            
            s["noise_mask"] = reshaped_mask
            status_message = "Noise mask added"
        except RuntimeError as e:
            print(f"Error reshaping mask: {e}")
            print("Returning original samples without modification.")
        
        return (s, status_message)

class SetLatentNoiseMaskImprovedWithStatus:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "samples": ("LATENT",),
                "text": ("STRING", {"multiline": True}),
            },
            "optional": {"mask": ("MASK",)},
            "hidden": {"unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO"},
        }
    RETURN_TYPES = ("LATENT", "STRING")
    FUNCTION = "set_mask"
    CATEGORY = "Moser/Latent"
    OUTPUT_NODE = True
    OUTPUT_IS_LIST = (False, True)

    def set_mask(self, samples, text, mask=None, unique_id=None, extra_pnginfo=None):
        s = samples.copy()
        status_message = "Noise mask not added"
        
        if mask is not None:
            try:
                # Ensure mask has at least 2 dimensions
                if mask.dim() < 2:
                    mask = mask.unsqueeze(0).unsqueeze(0)
                elif mask.dim() == 2:
                    mask = mask.unsqueeze(0)
                
                # Reshape the mask
                reshaped_mask = mask.reshape((-1, 1, mask.shape[-2], mask.shape[-1]))
                
                s["noise_mask"] = reshaped_mask
                status_message = "Noise mask added"
            except RuntimeError as e:
                print(f"Error reshaping mask: {e}")
                print("Returning original samples without modification.")
        
        if unique_id is not None and extra_pnginfo is not None:
            try:
                workflow = extra_pnginfo["workflow"]
                node = next((x for x in workflow["nodes"] if str(x["id"]) == str(unique_id)), None)
                if node:
                    node["widgets_values"] = [text, status_message]
            except Exception as e:
                print(f"Error updating node widget: {e}")

        return {"ui": {"text": status_message}, "result": (s, [status_message])}

# Keep the original SetLatentNoiseMaskImproved class

NODE_CLASS_MAPPINGS = {
    "SetLatentNoiseMaskImproved": SetLatentNoiseMaskImproved,
    "SetLatentNoiseMaskImprovedWithStatus": SetLatentNoiseMaskImprovedWithStatus
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SetLatentNoiseMaskImproved": "Set Latent Noise Mask (Improved)",
    "SetLatentNoiseMaskImprovedWithStatus": "Set Latent Noise Mask (Improved with Status)"
}