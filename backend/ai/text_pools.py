import json
import numpy as np
from backend.ai.client import ai_client

FALLBACK_POOLS = {
    "name": ["Emily Watson", "Liam Johnson", "Olivia Smith", "Noah Williams", "Sophia Brown"],
    "company": ["Apex Global Systems", "Nexus Dynamics", "OmniCorp International", "Horizon Health"],
    "product_name": ["Wireless Headphones", "Mechanical Keyboard", "4K Monitor", "Ergonomic Desk"]
}

def generate_text_pool(column_type: str, context="general", count=50, locale="en_US"):
    if ai_client.has_openai:
        prompt = f"Generate JSON array of {count} realistic '{column_type}' entries for context '{context}'. Return ONLY valid JSON array."
        resp = ai_client.generate_completion(prompt)
        if resp:
            try:
                data = json.loads(resp.strip())
                return [str(x) for x in data], "openai"
            except Exception:
                pass

    # High-quality fallback pool
    base = FALLBACK_POOLS.get(column_type, [f"{column_type.title()} {i+1}" for i in range(20)])
    rng = np.random.default_rng(42)
    selected = [str(x) for x in rng.choice(base, size=min(count, len(base)), replace=False)]
    return selected, "fallback"