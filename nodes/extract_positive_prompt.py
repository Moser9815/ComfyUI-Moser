import json

class ExtractPositivePrompt:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "metadata_string": ("STRING", {"multiline": True}),
                "output_label": ("STRING", {"default": "Extracted Positive Prompt"})
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("extracted_prompt", "label")
    FUNCTION = "extract"
    CATEGORY = "utils"

    def extract(self, metadata_string, output_label):
        try:
            metadata = json.loads(metadata_string)
            prompt = metadata.get('prompt', {})
            
            debug_info = []
            debug_info.append(f"Number of nodes: {len(prompt)}")
            
            # Find the StringFunction|pysssss node with the title "Pony Positive"
            for node_id, node_data in prompt.items():
                class_type = node_data.get('class_type', '')
                title = node_data.get('title', '')
                debug_info.append(f"Node {node_id}: class_type={class_type}, title={title}")
                
                if class_type == 'StringFunction|pysssss' and title == 'Pony Positive':
                    result = node_data.get('inputs', {}).get('result', '')
                    if result:
                        return result, output_label
                    else:
                        debug_info.append("Found Pony Positive node, but result is empty")
            
            # If not found, search for any StringFunction|pysssss node
            for node_id, node_data in prompt.items():
                if node_data.get('class_type') == 'StringFunction|pysssss':
                    result = node_data.get('inputs', {}).get('result', '')
                    if result:
                        return result, output_label
                    else:
                        debug_info.append(f"Found StringFunction node {node_id}, but result is empty")
            
            # If still not found, return debug information
            return "Debug Info:\n" + "\n".join(debug_info), output_label
        except json.JSONDecodeError:
            return "Invalid JSON in metadata string", output_label
        except Exception as e:
            return f"Error processing metadata: {str(e)}", output_label

NODE_CLASS_MAPPINGS = {
    "ExtractPositivePrompt": ExtractPositivePrompt
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExtractPositivePrompt": "Extract Positive Prompt"
}
