"""LLM Client - Gemini API with fallback support"""

import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


class LLMClient:
    """Gemini LLM client with model rotation and fallback."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.models = os.getenv("LLM_MODELS", "gemini-2.5-flash").split(",")
        self.current_model_idx = 0
        
        genai.configure(api_key=self.api_key)
        self._configure_safety()
    
    def _configure_safety(self):
        """Configure safety settings for financial content."""
        self.safety_settings = {
            genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    
    def _get_model(self, model_name: Optional[str] = None) -> genai.GenerativeModel:
        """Get Gemini model instance."""
        name = model_name or self.models[self.current_model_idx]
        return genai.GenerativeModel(name)
    
    def _rotate_model(self) -> str:
        """Rotate to next model on failure."""
        if self.current_model_idx < len(self.models) - 1:
            self.current_model_idx += 1
        else:
            self.current_model_idx = 0
        return self.models[self.current_model_idx]
    
    def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048
    ) -> str:
        """Generate response from Gemini."""
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        for attempt in range(len(self.models)):
            try:
                model_instance = self._get_model(model)
                response = model_instance.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ),
                    safety_settings=self.safety_settings
                )
                return response.text
            except Exception as e:
                print(f"Model {self.models[self.current_model_idx]} failed: {e}")
                self._rotate_model()
        
        raise Exception("All Gemini models failed")
    
    def extract_structured(
        self,
        text: str,
        schema: Dict[str, str],
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """Extract structured data from text using LLM."""
        schema_desc = "\n".join([f"- {k}: {v}" for k, v in schema.items()])
        
        prompt = f"""Extract the following fields from the text below.
Return ONLY a valid JSON object with these keys.
If a field is not found, use null.

Fields to extract:
{schema_desc}

Text:
{text}

JSON:"""
        
        response = self.generate(prompt, temperature=temperature)
        
        # Parse JSON from response
        import json
        try:
            # Try to extract JSON from response
            json_str = response.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: return raw response
            return {"raw_response": response}
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """Multi-turn chat with Gemini."""
        model_instance = self._get_model(model)
        chat = model_instance.start_chat(history=[])
        
        # Add history (skip last message which is the new one)
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            chat.history.append(genai.types.Content(
                role=role,
                parts=[genai.types.Part.from_text(msg["content"])]
            ))
        
        # Generate response for last message
        response = chat.send_message(
            messages[-1]["content"],
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
            ),
            safety_settings=self.safety_settings
        )
        return response.text
    
    def health_check(self) -> bool:
        """Check if Gemini API is accessible."""
        try:
            self.generate("Say 'OK'", max_tokens=10)
            return True
        except Exception:
            return False
