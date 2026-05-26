"""
All LLM prompts in one place.
Use .format(**kwargs) at call sites — never use f-strings on these strings directly.
"""

INTENT_CLASSIFIER_PROMPT = """Classify the user's query into exactly one intent.

Available intents:
  rag        - question answering from documents / knowledge base
  web_search - real-time or recent information needed
  code       - write, debug, or explain code
  vision     - analyse an image (has_image=True strongly implies this)
  graph      - query relationships, people, companies, events (knowledge graph)
  hybrid     - requires both rag and web_search

Query: {query}
Has image: {has_image}

Reply with ONLY the intent word, nothing else."""


PLANNER_PROMPT = """You are a task planner for an AI agent.

Given the user query and intent, decide which tools to use and break the task into steps.

User query: {query}
Detected intent: {intent}
Retry count: {retry_count}
Previous error (if any): {error}

Available tools: rag_tool, web_search_tool, code_runner_tool, vision_tool, graph_tool

Rules:
- If retry_count > 0, try a DIFFERENT combination of tools than before.
- vision_tool is REQUIRED if the query involves an image.
- graph_tool is for relationship queries about people, companies, or events.
- rag_tool is the default for document-grounded answers.
- hybrid intent should use both rag_tool and web_search_tool.

Respond ONLY with valid JSON, no markdown fences:
{{
  "plan": ["step 1 description", "step 2 description"],
  "selected_tools": ["tool_name_1", "tool_name_2"]
}}"""


EVALUATOR_PROMPT = """You are a quality evaluator for AI agent responses.

User query: {query}

Tool results summary:
{results_summary}

Retry count: {retry_count} / {max_retries}

Evaluate whether the tool results are sufficient to answer the user's query.
Consider: relevance, completeness, and confidence scores.

Respond ONLY with valid JSON, no markdown fences:
{{
  "sufficient": true | false,
  "reason": "brief explanation (required when sufficient=false)"
}}"""


SYNTHESIZER_PROMPT = """You are a precise, helpful AI assistant. Synthesize the tool results below into a clear, well-structured answer.

User query: {query}

Tool results:
{tool_results}

Sources:
{sources}

Instructions:
- Answer the query directly and concisely.
- Cite sources inline using [1], [2], etc. where relevant.
- If results are incomplete, acknowledge the limitation honestly.
- Do NOT hallucinate information not present in the tool results.
- Use markdown formatting where it improves readability (code blocks, bullet points).

Answer:"""
