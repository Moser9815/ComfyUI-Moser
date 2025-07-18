class ImageFallback:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "image_1": ("IMAGE", {"default": None}),
                "image_2": ("IMAGE", {"default": None}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "process"
    CATEGORY = "Moser"

    def process(self, **kwargs):
        # Get the inputs from kwargs, with None as default
        image_1 = kwargs.get('image_1', None)
        image_2 = kwargs.get('image_2', None)
        
        # Check if image_1 exists and is not empty
        if image_1 is not None and len(image_1) > 0:
            return (image_1,)
        
        # If image_1 is empty or None, return image_2 if it exists
        if image_2 is not None and len(image_2) > 0:
            return (image_2,)
        
        # If both images are empty, return an empty tensor to prevent errors
        # This maintains the expected return type while avoiding crashes
        import torch
        return (torch.zeros((1, 3, 512, 512)),)

NODE_CLASS_MAPPINGS = {
    "ImageFallback": ImageFallback
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageFallback": "Image Fallback"
} 