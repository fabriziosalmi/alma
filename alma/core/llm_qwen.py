"""Qwen3 LLM implementation for infrastructure orchestration."""

import json
import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path
import torch

from alma.core.llm import LLMInterface
from alma.core.config import get_settings

settings = get_settings()


class Qwen3LLM(LLMInterface):
    """
    Qwen3 0.6B LLM implementation.

    Uses transformers library to load and run Qwen3 model
    for infrastructure-related tasks.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
        device: Optional[str] = None,
        max_tokens: int = 512,
    ) -> None:
        """
        Initialize Qwen3 LLM.

        Args:
            model_name: HuggingFace model name
            device: Device to run on (cpu, cuda, mps)
            max_tokens: Maximum tokens to generate
        """
        self.model_name = model_name
        self.max_tokens = max_tokens

        # Determine device
        if device:
            self.device = device
        elif torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        self.model = None
        self.tokenizer = None
        self._initialized = False

    async def _initialize(self) -> None:
        """Initialize model and tokenizer lazily."""
        if self._initialized:
            return

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # Run initialization in thread pool to avoid blocking
            loop = asyncio.get_event_loop()

            def _load_model():
                tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    trust_remote_code=True,
                )
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                    device_map=self.device if self.device != "cpu" else None,
                    trust_remote_code=True,
                )
                if self.device == "cpu":
                    model = model.to(self.device)

                return tokenizer, model

            self.tokenizer, self.model = await loop.run_in_executor(None, _load_model)
            self._initialized = True

            print(f"✓ Loaded {self.model_name} on {self.device}")

        except ImportError:
            raise ImportError(
                "transformers and torch are required for Qwen3LLM. "
                "Install with: pip install transformers torch"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Qwen3 model: {e}")

    async def stream_generate(self, prompt: str, context: Optional[Dict[str, Any]] = None):
        """
        Stream text generation from prompt.

        Args:
            prompt: Input prompt
            context: Optional context information

        Yields:
            Text chunks as they are generated
        """
        await self._initialize()

        # Build messages
        system_prompt = self._get_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        loop = asyncio.get_event_loop()

        def _stream():
            # Tokenize input
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

            # Generate with streaming
            from transformers import TextIteratorStreamer
            from threading import Thread

            streamer = TextIteratorStreamer(
                self.tokenizer, skip_prompt=True, skip_special_tokens=True
            )

            generation_kwargs = dict(
                inputs,
                streamer=streamer,
                max_new_tokens=self.max_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
            )

            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()

            for text_chunk in streamer:
                yield text_chunk

            thread.join()

        # Stream chunks
        for chunk in await loop.run_in_executor(None, lambda: list(_stream())):
            yield chunk

    async def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text from prompt.

        Args:
            prompt: Input prompt
            context: Optional context information

        Returns:
            Generated text
        """
        await self._initialize()

        # Build messages for chat format
        messages = []

        # Add system message
        messages.append(
            {
                "role": "system",
                "content": self._get_system_prompt(),
            }
        )

        # Add context if provided
        if context:
            context_str = json.dumps(context, indent=2)
            messages.append(
                {
                    "role": "system",
                    "content": f"Context:\n{context_str}",
                }
            )

        # Add user prompt
        messages.append({"role": "user", "content": prompt})

        # Generate in thread pool
        loop = asyncio.get_event_loop()

        def _generate():
            # Apply chat template
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                return_attention_mask=True,
            ).to(self.device)

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_tokens,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            # Decode
            generated_text = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1] :],
                skip_special_tokens=True,
            )

            return generated_text.strip()

        return await loop.run_in_executor(None, _generate)

    async def function_call(self, prompt: str, functions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate function call from prompt.

        Args:
            prompt: Input prompt
            functions: Available functions

        Returns:
            Function call result with function name and arguments
        """
        await self._initialize()

        # Build function calling prompt
        function_descriptions = self._format_functions(functions)

        full_prompt = f"""You are an AI assistant that helps with infrastructure management.

Available functions:
{function_descriptions}

User request: {prompt}

Respond with a JSON object containing:
- "function": the name of the function to call
- "arguments": a dictionary of arguments for the function

Only respond with valid JSON, nothing else."""

        response = await self.generate(full_prompt)

        # Parse JSON response
        try:
            # Try to extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                return result
            else:
                # Fallback: return first function if no JSON found
                if functions:
                    return {
                        "function": functions[0]["name"],
                        "arguments": {},
                    }
                return {}

        except json.JSONDecodeError:
            # Fallback to simple parsing
            for func in functions:
                if func["name"].lower() in response.lower():
                    return {
                        "function": func["name"],
                        "arguments": {},
                    }
            return {}

    def _get_system_prompt(self) -> str:
        """
        Get system prompt for infrastructure tasks.

        Returns:
            System prompt text
        """
        return """You are an expert AI assistant specialized in infrastructure management and cloud orchestration.

Your role:
- Help users design, deploy, and manage infrastructure
- Convert natural language descriptions to infrastructure blueprints
- Suggest improvements and best practices
- Explain infrastructure concepts clearly
- Follow security and reliability best practices

Guidelines:
- Be concise and technical
- Use YAML format for infrastructure blueprints
- Consider scalability, security, and cost
- Suggest redundancy and high availability when appropriate
- Explain trade-offs clearly"""

    def _format_functions(self, functions: List[Dict[str, Any]]) -> str:
        """
        Format function definitions for prompt.

        Args:
            functions: List of function definitions

        Returns:
            Formatted function descriptions
        """
        formatted = []
        for func in functions:
            name = func.get("name", "unknown")
            description = func.get("description", "No description")
            params = func.get("parameters", {})

            param_str = json.dumps(params, indent=2) if params else "{}"
            formatted.append(f"- {name}: {description}\n  Parameters: {param_str}")

        return "\n".join(formatted)

    async def close(self) -> None:
        """Clean up resources."""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        self._initialized = False

        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# Singleton instance
_qwen_instance: Optional[Qwen3LLM] = None


async def get_qwen_llm() -> Qwen3LLM:
    """
    Get singleton Qwen3 LLM instance.

    Returns:
        Qwen3LLM instance
    """
    global _qwen_instance

    if _qwen_instance is None:
        _qwen_instance = Qwen3LLM(
            model_name=settings.llm_model_name,
            device=settings.llm_device,
            max_tokens=settings.llm_max_tokens,
        )
        await _qwen_instance._initialize()

    return _qwen_instance
