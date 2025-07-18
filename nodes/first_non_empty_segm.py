class FirstNonEmptySegm:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "segs_1": ("SEGS",),
            },
            "optional": {
                "segs_2": ("SEGS", {"default": None}),
                "segs_3": ("SEGS", {"default": None}),
            }
        }

    RETURN_TYPES = ("SEGS",)
    FUNCTION = "process"
    CATEGORY = "Moser"

    def process(self, segs_1, segs_2=None, segs_3=None):
        # Check each segs in order and return the first non-empty one
        if segs_1 and len(segs_1) > 0:
            return (segs_1,)
        if segs_2 and len(segs_2) > 0:
            return (segs_2,)
        if segs_3 and len(segs_3) > 0:
            return (segs_3,)
        
        # If all are empty, return an empty list
        # This prevents errors while maintaining the expected return type
        return ([],)

NODE_CLASS_MAPPINGS = {
    "FirstNonEmptySegm": FirstNonEmptySegm
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FirstNonEmptySegm": "First Non-Empty Segs"
} 