"""
OpenAI <-> Anthropic request/response translator — Person A (YOU).

Translates incoming OpenAI-format requests to Anthropic's API format,
and translates Anthropic responses back to OpenAI-compatible format.

See: Task 3 in PERSON_A_TASKS.md
"""


# Model alias mapping — agree with team before locking in
MODEL_MAP: dict[str, str] = {
    "gpt-4o": "claude-sonnet-4-6",
    "gpt-4o-mini": "claude-haiku-4",
    # Add more mappings as agreed with the team
}


def translate_request_to_anthropic(openai_payload: dict) -> dict:
    """
    Translate an OpenAI-format chat completion request to Anthropic's format.

    TODO (Task 3):
    - Extract system messages -> top-level 'system' field
    - Map model name via MODEL_MAP
    - Default max_tokens to 4096 if not set (decision #1)
    - Pass stream field through directly
    """
    raise NotImplementedError("Task 3 — implement OpenAI -> Anthropic request translation")


def translate_response_from_anthropic(anthropic_response: dict) -> dict:
    """
    Translate an Anthropic response back to OpenAI's chat.completion format.

    TODO (Task 3):
    - Map content[0].text -> choices[0].message.content
    - Map usage.input_tokens -> usage.prompt_tokens
    - Map usage.output_tokens -> usage.completion_tokens
    - Map stop_reason -> finish_reason
    - Handle error responses too
    """
    raise NotImplementedError("Task 3 — implement Anthropic -> OpenAI response translation")
