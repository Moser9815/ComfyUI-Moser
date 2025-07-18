import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SegsCompare:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "segs_1": ("SEGS",),
                "segs_2": ("SEGS",),
            }
        }

    RETURN_TYPES = ("SEGS", "SEGS")
    RETURN_NAMES = ("original_segs", "remaining_segs")
    FUNCTION = "process"
    CATEGORY = "Moser"

    def process(self, segs_1, segs_2):
        # First output is just the original segs_1
        original_segs = segs_1

        # For the second output, we need to subtract segs_1 areas from segs_2
        remaining_segs = []
        
        # Create a combined mask of all segments in segs_1
        combined_mask = None
        
        # Extract masks from segs_1
        for item in segs_1:
            if not isinstance(item, dict):
                continue
                
            seg_mask = item.get('mask')
            if seg_mask is None or not isinstance(seg_mask, np.ndarray):
                continue

            if combined_mask is None:
                combined_mask = seg_mask.copy()
            else:
                combined_mask = np.logical_or(combined_mask, seg_mask)

        # If we have no valid masks in segs_1, return original inputs
        if combined_mask is None:
            return (original_segs, segs_2)

        # Process each segment in segs_2
        for item in segs_2:
            if not isinstance(item, dict):
                continue
                
            seg_mask = item.get('mask')
            if seg_mask is None or not isinstance(seg_mask, np.ndarray):
                continue

            # Subtract the combined area of segs_1 from this segment
            remaining = np.logical_and(seg_mask, np.logical_not(combined_mask))
            
            # Only add if there's something left
            if np.sum(remaining) > 100:  # Adjust threshold as needed
                # Create new segment with updated mask but keep other metadata
                new_seg = item.copy()
                new_seg['mask'] = remaining
                remaining_segs.append(new_seg)

        logger.debug(f"Number of remaining segments: {len(remaining_segs)}")
        return (original_segs, remaining_segs)

NODE_CLASS_MAPPINGS = {
    "SegsCompare": SegsCompare
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SegsCompare": "Compare Segs"
} 