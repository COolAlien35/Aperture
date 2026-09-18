from typing import Dict, Tuple

# Pricing per 1000 tokens (Example arbitrary values, update with real provider pricing)
# Format: model_name: (input_price_per_1k, output_price_per_1k)
MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-4": (0.03, 0.06),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    "claude-3-opus-20240229": (0.015, 0.075),
    "claude-3-sonnet-20240229": (0.003, 0.015),
    "claude-3-haiku-20240307": (0.00025, 0.00125),
}

FALLBACK_MAX_TOKENS = 4096
DEFAULT_PRICING = (0.01, 0.03)  # Safe default if model is missing

def estimate_cost(model: str, prompt_tokens: int, requested_max_tokens: int = None) -> float:
    """
    Estimates the maximum possible cost of a request based on prompt tokens and max_tokens.
    Formula: (prompt_tokens * input_price) + (max_tokens * output_price)
    """
    input_price_1k, output_price_1k = MODEL_PRICING.get(model, DEFAULT_PRICING)
    
    # Calculate input cost
    input_cost = (prompt_tokens / 1000.0) * input_price_1k
    
    # If max_tokens isn't specified in the request, assume the 4096 fallback default
    max_tokens = requested_max_tokens if requested_max_tokens is not None else FALLBACK_MAX_TOKENS
    
    # Calculate max possible output cost
    output_cost = (max_tokens / 1000.0) * output_price_1k
    
    return input_cost + output_cost

def calculate_actual_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculates the exact actual cost of a completed request.
    """
    input_price_1k, output_price_1k = MODEL_PRICING.get(model, DEFAULT_PRICING)
    
    input_cost = (prompt_tokens / 1000.0) * input_price_1k
    output_cost = (completion_tokens / 1000.0) * output_price_1k
    
    return input_cost + output_cost
