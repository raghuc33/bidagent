"""Agent loop engine — orchestrates LLM + tool calls for iterative bid refinement."""

import json
from services.llm import generate_with_tools
from services.agent_tools import TOOL_DEFINITIONS, execute_tool

MAX_ITERATIONS = 10

SYSTEM_PROMPT_TEMPLATE = """You are BidAgent, an expert AI bid writer for UK Public Sector tenders.

You are currently helping the user refine their response to:
Section: {section_title}
Description: {section_description}
Word Limit: {word_limit} words

{draft_context}

You have tools available to help. Use them when appropriate:
- search_knowledge_base: Find evidence from uploaded documents
- generate_draft: Create a new draft using RAG context
- squeeze_word_count: Compress text to fit word limits
- score_against_rubric: Evaluate quality against scoring criteria
- analyze_evidence_gaps: Find what evidence is missing
- restyle_tone: Adjust writing tone for UK public sector

When the user asks you to modify the draft, use the appropriate tool and return the updated text.
When citing evidence, reference source documents and page numbers.
Keep your explanations brief and focused on bid quality.
Always tell the user what you did and why."""


def build_system_prompt(section_title: str, section_description: str = "",
                        current_draft: str = "", word_limit: int = 250) -> str:
    draft_context = ""
    if current_draft:
        wc = len(current_draft.split())
        draft_context = f"The current draft ({wc} words):\n---\n{current_draft}\n---"

    return SYSTEM_PROMPT_TEMPLATE.format(
        section_title=section_title,
        section_description=section_description or "Not specified",
        word_limit=word_limit,
        draft_context=draft_context,
    )


async def run_agent_turn(
    conversation_history: list,
    section_title: str,
    section_description: str = "",
    current_draft: str = "",
    word_limit: int = 250,
) -> dict:
    """Run one agent turn: send messages to LLM, execute any tool calls, return final response.

    Returns:
        {
            "text": str,           # The assistant's text response
            "updated_draft": str | None,  # If the agent produced a new draft
            "tool_calls": [        # Tools the agent invoked
                {"tool": str, "arguments": dict, "result": dict, "summary": str}
            ]
        }
    """
    system_prompt = build_system_prompt(section_title, section_description, current_draft, word_limit)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)

    tool_call_log = []

    for _ in range(MAX_ITERATIONS):
        response_msg = await generate_with_tools(messages, TOOL_DEFINITIONS)

        # If the LLM returns tool calls, execute them and loop
        tool_calls = response_msg.get("tool_calls")
        if tool_calls:
            # Append the assistant message with tool calls
            messages.append(response_msg)

            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                try:
                    fn_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    fn_args = {}

                result_str = await execute_tool(fn_name, fn_args)

                # Log for frontend
                try:
                    result_parsed = json.loads(result_str)
                except json.JSONDecodeError:
                    result_parsed = {"raw": result_str}

                tool_call_log.append({
                    "tool": fn_name,
                    "arguments": fn_args,
                    "result": result_parsed,
                    "summary": _summarize_tool_result(fn_name, result_parsed),
                })

                # Append tool result for the LLM
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result_str,
                })

            continue

        # No tool calls — LLM returned a text response
        text = response_msg.get("content", "")

        # Check if any tool produced an updated draft
        updated_draft = None
        for tc in tool_call_log:
            result = tc["result"]
            if tc["tool"] in ("generate_draft", "squeeze_word_count", "restyle_tone"):
                draft_text = result.get("text") or result.get("draft")
                if draft_text:
                    updated_draft = draft_text

        return {
            "text": text,
            "updated_draft": updated_draft,
            "tool_calls": tool_call_log,
        }

    # Fallback if max iterations reached
    return {
        "text": "I've reached the maximum number of steps. Please try a simpler request.",
        "updated_draft": None,
        "tool_calls": tool_call_log,
    }


def _summarize_tool_result(tool_name: str, result: dict) -> str:
    """Generate a brief human-readable summary of a tool result."""
    if tool_name == "search_knowledge_base":
        n = result.get("matches", 0)
        return f"Found {n} relevant passage{'s' if n != 1 else ''}"
    elif tool_name == "generate_draft":
        wc = result.get("word_count", 0)
        return f"Generated draft ({wc} words)"
    elif tool_name == "squeeze_word_count":
        wc = result.get("word_count", 0)
        return f"Squeezed to {wc} words"
    elif tool_name == "score_against_rubric":
        score = result.get("score", "?")
        return f"Scored {score}/100"
    elif tool_name == "analyze_evidence_gaps":
        n = result.get("evidence_found", 0)
        return f"Analyzed gaps ({n} evidence items found)"
    elif tool_name == "restyle_tone":
        wc = result.get("word_count", 0)
        return f"Restyled for public sector tone ({wc} words)"
    elif tool_name == "compliance_check":
        total = result.get("total", 0)
        addressed = result.get("addressed", 0)
        gaps = result.get("gaps", 0)
        pct = result.get("coverage_pct", 0)
        return f"Compliance: {addressed}/{total} addressed, {gaps} gaps ({pct}% coverage)"
    return f"Executed {tool_name}"
