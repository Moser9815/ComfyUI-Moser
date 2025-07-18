import os
import hashlib
import folder_paths
from datetime import datetime

def get_sha256(filename):
    hash_sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def civitai_embedding_key_name(embedding):
    return f"embed:{embedding}"

def civitai_lora_key_name(lora):
    return f"LORA:{lora}"

def full_embedding_path_for(embedding):
    embedding_path = folder_paths.get_full_path("embeddings", embedding)
    if embedding_path is None:
        print(f"Embedding {embedding} not found")
    return embedding_path

def full_lora_path_for(lora):
    lora_folders = folder_paths.get_folder_paths("loras")
    for folder in lora_folders:
        for root, dirs, files in os.walk(folder):
            if lora in files:
                return os.path.join(root, lora)
    print(f"LoRA {lora} not found")
    return None

def get_current_datetime():
    return datetime.now().isoformat()
