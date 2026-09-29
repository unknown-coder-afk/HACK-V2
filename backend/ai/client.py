# AI client stub — pluggable AI backend
# Set OPENAI_API_KEY env variable to enable AI-assisted text generation

import os

class _AIClient:
    def __init__(self):
        self._openai = None
        self.has_openai = False
        try:
            import openai
            key = os.getenv("OPENAI_API_KEY")
            if key:
                self._openai = openai.OpenAI(api_key=key)
                self.has_openai = True
        except ImportError:
            pass

    def generate_completion(self, prompt: str) -> str | None:
        if not self.has_openai or self._openai is None:
            return None
        try:
            resp = self._openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=800,
            )
            return resp.choices[0].message.content
        except Exception:
            return None

ai_client = _AIClient()
