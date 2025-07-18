import re
from typing import List
import logging
import os
from .utils import civitai_embedding_key_name, civitai_lora_key_name, full_embedding_path_for, full_lora_path_for, get_sha256

logger = logging.getLogger(__name__)

class PromptMetadataExtractor:
    EMBEDDING = r'embedding:([^,\s\(\)\:]+)'
    LORA = r'<lora:([^>:]+)(?::[^>]+)?>'

    def __init__(self, prompts: List[str]):
        self.__embeddings = {}
        self.__loras = {}
        self.__perform(prompts)

    def get_embeddings(self):
        return self.__embeddings
        
    def get_loras(self):
        return self.__loras

    def __perform(self, prompts):
        for prompt in prompts:
            logger.debug(f"Processing prompt: {prompt}")
            embeddings = re.findall(self.EMBEDDING, prompt, re.IGNORECASE | re.MULTILINE)
            for embedding in embeddings:
                self.__extract_embedding_information(embedding)
            
            loras = re.findall(self.LORA, prompt, re.IGNORECASE | re.MULTILINE)
            for lora in loras:
                self.__extract_lora_information(lora)

    def __extract_embedding_information(self, embedding: str):
        logger.debug(f"Extracting embedding information for: {embedding}")
        embedding_name = civitai_embedding_key_name(embedding)
        embedding_path = full_embedding_path_for(embedding)
        if embedding_path is None:
            logger.warning(f"Embedding path not found for: {embedding}")
            return
        sha = self.__get_shortened_sha(embedding_path)
        self.__embeddings[embedding_name] = sha
        logger.debug(f"Added embedding: {embedding_name} with hash: {sha}")

    def __extract_lora_information(self, lora: str):
        logger.debug(f"Extracting LoRA information for: {lora}")
        lora_name = civitai_lora_key_name(lora)
        
        # The lora name already includes the extension, so we don't need to add it
        lora_path = full_lora_path_for(lora)
        
        if lora_path is None:
            logger.warning(f"LoRA path not found for: {lora}")
            return
        
        sha = self.__get_shortened_sha(lora_path)
        self.__loras[lora_name] = sha
        logger.debug(f"Added LoRA: {lora_name} with hash: {sha}")
    
    def __get_shortened_sha(self, file_path: str):
       return get_sha256(file_path)[:10]
