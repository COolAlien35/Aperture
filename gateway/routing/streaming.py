"""
SSE streaming passthrough — Person A (YOU).

Handles streaming responses from Anthropic's API, translating
each SSE chunk to OpenAI's streaming format in real-time.

Tracks running token count for partial-disconnect reconciliation
(design decision #6).

See: Task 4 in PERSON_A_TASKS.md
"""


async def stream_anthropic_response(request, anthropic_payload: dict):
    """
    Open a streaming connection to Anthropic, translate chunks to
    OpenAI SSE format, and yield them to the client.

    TODO (Task 4):
    - Use httpx.AsyncClient for streaming POST to Anthropic
    - Translate each chunk: message_start, content_block_delta, message_stop
    - Track request.state.tokens_streamed_so_far
    - Handle 3 termination cases: clean, client disconnect, provider error
    - Fire reconciliation hook (agree interface with Person B first)
    - Call publish_usage_event() fire-and-forget after reconciliation
    """
    raise NotImplementedError("Task 4 — implement SSE streaming passthrough")
