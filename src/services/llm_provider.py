"""
LLM Provider Service (Ollama Exclusive)
"""
import os
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator

logger = logging.getLogger(__name__)

class OllamaProvider:
    """Ollama local LLM provider using OpenAI-compatible endpoint."""
    
    def __init__(self, base_url: str = None, model: str = None):
        from openai import OpenAI
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self.model = model or os.getenv("OLLAMA_MODEL", "gemma3:4b")
        
        # Ollama's OpenAI API compatibility layer doesn't need an API key
        self.client = OpenAI(api_key="ollama", base_url=self.base_url)
    
    async def chat(self, messages, system="", max_tokens=4096, tools=None):
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        
        for msg in messages:
            if isinstance(msg.get("content"), list):
                # Handle tool_result and multi-content
                text_parts = []
                for block in msg["content"]:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block["text"])
                        elif block.get("type") == "tool_result":
                            text_parts.append(str(block.get("content", "")))
                    else:
                        text_parts.append(str(block))
                msgs.append({"role": msg["role"], "content": "\n".join(text_parts)})
            else:
                msgs.append(msg)
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": msgs,
        }
        
        # Convert Anthropic tools to OpenAI function format
        if tools:
            openai_tools = []
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {})
                    }
                })
            kwargs["tools"] = openai_tools
        
        try:
            response = self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            
            # Convert OpenAI response to Anthropic-like format expected by agents
            content = []
            if choice.message.content:
                content.append({"type": "text", "text": choice.message.content})
            
            # Handle tool calls
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.function.name,
                        "input": json.loads(tc.function.arguments)
                    })
            
            stop_reason = "end_turn"
            if choice.finish_reason == "tool_calls":
                stop_reason = "tool_use"
            
            return {
                "content": content,
                "model": response.model,
                "usage": {"input": getattr(response.usage, 'prompt_tokens', 0), "output": getattr(response.usage, 'completion_tokens', 0)},
                "stop_reason": stop_reason,
            }
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            raise

    async def chat_stream(self, messages, system="", max_tokens=4096, tools=None):
        # Streaming can be complex with tool use, just wrap chat for now
        result = await self.chat(messages, system, max_tokens, tools)
        yield result

class LLMProviderManager:
    """Manages LLM provider connections."""
    
    def __init__(self, db_connection=None):
        self.db = db_connection
    
    def get_company_provider(self, company_id: str) -> OllamaProvider:
        """Always returns Ollama provider."""
        return OllamaProvider()

PROVIDERS = {
    "ollama": {
        "name": "Ollama Local LLM",
        "default_model": "gemma3:4b",
        "auth_method": "env_var"
    }
}
