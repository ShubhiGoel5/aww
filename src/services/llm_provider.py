"""
LLM Provider Service (Groq — Free Cloud LLM API)
Uses Groq's OpenAI-compatible endpoint to run Llama/Mixtral models for free.
"""
import os
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator

logger = logging.getLogger(__name__)

class GroqProvider:
    """Groq cloud LLM provider using OpenAI-compatible endpoint."""
    
    def __init__(self, base_url: str = None, model: str = None, api_key: str = None):
        from openai import OpenAI
        self.base_url = base_url or os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required. Get a free key at https://console.groq.com")
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
    
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
        
        # Convert Anthropic-style tools to OpenAI function format
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
            logger.error(f"Error calling Groq: {e}")
            raise

    async def chat_stream(self, messages, system="", max_tokens=4096, tools=None):
        # Streaming can be complex with tool use, just wrap chat for now
        result = await self.chat(messages, system, max_tokens, tools)
        yield result


# Keep backward compatibility alias
OllamaProvider = GroqProvider


class LLMProviderManager:
    """Manages LLM provider connections."""
    
    def __init__(self, db_connection=None):
        self.db = db_connection
    
    def get_company_provider(self, company_id: str) -> GroqProvider:
        """Always returns Groq provider."""
        return GroqProvider()
    
    @staticmethod
    def list_providers():
        """List available providers."""
        return PROVIDERS

PROVIDERS = {
    "groq": {
        "name": "Groq Cloud LLM (Free)",
        "default_model": "llama-3.3-70b-versatile",
        "auth_method": "api_key",
        "models": [
            {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile", "context": 131072},
            {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant", "context": 131072},
            {"id": "gemma2-9b-it", "name": "Gemma 2 9B IT", "context": 8192},
            {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "context": 32768},
        ]
    }
}


async def call_llm_simple(system_prompt: str, user_message: str, max_tokens: int = 4096) -> dict:
    """
    Simple helper to call the LLM without tool use.
    Returns {"content": str, "input_tokens": int, "output_tokens": int, "model": str}
    Used by routes (contracts, documents, templates) that need a quick LLM call.
    """
    provider = GroqProvider()
    
    messages = [{"role": "user", "content": user_message}]
    
    try:
        result = await provider.chat(
            system=system_prompt,
            messages=messages,
            max_tokens=max_tokens
        )
        text = result["content"][0]["text"] if result.get("content") else ""
        usage = result.get("usage", {})
        return {
            "content": text,
            "input_tokens": usage.get("input", 0),
            "output_tokens": usage.get("output", 0),
            "model": result.get("model", provider.model)
        }
    except Exception as e:
        logger.error(f"LLM call error: {e}")
        raise
