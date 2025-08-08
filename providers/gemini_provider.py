import google.generativeai as genai
from .base_provider import BaseProvider

# This is the core instruction set for the AI model.
SYSTEM_PROMPT = """
You are an expert security programmer. Your task is to analyze a given Python code file for security vulnerabilities and fix them.
Do not explain the vulnerability. Do not add any comments or introductory text.
Respond ONLY with the complete, corrected code for the file.
"""

class GeminiProvider(BaseProvider):
    """Provider for Google's Gemini models."""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash') # Or another Gemini model

    def fix_code(self, vulnerable_code: str) -> str:
        print("[Agent/Gemini]: Sending code to Gemini for analysis...")
        try:
            # Gemini uses a specific format for system prompts + user input
            full_prompt = f"{SYSTEM_PROMPT}\n\n--- VULNERABLE CODE ---\n{vulnerable_code}"
            
            response = self.model.generate_content(full_prompt)
            
            # The response text contains the code
            corrected_code = response.text

            # Clean up markdown formatting, which models often add
            if corrected_code.startswith("```python"):
                corrected_code = corrected_code[len("```python\n"):-len("```")]
            
            return corrected_code

        except Exception as e:
            print(f"[Agent/Gemini]: ERROR - Failed to get response from Gemini: {e}")
            # Return original code on failure to avoid breaking the file
            return vulnerable_code