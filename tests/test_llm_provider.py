import pytest
from src.services.llm_provider import OllamaProvider

def test_ollama_provider_init():
    provider = OllamaProvider()
    assert provider.model == 'gemma3:4b'

def test_ollama_provider_init_custom_model():
    provider = OllamaProvider(model='llama3:8b')
    assert provider.model == 'llama3:8b'
