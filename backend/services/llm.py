import httpx
from config import LLM_API_KEY, LLM_MODEL, LLM_BASE_URL


async def generate_text(prompt: str, system_prompt: str = "") -> str:
    """Send a prompt to the LLM and return the response text."""
    if not LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY not configured")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": messages,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"]


async def generate_with_tools(messages: list, tools: list | None = None) -> dict:
    """Call LLM with messages and optional tool definitions.

    Returns the raw message object from the LLM response, which may contain
    either 'content' (text) or 'tool_calls' (list of tool invocations).
    """
    if not LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY not configured")

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
    }
    if tools:
        payload["tools"] = tools

    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]
