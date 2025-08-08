import google.generativeai as genai
from .base_provider import BaseProvider

SYSTEM_PROMPT = """
You are an expert security programmer. Your task is to analyze a given Python code file for security vulnerabilities and fix them.
Do not explain the vulnerability. Do not add any comments or introductory text.
Respond ONLY with the complete, corrected code for the file.
"""

class GeminiProvider(BaseProvider):
    """Provider for Google's Gemini models."""

    def __init__(self, api_key: str, model_name: str = None):
        super().__init__(api_key, model_name)
        genai.configure(api_key=self.api_key)
        
        # Use the provided model name, or a sensible default.
        self.model_name = model_name or 'gemini-1.5-flash'
        
        print(f"[Agent/Gemini]: Initializing model: {self.model_name}")
        self.model = genai.GenerativeModel(self.model_name)

    def fix_code(self, vulnerable_code: str) -> str:
        # This method remains the same
        print(f"[Agent/Gemini]: Sending code to {self.model_name} for analysis...")
        try:
            full_prompt = f"{SYSTEM_PROMPT}\n\n--- VULNERABLE CODE ---\n{vulnerable_code}"
            response = self.model.generate_content(full_prompt)
            corrected_code = response.text
            cleaned_code = corrected_code.strip().strip('`')
            if cleaned_code.startswith("python"):
                cleaned_code = cleaned_code[len("python\n"):].strip()
            return cleaned_code
        except Exception as e:
            print(f"[Agent/Gemini]: ERROR - Failed to get response from Gemini: {e}")
            return e

    @staticmethod
    def list_models(api_key: str) -> list[str]:
        """Connects to the Gemini API to discover available models."""
        print("[Harness]: Discovering available Gemini models...")
        try:
            genai.configure(api_key=api_key)
            available_models = []
            for m in genai.list_models():
                # We only want models that support content generation
                if 'generateContent' in m.supported_generation_methods:
                    # The API returns 'models/gemini-1.5-pro', we just want 'gemini-1.5-pro'
                    model_name = m.name.split('/')[-1]
                    available_models.append(model_name)
            return available_models
        except Exception as e:
            print(f"Warning: Could not fetch Gemini models. Error: {e}")
            return []