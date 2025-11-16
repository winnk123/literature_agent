"""
OpenAI Model Adapter for InternAgent

Implements the BaseModel interface for OpenAI models.
"""

import base64
import json
import logging
import mimetypes
import os
from typing import Dict, List, Optional, Any, Union
from json_repair import repair_json

import openai
from openai import AsyncOpenAI

from .base_model import BaseModel

logger = logging.getLogger(__name__)


class OpenAIModel(BaseModel):
    """OpenAI implementation of the BaseModel interface."""
    
    def __init__(self, 
                api_key: Optional[str] = None, 
                model_name: str = "gpt-4o", 
                max_tokens: int = 4096,
                temperature: float = 0.7,
                timeout: int = 100):
        """
        Initialize the OpenAI model adapter.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
            model_name: Model identifier to use (e.g., "gpt-4o")
            max_tokens: Maximum tokens to generate by default
            temperature: Default temperature setting (0 to 1)
            timeout: Timeout in seconds for API calls
        """
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        self.base_url = os.environ.get("OPENAI_API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        if not self.api_key:
            logger.warning("OpenAI API key not provided. Please set OPENAI_API_KEY environment variable.")
            
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        
        try:

            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
            logger.info(f"OpenAI client initialized with model: {self.model_name} via {self.base_url}")
        except TypeError as e:
            logger.warning(f"Error initializing OpenAI client: {e}")
            self.client = None
    
    async def generate(self, 
                      prompt: str, 
                      system_prompt: Optional[str] = None,
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      stop_sequences: Optional[List[str]] = None,
                      **kwargs) -> str:
        """
        Generate text based on the provided prompt using OpenAI API.
        
        Args:
            prompt: The user prompt to send to the model
            system_prompt: Optional system prompt to guide the model
            temperature: Controls randomness (0 to 1)
            max_tokens: Maximum number of tokens to generate
            stop_sequences: List of sequences at which to stop generation
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated text response from the model
        """

        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})

        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop_sequences,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {e}")
            raise
    
    async def generate_with_json_output(self, 
                                       prompt: str, 
                                       json_schema: Dict[str, Any],
                                       system_prompt: Optional[str] = None,
                                       temperature: Optional[float] = None,
                                       **kwargs) -> Dict[str, Any]:
        """
        Generate a response formatted as JSON according to the provided schema.
        
        Args:
            prompt: The user prompt to send to the model
            json_schema: JSON schema defining the expected response structure
            system_prompt: Optional system prompt to guide the model
            temperature: Controls randomness (0 to 1)
            **kwargs: Additional model-specific parameters
            
        Returns:
            JSON response matching the provided schema
        """

        if system_prompt:
            enhanced_system_prompt = f"{system_prompt}\n\nRespond with JSON that matches this schema: {json.dumps(json_schema)}"
        else:
            enhanced_system_prompt = f"Respond with JSON that matches this schema: {json.dumps(json_schema)}"

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": enhanced_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature if temperature is not None else self.temperature,
                response_format={"type": "json_object"},
                **kwargs
            )
            
            result_text = response.choices[0].message.content
            
            # 首先尝试清理和提取JSON
            cleaned_text = result_text.strip()
            
            # 尝试从markdown代码块中提取JSON（支持多行）
            import re
            # 匹配 ```json ... ``` 或 ``` ... ``` 中的JSON
            json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```', cleaned_text, re.MULTILINE)
            if json_match:
                cleaned_text = json_match.group(1).strip()
            
            # 如果还是找不到，尝试找到第一个 { 或 [（支持多行JSON）
            if not cleaned_text.startswith('{') and not cleaned_text.startswith('['):
                start_idx = cleaned_text.find('{')
                if start_idx == -1:
                    start_idx = cleaned_text.find('[')
                if start_idx >= 0:
                    # 找到匹配的结束位置（支持嵌套）
                    brace_count = 0
                    bracket_count = 0
                    in_string = False
                    escape_next = False
                    end_idx = start_idx
                    
                    for i in range(start_idx, len(cleaned_text)):
                        char = cleaned_text[i]
                        
                        if escape_next:
                            escape_next = False
                            continue
                        
                        if char == '\\':
                            escape_next = True
                            continue
                        
                        if char == '"' and not escape_next:
                            in_string = not in_string
                            continue
                        
                        if not in_string:
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                            elif char == '[':
                                bracket_count += 1
                            elif char == ']':
                                bracket_count -= 1
                            
                            if brace_count == 0 and bracket_count == 0:
                                end_idx = i + 1
                                break
                    
                    if end_idx > start_idx:
                        cleaned_text = cleaned_text[start_idx:end_idx].strip()
            
            try:
                result_dict = json.loads(cleaned_text)
                return result_dict
            except json.JSONDecodeError:
                # 如果清理后的文本仍然失败，尝试原始文本
                try:
                    result_dict = json.loads(result_text)
                    return result_dict
                except json.JSONDecodeError:
                    logger.error(f"Model returned invalid JSON: {result_text[:500]}...")
                    repaired_text = repair_json(result_text) if repair_json else None
                    if repaired_text:
                        try:
                            return json.loads(repaired_text)
                        except json.JSONDecodeError:
                            logger.error(f"Repaired JSON still invalid: {repaired_text[:500]}...")
                    # 在异常消息中包含原始响应文本，以便上层代码可以尝试提取
                    raise ValueError(f"Model did not return valid JSON: {result_text}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            raise ValueError(f"Model did not return valid JSON: {e}")
        except Exception as e:
            logger.error(f"Error generating JSON response from OpenAI: {e}")
            raise
    
    async def generate_json(self, 
                          prompt: str, 
                          schema: Dict[str, Any],
                          system_prompt: Optional[str] = None,
                          temperature: Optional[float] = None,
                          default: Optional[Dict[str, Any]] = None,
                          **kwargs) -> Dict[str, Any]:
        """
        Generate JSON output from the model.
        
        Args:
            prompt: User prompt to generate from
            schema: JSON schema that the output should conform to
            system_prompt: System prompt (instructions for the model)
            temperature: Sampling temperature (0.0 to 1.0)
            default: Default JSON to return if generation fails
            **kwargs: Additional model-specific parameters
            
        Returns:
            JSON output as a Python dictionary
            
        Raises:
            ModelError: If generation fails and no default is provided
        """
        try:
            return await self.generate_with_json_output(
                prompt=prompt,
                json_schema=schema,
                system_prompt=system_prompt,
                temperature=temperature,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Error in generate_json: {e}")
            if default is not None:
                logger.warning(f"Returning default JSON due to error: {e}")
                return default
            raise

    def _image_to_payload(self, image_reference: str) -> Dict[str, Any]:
        """Prepare image payload for responses API."""
        if image_reference.startswith("http://") or image_reference.startswith("https://"):
            return {
                "type": "input_image",
                "image_url": {"url": image_reference}
            }

        if not os.path.exists(image_reference):
            raise FileNotFoundError(f"Image not found: {image_reference}")

        with open(image_reference, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        return {
            "type": "input_image",
            "image_base64": encoded
        }

    async def generate_multimodal_json(self,
                                   prompt: str,
                                   schema: Dict[str, Any],
                                   images: Optional[List[str]] = None,
                                   system_prompt: Optional[str] = None,
                                   temperature: Optional[float] = None,
                                   **kwargs) -> Dict[str, Any]:
  
        messages: List[Dict[str, Any]] = []
     
        if system_prompt:
          messages.append({"role": "system", "content": system_prompt})
    
        # Build user content with text and images
        user_content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    
        for image_ref in images or []:
          try:
             if image_ref.startswith("http://") or image_ref.startswith("https://"):
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": image_ref}
                })
             else:
                # Local file: convert to base64 data URL
                if not os.path.exists(image_ref):
                    raise FileNotFoundError(f"Image not found: {image_ref}")
                
                mime_type, _ = mimetypes.guess_type(image_ref)
                if not mime_type:
                    mime_type = "image/png"
                
                with open(image_ref, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                
                data_url = f"data:{mime_type};base64,{encoded}"
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": data_url}
                })
          except Exception as exc:
            logger.error(f"Failed to process image '{image_ref}': {exc}")
            raise
    
        messages.append({"role": "user", "content": user_content})
    
    # Add schema instruction to system prompt
        schema_instruction = json.dumps(schema, indent=2)
        enhanced_system = system_prompt or ""
        if enhanced_system:
          enhanced_system += "\n\n"
        enhanced_system += (
        f"Return a JSON object that strictly follows this schema:\n{schema_instruction}\n"
        "Output only valid JSON, no additional text."
        )
        if messages and messages[0].get("role") == "system":
          messages[0]["content"] = enhanced_system
        else:
          messages.insert(0, {"role": "system", "content": enhanced_system})
    
        try:
            response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            response_format={"type": "json_object"},
            **kwargs
            )
        
            result_text = response.choices[0].message.content
            try:
              return json.loads(result_text)
            except json.JSONDecodeError:
              logger.error(f"Model returned invalid JSON for multimodal request: {result_text}")
              repaired = repair_json(result_text)
              if repaired:
                return json.loads(repaired)
              raise ValueError("Model did not return valid JSON for multimodal request")
    
        except json.JSONDecodeError as e:
           logger.error(f"Failed to decode JSON response: {e}")
           raise ValueError(f"Model did not return valid JSON: {e}")
        except Exception as e:
           logger.error(f"Error generating multimodal JSON response from OpenAI: {e}")
           raise
    
    async def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for the given text(s).
        
        Args:
            text: Text string or list of strings to embed
            
        Returns:
            Embedding vector or list of embedding vectors
        """
        try:
            text_list = [text] if isinstance(text, str) else text
            
            response = await self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text_list
            )
            
            embeddings = [item.embedding for item in response.data]
            
            return embeddings[0] if isinstance(text, str) else embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'OpenAIModel':
        """
        Create an OpenAI model instance from a configuration dictionary.

        This factory method enables consistent model instantiation across the system
        based on configuration settings.
        
        Args:
            config: Configuration dictionary with model settings
            
        Returns:
            Configured OpenAIModel instance
        """
        return cls(
            api_key=config.get("api_key"),
            model_name=config.get("model_name", "gpt-4o"),
            max_tokens=config.get("max_tokens", 10000),
            temperature=config.get("temperature", 0.6),
            timeout=config.get("timeout", 300)
        ) 
