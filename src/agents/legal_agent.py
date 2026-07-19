"""
Legal AI Agent — Tool-Use Architecture
Uses Claude's native tool_use to autonomously decide which tools to call
based on user questions. Replaces hardcoded Q&A flow.
"""
import json
import httpx
import os
from typing import Optional, List, AsyncGenerator
from psycopg2.extras import RealDictCursor
from .company_memory import get_company_memory, update_company_memory, init_memory
from .context_builder import build_user_context, init_context

# ============================================
# Shared DB & Claude config (imported from main)
# ============================================

# These will be set by init_agent() called from main.py
_get_db = None
_multi_query_search = None
_search_laws = None
_llm_provider_manager = None

# LLM calls are routed through GroqProvider (no direct API URL needed)


def init_agent(get_db_fn, multi_query_search_fn, search_laws_fn, llm_provider_manager_fn=None):
    """Initialize agent with shared functions from main.py"""
    global _get_db, _multi_query_search, _search_laws, _llm_provider_manager
    _get_db = get_db_fn
    _multi_query_search = multi_query_search_fn
    _search_laws = search_laws_fn
    _llm_provider_manager = llm_provider_manager_fn
    # Initialize company memory and context builder with same DB function
    init_memory(get_db_fn)
    init_context(get_db_fn)


# ============================================
# Tool Definitions
# ============================================

TOOLS = [
    {
        "name": "search_law",
        "description": "Search Indian Law documents by keyword. Use when needing to look up acts, codes, rules, or judgments. ALWAYS use this tool before answering legal questions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Legal search keyword"},
                "domains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Domain: labour, corporate, civil, criminal, tax, property, consumer, it_cyber, constitutional"
                },
                "limit": {"type": "integer", "default": 10, "description": "Max results"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_contract",
        "description": "Read uploaded contract content. Use when user asks about a specific contract or needs it reviewed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "Contract ID (UUID)"}
            },
            "required": ["contract_id"]
        }
    },
    {
        "name": "list_contracts",
        "description": "List all company contracts. Use for an overview or when user asks 'which contracts' or 'contract list'.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "search_company_docs",
        "description": "Search internal company documents. Use to find rules, policies, internal documents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword in company documents"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_contract_risk",
        "description": "Detailed legal risk analysis for a contract. Use when asked to review, assess risks, or check legal compliance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "Contract ID to analyze"}
            },
            "required": ["contract_id"]
        }
    },
    {
        "name": "review_contract_ai",
        "description": "Review contract with AI Contract Review Service — Analyzes 10 risk categories, checks compliance with Indian Law (Indian Contract Act 1872, Companies Act 2013, IR Code 2020), scores risk 0-100, suggests specific revisions. Use for comprehensive review.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "Contract ID to review"}
            },
            "required": ["contract_id"]
        }
    },
    {
        "name": "draft_document",
        "description": "Draft new legal document (contract, petition, decision, minutes, official letter, rules). Use when user asks to draft/create a document.",
        "input_schema": {
            "type": "object",
            "properties": {
                "doc_type": {
                    "type": "string",
                    "description": "Document type: contract, petition, decision, minutes, official_letter, internal_rules, employment_contract, service_contract"
                },
                "requirements": {
                    "type": "string",
                    "description": "Detailed requirements for the document"
                },
                "template_id": {
                    "type": "string",
                    "description": "Template ID (optional)"
                }
            },
            "required": ["doc_type", "requirements"]
        }
    },
    {
        "name": "get_company_profile",
        "description": "Get company profile: name, type, industry, headcount, current contracts, documents. Use when company context is needed.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "compare_contracts",
        "description": "Compare 2 or more contracts. Find differences, inconsistencies, and evaluate which contract is more favorable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contract_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of Contract IDs to compare (min 2)"
                }
            },
            "required": ["contract_ids"]
        }
    },
    {
        "name": "summarize_contract",
        "description": "Create a brief summary of a contract: parties, value, duration, main clauses. Use for a quick summary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "Contract ID"}
            },
            "required": ["contract_id"]
        }
    },
    {
        "name": "check_legal_compliance",
        "description": "Check if contract complies with basic legal requirements (mandatory clauses, duration, penalties...). Use for compliance checks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string"},
                "check_type": {"type": "string", "enum": ["labor", "commercial", "service", "all"], "description": "Check type: labor, commercial, service, all"}
            },
            "required": ["contract_id"]
        }
    },
    {
        "name": "generate_clause",
        "description": "Draft a specific legal clause. Use when user asks to draft a confidentiality, penalty, termination, etc., clause.",
        "input_schema": {
            "type": "object",
            "properties": {
                "clause_type": {"type": "string", "description": "Clause type: confidentiality, penalty, termination, compensation, warranty, payment, dispute, force_majeure"},
                "context": {"type": "string", "description": "Specific context/requirements"}
            },
            "required": ["clause_type"]
        }
    },
    {
        "name": "crawl_legal_document",
        "description": "Crawl and extract content from a legal document URL. Use when user provides a legal document link and wants to analyze it or add it to the knowledge base. CrawlKit API key required.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL of the legal document to crawl"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "list_documents",
        "description": "List all documents and contracts in the company's system. Use to find files, view document lists, or check which files exist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "folder": {"type": "string", "description": "Folder to list (default: all)"},
                "search": {"type": "string", "description": "Search keyword in file name"},
                "type": {"type": "string", "enum": ["all", "contract", "document", "template"], "description": "File type to filter by"}
            }
        }
    },
    {
        "name": "read_document",
        "description": "Read the full content of a document or contract. Use to see detailed content, analyze, or extract information from a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "ID of the document to read"},
                "section": {"type": "string", "description": "Specific section to read (e.g., 'Section 5', 'Appendix')"}
            },
            "required": ["document_id"]
        }
    },
    {
        "name": "write_document",
        "description": "Create a new document or overwrite content. Use to draft contracts, legal documents, reports, or save analysis results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title"},
                "content": {"type": "string", "description": "FULL content of the document. IMPORTANT: Must write the ENTIRE content, DO NOT summarize or shorten. If processing an uploaded file, copy the original text exactly."},
                "type": {"type": "string", "enum": ["contract", "document", "template", "report", "memo"], "description": "Document type"},
                "folder": {"type": "string", "description": "Save folder (optional)"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Classification tags"}
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "edit_document",
        "description": "Edit a specific part of an existing document. Use to modify clauses, update content, or replace errors. Smarter than Find & Replace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "ID of document to edit"},
                "old_text": {"type": "string", "description": "Text to replace (exact match)"},
                "new_text": {"type": "string", "description": "New replacement content"},
                "description": {"type": "string", "description": "Short description of the change (for logging)"}
            },
            "required": ["document_id", "old_text", "new_text"]
        }
    },
    {
        "name": "compare_documents",
        "description": "Compare two documents and show differences. Use to see changes between versions, compare two contracts, or check edits.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id_1": {"type": "string", "description": "ID of first document"},
                "document_id_2": {"type": "string", "description": "ID of second document"},
                "mode": {"type": "string", "enum": ["summary", "detailed", "clause_by_clause"], "description": "Level of detail for comparison"}
            },
            "required": ["document_id_1", "document_id_2"]
        }
    },
    {
        "name": "create_folder",
        "description": "Create a new folder/case to organize documents. Use to classify by project, client, or legal case.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the folder/case"},
                "description": {"type": "string", "description": "Description"},
                "parent_folder": {"type": "string", "description": "Parent folder (if any)"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "move_document",
        "description": "Move a document to another folder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "Document ID"},
                "target_folder": {"type": "string", "description": "Target folder"}
            },
            "required": ["document_id", "target_folder"]
        }
    },
    {
        "name": "delete_document",
        "description": "Delete a document (moves to trash, recoverable for 30 days). Only use when user explicitly requests it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "ID of document to delete"},
                "reason": {"type": "string", "description": "Reason for deletion"}
            },
            "required": ["document_id"]
        }
    },
    {
        "name": "generate_document",
        "description": "Draft a new legal document from requirements. AI will draft contracts, petitions, letters, minutes, etc., based on description and information provided.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "Document type (employment_contract, lease_agreement, complaint, official_letter, minutes, nda, ...)"},
                "requirements": {"type": "string", "description": "Detailed requirements for content"},
                "parties": {"type": "array", "items": {"type": "string"}, "description": "Involved parties"},
                "key_terms": {"type": "object", "description": "Key terms (contract value, duration, ...)"},
                "save": {"type": "boolean", "description": "Auto-save to system", "default": True}
            },
            "required": ["type", "requirements"]
        }
    },
    {
        "name": "batch_review",
        "description": "Review multiple contracts/documents at once. Returns a risk summary for each file and an overview.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_ids": {"type": "array", "items": {"type": "string"}, "description": "List of document IDs to review"},
                "focus": {"type": "string", "description": "What aspect to focus on (penalty, compliance, risk, all)"}
            },
            "required": ["document_ids"]
        }
    },
    {
        "name": "document_history",
        "description": "View document edit history. Who edited what, and when.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "Document ID"}
            },
            "required": ["document_id"]
        }
    },
    {
        "name": "edit_and_diff_document",
        "description": "Edit contract/document and show diff view (comparing original vs edited version). Use when user asks to 'review and edit', 'modify contract', 'fix contract'. AI will automatically: (1) Analyze document, (2) Find legal issues, (3) Create edited version, (4) Display inline diff view, (5) Allow downloading the revised version.",
        "input_schema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "ID of document or contract to edit"},
                "edit_instructions": {"type": "string", "description": "Specific edit instructions (e.g., 'Add confidentiality clause per IR Code 2020', 'Fix typos', 'Update penalty')"},
                "auto_fix": {"type": "boolean", "description": "Automatically fix common legal errors (default: True)", "default": True}
            },
            "required": ["document_id"]
        }
    }
]

# ============================================
# System Prompt
# ============================================

AGENT_SYSTEM_PROMPT = """You are an intelligent AI Legal Assistant specializing in Indian Law.
You have full access to the document management system. You can read, create, edit, delete, and compare documents and contracts.
When the user requests an action, AUTOMATICALLY perform the necessary steps.
Example: "Fix the penalty clause in the contract" -> you automatically read -> find -> edit -> save.
Always report what you have done after completing a task.

## Chat Modes:
- **Casual Chat** — If the user says hi, asks how you are, etc., respond naturally and friendly. DO NOT use tools, DO NOT format as a report.
- **Legal Chat** — When the user asks about laws, contracts, or documents, THEN use tools and answer deeply.
- **Document Operations** — When asked to edit/create/delete, AUTOMATICALLY perform the action chain (read -> edit -> save).
- **Tone** — Professional yet friendly and easy to understand. Avoid being overly formal or using too many emojis.

## IMPORTANT — Drafting Documents:
- When the user asks to draft/edit a document, OUTPUT THE FULL DOCUMENT CONTENT.
- DO NOT just list "I changed X and Y" — output the complete revised version.
- If you need to explain changes, do it at the END, after the full document.
- Format: clear headings, numbered clauses, professional look.
- When using write_document/edit_document tools, just say "The document has been drafted, please check the Documents tab", do not repeat the whole text.

## STRICT PROHIBITION — Legal Citations (Anti-Hallucination):
- ONLY cite act/section numbers when search_law returns actual results.
- ABSOLUTELY DO NOT invent section numbers. If not found, say "according to current legal provisions".
- Prioritize using search_law BEFORE citing any specific law.
- DO NOT guess or rely on memory for section numbers — they must come from search_law.
- WRONG: "According to Section 293 of the Indian Contract Act..." (if search_law didn't return it)
- CORRECT: "According to current Indian contract law..." (then call search_law to find it)

## Professional Tone:
- Do not praise yourself as "professional" or "legally safe" — let the user judge.
- Do not claim "100% legal/accurate" — always add a disclaimer: "This is a draft, please consult an advocate before use."
- Humble, practical: "Here is the draft, please review and adjust as needed."
- Avoid emojis in official document content (only use in casual chat).

## When to use tools:
- Ask about specific laws -> search_law
- Ask about contracts -> list_contracts / read_contract
- Need to draft a document -> draft_document or generate_document
- Need to find a document -> search_company_docs or list_documents
- Need to review -> analyze_contract_risk or review_contract_ai
- Need company info -> get_company_profile
- Compare contracts -> compare_contracts or compare_documents
- Summarize contract -> summarize_contract
- Check legal compliance -> check_legal_compliance
- Draft specific clause -> generate_clause
- Crawl legal URL -> crawl_legal_document
- **Document Management:**
  - View list -> list_documents
  - Read document -> read_document
  - Create new document -> write_document
  - Edit document -> edit_document
  - **Review and fix contract -> edit_and_diff_document** (shows diff view like VSCode)
  - Compare 2 documents -> compare_documents
  - Create folder -> create_folder
  - Move file -> move_document
  - Delete file -> delete_document (be careful!)
  - Batch review -> batch_review
  - View edit history -> document_history
- **DO NOT use tools** for greetings, casual chat, simple questions.

## Multi-step workflows:
When the user asks for a complex task, you can call multiple tools sequentially:
- "Fix penalty clause in Contract ABC" -> read_document -> edit_document -> document_history
- "Draft NDA between A and B" -> generate_document -> write_document
- "Compare 3 contracts and pick the best" -> read_contract (x3) -> compare_documents -> recommendation

## When editing/revising documents:
- Use edit_and_diff_document to show a diff view (original vs edited)
- OR output the entire edited text (not just the changes).
- If highlighting changes: mark as [NEW] or [EDITED] inline.
- User wants to see the RESULT, not the PROCESS.

## When giving legal answers:
- Cite specifically: "Under Section X of Act Y" — ONLY if found via search_law.
- DO NOT invent numbers.
- Give practical advice, not just theory.
- Always add disclaimer: "Please consult an advocate before applying this" for serious matters.

## ACTION, DO NOT ASK BACK:
- When user says "help me fix", "edit", "fix" -> **DO IT IMMEDIATELY**, do not ask "what part do you want to fix?"
- Use edit_and_diff_document or edit_document immediately.
- If user uploaded a file -> edit that file.
- If user was just talking about a document -> edit that document.
- Only ask back if you REALLY don't know what to edit.
- **Prioritize action > asking** — like a good developer: receive task -> do it -> report result.

## Remember: You are a SMART assistant, not a search engine. Chat naturally first, use tools when needed. ALWAYS ANSWER WITH TEXT. ACT, DO NOT ASK BACK.
"""

# ============================================
# LLM API helpers (Groq Provider)
# ============================================

async def _call_llm_with_tools(messages: list, tools: list, system: str = AGENT_SYSTEM_PROMPT, max_tokens: int = 8192, model: str = None, company_id: str = None) -> dict:
    """Call LLM API (Groq Provider) with tool definitions, return raw response dict"""
    from src.services.llm_provider import GroqProvider
    
    provider = GroqProvider(model=model) if model else GroqProvider()
    result = await provider.chat(messages=messages, system=system, max_tokens=max_tokens, tools=tools)
    return result


# Fast path detection — skip agent loop for simple questions
SIMPLE_PATTERNS = [
    "hello", "hi", "hey", "thanks", "thank", 
    "who are you", "introduce yourself", "what can you do"
]
# Note: "ok", "yes", "sure", "yeah", "yep" are NOT simple — they are confirmations
# that NEED chat history context to understand what user is agreeing to

def is_simple_question(question: str) -> bool:
    """Check if question is simple enough to skip agent loop.
    Only skip for very obvious non-legal greetings/acknowledgments.
    Let Claude decide for everything else — trust the AI."""
    q = question.strip().lower()
    # Only skip for very short, clearly non-legal messages
    if len(q) < 15:
        for p in SIMPLE_PATTERNS:
            if q == p or q.startswith(p + " ") or q.endswith(" " + p):
                return True
    return False


def is_followup_question(question: str, chat_history: list = None) -> bool:
    """Check if this is a follow-up that doesn't need tools"""
    q = question.strip().lower()
    followup_markers = [
        "explain more", "more detail", "what do you mean",
        "example", "exception", "use case", "what else",
        "summarise", "summarize", "shorter", "translate",
        "anything else", "compare", "why", "more specific",
        "clarify", "meaning", "how to understand", "apply",
        "in practice", "specific example", "explain", "what does it mean"
    ]
    if any(m in q for m in followup_markers) and chat_history and len(chat_history) >= 2:
        return True
    return False


def generate_quick_replies(question: str, answer: str, tools_used: list) -> list:
    """Generate contextual quick reply suggestions based on tools used and context"""
    suggestions = []

    if 'search_law' in tools_used:
        suggestions.extend([
            {"text": "Analyse in more detail", "icon": "📊"},
            {"text": "Related provisions", "icon": "🔗"},
            {"text": "Compare with earlier law", "icon": "⚖️"}
        ])
    elif 'read_contract' in tools_used or 'analyze_contract_risk' in tools_used:
        suggestions.extend([
            {"text": "Suggest specific revisions", "icon": "✏️"},
            {"text": "Export review report", "icon": "📥"},
            {"text": "Compare with another contract", "icon": "🔄"}
        ])
    elif 'list_contracts' in tools_used:
        suggestions.extend([
            {"text": "Overall risk analysis", "icon": "⚠️"},
            {"text": "Which contracts are expiring?", "icon": "📅"},
            {"text": "Compare all contracts", "icon": "📊"}
        ])
    elif 'draft_document' in tools_used:
        suggestions.extend([
            {"text": "Edit content", "icon": "✏️"},
            {"text": "Add confidentiality clause", "icon": "🔒"},
            {"text": "Export to Word", "icon": "📄"}
        ])
    elif 'search_company_docs' in tools_used:
        suggestions.extend([
            {"text": "Analyse this document", "icon": "📊"},
            {"text": "Find related documents", "icon": "🔍"},
            {"text": "Compare with legal provisions", "icon": "⚖️"}
        ])
    else:
        # General/greeting
        suggestions.extend([
            {"text": "Search labour law", "icon": "🔍"},
            {"text": "Review a contract", "icon": "📄"},
            {"text": "Draft a new document", "icon": "✍️"}
        ])

    return suggestions[:4]  # Max 4 suggestions


def extract_inline_actions(answer_text: str, tools_used: list, tool_results: list) -> list:
    """Extract actionable items from agent response and tool results"""
    actions = []

    for result in tool_results:
        tool_name = result.get("tool", "")
        data = result.get("data", {})

        if tool_name == "list_contracts":
            contracts = data.get("contracts", [])
            for contract in contracts[:3]:
                actions.append({
                    "type": "view_contract",
                    "id": str(contract.get("id", "")),
                    "label": f"📄 {str(contract.get('name', ''))[:40]}"
                })
        elif tool_name == "read_contract" or tool_name == "analyze_contract_risk":
            contract = data.get("contract", {})
            if contract.get("id"):
                actions.append({
                    "type": "view_contract",
                    "id": str(contract["id"]),
                    "label": f"📄 {str(contract.get('name', ''))[:40]}"
                })
        elif tool_name == "search_company_docs":
            docs = data.get("documents", [])
            for doc in docs[:3]:
                actions.append({
                    "type": "view_document",
                    "id": str(doc.get("id", "")),
                    "label": f"📋 {str(doc.get('name', ''))[:40]}"
                })

    return actions


async def quick_answer(question: str, chat_history: list = None) -> dict:
    """Direct LLM call without tools — for simple questions"""
    from src.services.llm_provider import GroqProvider
    
    provider = GroqProvider()
    messages = []
    if chat_history:
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})
    
    result = await provider.chat(
        system=AGENT_SYSTEM_PROMPT,
        messages=messages,
        max_tokens=2048
    )
    
    text = "".join(b.get("text", "") for b in result.get("content", []) if b.get("type") == "text")
    usage = result.get("usage", {})
    return {
        "answer": text,
        "citations": [],
        "input_tokens": usage.get("input", 0),
        "output_tokens": usage.get("output", 0),
        "model": result.get("model", ""),
        "tool_calls_made": 0
    }


async def _call_llm_with_tools_stream(messages: list, tools: list, system: str = AGENT_SYSTEM_PROMPT, max_tokens: int = 8192):
    """Call LLM API with tools + streaming. Uses GroqProvider (non-streaming wrapper)."""
    from src.services.llm_provider import GroqProvider
    provider = GroqProvider()
    result = await provider.chat(messages=messages, system=system, max_tokens=max_tokens, tools=tools)
    # Yield the full result as a single event (Groq doesn't support streaming with tools easily)
    yield result


async def _stream_final_text(messages: list, system: str = AGENT_SYSTEM_PROMPT, company_id: str = None) -> AsyncGenerator[str, None]:
    """Stream LLM response without tools — for fast path"""
    from src.services.llm_provider import GroqProvider
    
    try:
        provider = GroqProvider()
        result = await provider.chat(messages=messages, system=system, max_tokens=4096)
        
        # Extract text from result and yield as SSE delta events
        text_parts = [b.get("text", "") for b in result.get("content", []) if b.get("type") == "text"]
        full_text = "".join(text_parts)
        
        if full_text:
            # Yield in chunks to simulate streaming for the frontend
            chunk_size = 20  # characters per chunk
            for i in range(0, len(full_text), chunk_size):
                chunk = full_text[i:i+chunk_size]
                yield f"data: {json.dumps({'type': 'delta', 'text': chunk}, ensure_ascii=False)}\n\n"
    except Exception as e:
        print(f"[DEBUG] Provider error: {e}")
        import traceback; traceback.print_exc()
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"


# ============================================
# Tool Execution
# ============================================

async def execute_tool(tool_name: str, tool_input: dict, company_id: str) -> dict:
    """Execute a tool and return result dict"""

    if tool_name == "search_law":
        return await _tool_search_law(tool_input, company_id)
    elif tool_name == "read_contract":
        return await _tool_read_contract(tool_input, company_id)
    elif tool_name == "list_contracts":
        return await _tool_list_contracts(company_id)
    elif tool_name == "search_company_docs":
        return await _tool_search_company_docs(tool_input, company_id)
    elif tool_name == "analyze_contract_risk":
        return await _tool_analyze_contract_risk(tool_input, company_id)
    elif tool_name == "review_contract_ai":
        return await _tool_review_contract_ai(tool_input, company_id)
    elif tool_name == "draft_document":
        return await _tool_draft_document(tool_input, company_id)
    elif tool_name == "get_company_profile":
        return await _tool_get_company_profile(company_id)
    elif tool_name == "compare_contracts":
        return await _tool_compare_contracts(tool_input, company_id)
    elif tool_name == "crawl_legal_document":
        return await _tool_crawl_legal_document(tool_input, company_id)
    elif tool_name == "summarize_contract":
        contract_id = tool_input.get("contract_id")
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT name, content, parties, start_date, end_date, contract_type, metadata FROM contracts WHERE id = %s AND company_id = %s AND status != 'deleted'", (contract_id, company_id))
            contract = cur.fetchone()
        if not contract:
            return {"error": "Contract not found"}
        content = contract.get("content", "")[:5000]
        return {
            "name": contract["name"],
            "type": contract.get("contract_type", "N/A"),
            "parties": contract.get("parties", []),
            "start_date": str(contract.get("start_date", "N/A")),
            "end_date": str(contract.get("end_date", "N/A")),
            "content_preview": content,
            "notes": (contract.get("metadata") or {}).get("notes", [])
        }
    elif tool_name == "check_legal_compliance":
        contract_id = tool_input.get("contract_id")
        check_type = tool_input.get("check_type", "all")
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT name, content, contract_type FROM contracts WHERE id = %s AND company_id = %s AND status != 'deleted'", (contract_id, company_id))
            contract = cur.fetchone()
        if not contract:
            return {"error": "Contract not found"}
        content = contract.get("content", "")[:10000]
        checks = {
            "labor": [
                {"item": "Employee Information", "keywords": ["name", "date of birth", "aadhaar", "pan", "employee id"]},
                {"item": "Type of Employment Contract", "keywords": ["fixed term", "permanent", "probation", "contractual", "apprentice"]},
                {"item": "Job Description", "keywords": ["duties", "responsibilities", "designation", "position", "role"]},
                {"item": "Working Hours", "keywords": ["working hours", "shift", "overtime", "leaves"]},
                {"item": "Salary & Remuneration", "keywords": ["salary", "wages", "remuneration", "ctc", "compensation"]},
                {"item": "Provident Fund & ESI", "keywords": ["provident fund", "pf", "esi", "esic", "gratuity"]},
                {"item": "Termination Conditions", "keywords": ["termination", "notice period", "resignation", "dismissal", "retrenchment"]},
            ],
            "commercial": [
                {"item": "Party Details", "keywords": ["party a", "party b", "authorized signatory", "gst number", "cin"]},
                {"item": "Subject Matter", "keywords": ["subject", "goods", "services", "product", "scope"]},
                {"item": "Contract Value", "keywords": ["price", "value", "payment", "amount", "consideration"]},
                {"item": "Delivery Timeline", "keywords": ["timeline", "delivery date", "schedule", "deadline"]},
                {"item": "Rights and Obligations", "keywords": ["rights", "obligations", "responsibilities", "duties"]},
                {"item": "Penalty for Breach", "keywords": ["penalty", "breach", "liquidated damages", "compensation"]},
                {"item": "Dispute Resolution", "keywords": ["dispute", "arbitration", "court", "jurisdiction"]},
            ],
            "service": [
                {"item": "Scope of Services", "keywords": ["scope", "services", "deliverables", "work order"]},
                {"item": "Quality Standards", "keywords": ["quality", "standards", "kpi", "sla", "benchmark"]},
                {"item": "Duration and Renewal", "keywords": ["duration", "renewal", "extension", "term"]},
                {"item": "Confidentiality", "keywords": ["confidential", "non-disclosure", "nda", "proprietary"]},
                {"item": "Termination Clause", "keywords": ["termination", "cancellation", "exit", "discontinue"]},
            ]
        }
        content_lower = content.lower()
        check_types = [check_type] if check_type != "all" else ["labor", "commercial", "service"]
        results = []
        for ct in check_types:
            for check in checks.get(ct, []):
                found = any(kw in content_lower for kw in check["keywords"])
                results.append({
                    "category": ct,
                    "item": check["item"],
                    "status": "pass" if found else "missing",
                    "keywords_found": [kw for kw in check["keywords"] if kw in content_lower]
                })
        passed = sum(1 for r in results if r["status"] == "pass")
        total = len(results)
        return {
            "contract_name": contract["name"],
            "check_type": check_type,
            "score": f"{passed}/{total}",
            "percentage": round(passed/total*100) if total > 0 else 0,
            "results": results,
            "missing_items": [r["item"] for r in results if r["status"] == "missing"]
        }
    elif tool_name == "generate_clause":
        clause_type = tool_input.get("clause_type", "")
        context = tool_input.get("context", "")
        clause_templates = {
            "bao_mat": "CONFIDENTIALITY CLAUSE\n1. The parties commit to keeping all information related to this Contract confidential.\n2. Confidential information includes but is not limited to: technical, financial, business information, customer data.\n3. Confidentiality obligations are valid during the contract term and [X] years after termination.\n4. The breaching party must compensate for all direct and indirect damages.",
            "phat_vi_pham": "PENALTY CLAUSE\n1. The party breaching contract obligations must pay a penalty equal to [X]% of the contract value.\n2. The penalty must be reasonable and proportionate to the loss (as per Indian Contract Act 1872).\n3. Besides the penalty, the breaching party must compensate for actual damages incurred.\n4. The aggrieved party has the right to claim the penalty.",
            "cham_dut": "TERMINATION CLAUSE\n1. The contract terminates when: (a) term expires, (b) obligations are fulfilled, (c) parties agree.\n2. Unilateral termination: the terminating party must give [X] days prior written notice.\n3. Unlawful unilateral termination requires compensation for damages.\n4. Confidentiality and penalty clauses remain valid after termination.",
            "boi_thuong": "COMPENSATION CLAUSE\n1. The party causing damage must fully and timely compensate.\n2. Compensated damages include: direct damages, lost benefits, reasonable expenses.\n3. The maximum compensation shall not exceed [X]% of the contract value.\n4. The claiming party must prove damages with valid documents.",
            "thanh_toan": "PAYMENT CLAUSE\n1. Contract value: [amount] INR (in words: ...).\n2. Method: bank transfer.\n3. Schedule: (a) [X]% advance upon signing, (b) [X]% upon acceptance, (c) [X]% upon completion.\n4. Payment term: within [X] working days from receipt of valid invoice.\n5. Late payment incurs interest of [X]%/month on the delayed amount.",
            "tranh_chap": "DISPUTE RESOLUTION CLAUSE\n1. Any arising disputes shall first be resolved through negotiation and mediation.\n2. If unresolved within [X] days, the dispute shall be submitted to [Court/Arbitration].\n3. Governing law: Indian Law.\n4. The decision of the [Court/Arbitration] is final and binding on the parties.",
            "bat_kha_khang": "FORCE MAJEURE CLAUSE\n1. Force majeure is an objective, unforeseeable, and insurmountable event (natural disaster, epidemic, war, change in law...).\n2. The affected party must notify in writing within [X] days.\n3. The contract performance period is extended by the duration of the force majeure.\n4. If force majeure lasts over [X] days, parties have the right to terminate the contract."
        }
        template = clause_templates.get(clause_type, f"Template not found for type '{clause_type}'. Available types: {', '.join(clause_templates.keys())}")
        return {
            "clause_type": clause_type,
            "template": template,
            "context": context,
            "note": "This is a reference template. AI will customize it according to the specific context."
        }
    elif tool_name == "crawl_legal_document":
        url = tool_input.get("url", "")
        
        try:
            from ..services.crawler import LegalCrawler
            crawler = LegalCrawler()
            crawl_result = crawler.crawl_and_index(url, company_id)
            if crawl_result["success"]:
                doc = crawl_result["document"]
                return {
                    "success": True,
                    "title": doc['title'],
                    "url": url,
                    "content_length": crawl_result['content_length'],
                    "chunks": crawl_result['chunks'],
                    "source": doc['source'],
                    "content_preview": doc['content'][:2000],
                    "full_content": doc['content'],
                    "message": f"✅ Crawled successfully!\n\n📄 **{doc['title']}**\n🔗 {url}\n📊 {crawl_result['content_length']:,} characters, {crawl_result['chunks']} chunks\n📁 Source: {doc['source']}"
                }
            else:
                return {"error": f"❌ Crawl failed: {crawl_result['error']}"}
        except Exception as e:
            return {"error": f"❌ Crawl error: {str(e)}"}
    
    # ============================================
    # NEW AGENTIC TOOLS — Full Document Control
    # ============================================
    
    elif tool_name == "list_documents":
        folder = tool_input.get("folder")
        search = tool_input.get("search")
        doc_type = tool_input.get("type", "all")
        
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Build query
            query = "SELECT id, name, doc_type, file_size, created_at FROM documents WHERE company_id = %s AND deleted_at IS NULL"
            params = [company_id]
            
            if folder:
                query += " AND folder_id = (SELECT id FROM folders WHERE name = %s AND company_id = %s LIMIT 1)"
                params.extend([folder, company_id])
            
            if search:
                query += " AND name ILIKE %s"
                params.append(f"%{search}%")
            
            if doc_type != "all" and doc_type == "document":
                pass  # documents table
            
            query += " ORDER BY created_at DESC LIMIT 50"
            
            cur.execute(query, tuple(params))
            docs = [dict(r) for r in cur.fetchall()]
            
            # Also get contracts if type is "all" or "contract"
            contracts = []
            if doc_type in ["all", "contract"]:
                query_c = "SELECT id, name, contract_type as doc_type, NULL as file_size, created_at FROM contracts WHERE company_id = %s AND status != 'deleted' AND deleted_at IS NULL"
                params_c = [company_id]
                
                if folder:
                    query_c += " AND folder_id = (SELECT id FROM folders WHERE name = %s AND company_id = %s LIMIT 1)"
                    params_c.extend([folder, company_id])
                
                if search:
                    query_c += " AND name ILIKE %s"
                    params_c.append(f"%{search}%")
                
                query_c += " ORDER BY created_at DESC LIMIT 50"
                
                cur.execute(query_c, tuple(params_c))
                contracts = [dict(r) for r in cur.fetchall()]
            
            all_items = docs + contracts
            all_items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return {
                "items": all_items[:50],
                "total": len(all_items),
                "folder": folder,
                "search": search
            }
    
    elif tool_name == "read_document":
        document_id = tool_input.get("document_id", "")
        section = tool_input.get("section")
        
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Try documents table first
            cur.execute("""
                SELECT id, name, extracted_text, doc_type, file_size, created_at
                FROM documents
                WHERE id::text = %s AND company_id = %s AND deleted_at IS NULL
            """, (document_id, company_id))
            doc = cur.fetchone()
            
            # If not found, try contracts table
            if not doc:
                cur.execute("""
                    SELECT id, name, content as extracted_text, contract_type as doc_type, NULL as file_size, created_at
                    FROM contracts
                    WHERE id::text = %s AND company_id = %s AND status != 'deleted' AND deleted_at IS NULL
                """, (document_id, company_id))
                doc = cur.fetchone()
            
            if not doc:
                return {"error": f"Document not found with ID: {document_id}"}
            
            content = doc.get("extracted_text", "") or ""
            
            # If section specified, try to extract it
            if section and section.lower() in content.lower():
                # Simple extraction: find section and get next 1000 chars
                import re
                pattern = re.escape(section)
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    start = match.start()
                    end = min(start + 2000, len(content))
                    content = content[start:end]
            
            return {
                "id": str(doc["id"]),
                "name": doc["name"],
                "type": doc.get("doc_type", "N/A"),
                "content": content,
                "content_length": len(content),
                "created_at": str(doc.get("created_at", ""))
            }
    
    elif tool_name == "write_document":
        title = tool_input.get("title", "")
        content = tool_input.get("content", "")
        doc_type = tool_input.get("type", "document")
        folder = tool_input.get("folder")
        tags = tool_input.get("tags", [])
        
        if not title or not content:
            return {"error": "Missing info: title and content are required"}
        
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get folder_id if folder specified
            folder_id = None
            if folder:
                cur.execute("SELECT id FROM folders WHERE name = %s AND company_id = %s", (folder, company_id))
                folder_row = cur.fetchone()
                if folder_row:
                    folder_id = folder_row["id"]
            
            # Insert document
            cur.execute("""
                INSERT INTO documents (company_id, name, extracted_text, doc_type, status, folder_id, tags, file_path, file_size, mime_type)
                VALUES (%s, %s, %s, 'other', 'analyzed', %s, %s, 'ai-generated', %s, 'text/plain')
                RETURNING id, name, created_at
            """, (company_id, title, content, folder_id, tags, len(content.encode('utf-8'))))
            
            new_doc = dict(cur.fetchone())
            conn.commit()
            
            # Log edit
            cur.execute("""
                INSERT INTO document_edits (document_id, company_id, edit_type, new_content, description)
                VALUES (%s, %s, 'create', %s, %s)
            """, (new_doc["id"], company_id, content[:1000], f"AI created document: {title}"))
            conn.commit()
            
            return {
                "success": True,
                "document_id": str(new_doc["id"]),
                "title": new_doc["name"],
                "message": f"✅ Document created: {title}",
                "created_at": str(new_doc.get("created_at", ""))
            }
    
    elif tool_name == "edit_document":
        document_id = tool_input.get("document_id", "")
        old_text = tool_input.get("old_text", "")
        new_text = tool_input.get("new_text", "")
        description = tool_input.get("description", "AI edit")
        
        if not document_id or not old_text:
            return {"error": "Missing info: document_id and old_text are required"}
        
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get current document
            cur.execute("""
                SELECT id, name, extracted_text FROM documents
                WHERE id::text = %s AND company_id = %s AND deleted_at IS NULL
            """, (document_id, company_id))
            doc = cur.fetchone()
            
            if not doc:
                # Try contracts table
                cur.execute("""
                    SELECT id, name, content as extracted_text FROM contracts
                    WHERE id::text = %s AND company_id = %s AND status != 'deleted' AND deleted_at IS NULL
                """, (document_id, company_id))
                doc = cur.fetchone()
                table_name = "contracts"
                content_col = "content"
            else:
                table_name = "documents"
                content_col = "extracted_text"
            
            if not doc:
                return {"error": f"Document not found: {document_id}"}
            
            old_content = doc.get("extracted_text", "") or ""
            
            # Replace old_text with new_text
            if old_text not in old_content:
                return {"error": f"Could not find text to replace: '{old_text[:50]}...'"}
            
            new_content = old_content.replace(old_text, new_text, 1)
            
            # Update document
            cur.execute(f"""
                UPDATE {table_name}
                SET {content_col} = %s, updated_at = NOW()
                WHERE id = %s
            """, (new_content, doc["id"]))
            conn.commit()
            
            # Log edit
            cur.execute("""
                INSERT INTO document_edits (document_id, company_id, edit_type, old_content, new_content, description)
                VALUES (%s, %s, 'edit', %s, %s, %s)
            """, (doc["id"], company_id, old_text[:1000], new_text[:1000], description))
            conn.commit()
            
            return {
                "success": True,
                "document_id": str(doc["id"]),
                "document_name": doc["name"],
                "message": f"✅ Document updated: {doc['name']}",
                "old_text_preview": old_text[:100],
                "new_text_preview": new_text[:100]
            }
    
    elif tool_name == "compare_documents":
        doc1_id = tool_input.get("document_id_1", "")
        doc2_id = tool_input.get("document_id_2", "")
        mode = tool_input.get("mode", "summary")
        
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get both documents
            docs = []
            for doc_id in [doc1_id, doc2_id]:
                cur.execute("""
                    SELECT id, name, extracted_text FROM documents
                    WHERE id::text = %s AND company_id = %s AND deleted_at IS NULL
                    UNION ALL
                    SELECT id, name, content as extracted_text FROM contracts
                    WHERE id::text = %s AND company_id = %s AND status != 'deleted' AND deleted_at IS NULL
                """, (doc_id, company_id, doc_id, company_id))
                doc = cur.fetchone()
                if doc:
                    docs.append(dict(doc))
            
            if len(docs) != 2:
                return {"error": "One or both documents not found"}
            
            # Simple diff using difflib
            import difflib
            text1 = docs[0].get("extracted_text", "") or ""
            text2 = docs[1].get("extracted_text", "") or ""
            
            # Calculate similarity
            ratio = difflib.SequenceMatcher(None, text1, text2).ratio()
            
            # Get differences
            if mode == "detailed":
                diff = list(difflib.unified_diff(
                    text1.split('\n'), 
                    text2.split('\n'),
                    lineterm='',
                    n=1
                ))
                diff_text = '\n'.join(diff[:100])  # Limit to 100 lines
            else:
                diff_text = f"Similarity: {ratio*100:.1f}%"
            
            # Count changes
            added = text2.count('\n') - text1.count('\n')
            
            return {
                "document_1": {"id": str(docs[0]["id"]), "name": docs[0]["name"]},
                "document_2": {"id": str(docs[1]["id"]), "name": docs[1]["name"]},
                "similarity": round(ratio * 100, 1),
                "differences": diff_text,
                "lines_changed": abs(added),
                "mode": mode
            }
    
    elif tool_name == "create_folder":
        name = tool_input.get("name", "")
        description = tool_input.get("description", "")
        parent_folder = tool_input.get("parent_folder")
        
        if not name:
            return {"error": "Folder name is required"}
        
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get parent folder ID if specified
            parent_id = None
            if parent_folder:
                cur.execute("SELECT id FROM folders WHERE name = %s AND company_id = %s", (parent_folder, company_id))
                parent_row = cur.fetchone()
                if parent_row:
                    parent_id = parent_row["id"]
            
            # Create folder
            cur.execute("""
                INSERT INTO folders (company_id, name, description, parent_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id, name, created_at
            """, (company_id, name, description, parent_id))
            
            folder = dict(cur.fetchone())
            conn.commit()
            
            return {
                "success": True,
                "folder_id": str(folder["id"]),
                "name": folder["name"],
                "message": f"✅ Folder created: {name}"
            }
    
    elif tool_name == "move_document":
        document_id = tool_input.get("document_id", "")
        target_folder = tool_input.get("target_folder", "")
        
        if not document_id or not target_folder:
            return {"error": "Missing info: document_id and target_folder are required"}
        
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get folder ID
            cur.execute("SELECT id FROM folders WHERE name = %s AND company_id = %s", (target_folder, company_id))
            folder_row = cur.fetchone()
            if not folder_row:
                return {"error": f"Folder not found: {target_folder}"}
            
            folder_id = folder_row["id"]
            
            # Update document
            cur.execute("""
                UPDATE documents SET folder_id = %s
                WHERE id::text = %s AND company_id = %s AND deleted_at IS NULL
                RETURNING id, name
            """, (folder_id, document_id, company_id))
            doc = cur.fetchone()
            
            if not doc:
                # Try contracts
                cur.execute("""
                    UPDATE contracts SET folder_id = %s
                    WHERE id::text = %s AND company_id = %s AND status != 'deleted' AND deleted_at IS NULL
                    RETURNING id, name
                """, (folder_id, document_id, company_id))
                doc = cur.fetchone()
            
            if not doc:
                return {"error": f"Document not found: {document_id}"}
            
            conn.commit()
            
            # Log edit
            cur.execute("""
                INSERT INTO document_edits (document_id, company_id, edit_type, description)
                VALUES (%s, %s, 'move', %s)
            """, (doc["id"], company_id, f"Moved to folder: {target_folder}"))
            conn.commit()
            
            return {
                "success": True,
                "document_id": str(doc["id"]),
                "document_name": doc["name"],
                "target_folder": target_folder,
                "message": f"✅ Moved '{doc['name']}' to folder '{target_folder}'"
            }
    
    elif tool_name == "delete_document":
        document_id = tool_input.get("document_id", "")
        reason = tool_input.get("reason", "AI deletion")
        
        if not document_id:
            return {"error": "Missing document_id"}
        
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Soft delete document
            cur.execute("""
                UPDATE documents SET deleted_at = NOW()
                WHERE id::text = %s AND company_id = %s AND deleted_at IS NULL
                RETURNING id, name
            """, (document_id, company_id))
            doc = cur.fetchone()
            
            if not doc:
                # Try contracts
                cur.execute("""
                    UPDATE contracts SET deleted_at = NOW(), status = 'deleted'
                    WHERE id::text = %s AND company_id = %s AND deleted_at IS NULL
                    RETURNING id, name
                """, (document_id, company_id))
                doc = cur.fetchone()
            
            if not doc:
                return {"error": f"Document not found: {document_id}"}
            
            conn.commit()
            
            # Log edit
            cur.execute("""
                INSERT INTO document_edits (document_id, company_id, edit_type, description)
                VALUES (%s, %s, 'delete', %s)
            """, (doc["id"], company_id, reason))
            conn.commit()
            
            return {
                "success": True,
                "document_id": str(doc["id"]),
                "document_name": doc["name"],
                "message": f"✅ Document deleted: {doc['name']} (recoverable within 30 days)"
            }
    
    elif tool_name == "generate_document":
        doc_type = tool_input.get("type", "")
        requirements = tool_input.get("requirements", "")
        parties = tool_input.get("parties", [])
        key_terms = tool_input.get("key_terms", {})
        save = tool_input.get("save", True)
        
        if not doc_type or not requirements:
            return {"error": "Missing info: type and requirements are required"}
        
        # Call LLM to generate the document
        try:
            from src.services.llm_provider import GroqProvider
            provider = GroqProvider()
            
            system_prompt = """You are an expert in drafting Indian legal documents. Draft comprehensive, professional documents in compliance with the law."""
            
            user_message = f"""Draft legal document:

Type: {doc_type}
Requirements: {requirements}
Parties: {', '.join(parties) if parties else 'N/A'}
Key terms: {json.dumps(key_terms, ensure_ascii=False)}

Return a complete, correctly formatted document containing all legally required clauses."""
            
            result = await provider.chat(
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=8192
            )
            
            generated_content = result["content"][0]["text"] if result.get("content") else ""
            
            # Save if requested
            if save:
                with _get_db() as conn:
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute("""
                        INSERT INTO documents (company_id, name, extracted_text, doc_type, status, file_path, file_size, mime_type)
                        VALUES (%s, %s, %s, 'other', 'analyzed', 'ai-generated', %s, 'text/plain')
                        RETURNING id
                    """, (company_id, f"{doc_type}_{parties[0] if parties else 'generated'}", generated_content, len(generated_content.encode('utf-8'))))
                    
                    doc_id = cur.fetchone()["id"]
                    conn.commit()
            else:
                doc_id = None
            
            return {
                "success": True,
                "document_type": doc_type,
                "content": generated_content,
                "document_id": str(doc_id) if doc_id else None,
                "saved": save,
                "message": "✅ Document generated successfully"
            }
        
        except Exception as e:
            return {"error": f"Generation error: {str(e)}"}
    
    elif tool_name == "batch_review":
        document_ids = tool_input.get("document_ids", [])
        focus = tool_input.get("focus", "all")
        
        if not document_ids or len(document_ids) == 0:
            return {"error": "Missing document list"}
        
        reviews = []
        
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            for doc_id in document_ids[:10]:  # Limit to 10 docs
                # Get document
                cur.execute("""
                    SELECT id, name, extracted_text FROM documents
                    WHERE id::text = %s AND company_id = %s AND deleted_at IS NULL
                    UNION ALL
                    SELECT id, name, content as extracted_text FROM contracts
                    WHERE id::text = %s AND company_id = %s AND status != 'deleted' AND deleted_at IS NULL
                """, (doc_id, company_id, doc_id, company_id))
                doc = cur.fetchone()
                
                if not doc:
                    reviews.append({"document_id": doc_id, "error": "Not found"})
                    continue
                
                # Quick risk assessment
                content = (doc.get("extracted_text", "") or "").lower()
                
                risks = []
                risk_score = 0
                
                # Check for common issues
                if "penalty" not in content and "breach" not in content:
                    risks.append("Missing penalty clause")
                    risk_score += 20
                
                if "confidentiality" not in content:
                    risks.append("Missing confidentiality clause")
                    risk_score += 15
                
                if "dispute" not in content:
                    risks.append("Missing dispute resolution clause")
                    risk_score += 20
                
                if "termination" not in content:
                    risks.append("Missing termination clause")
                    risk_score += 15
                
                reviews.append({
                    "document_id": str(doc["id"]),
                    "document_name": doc["name"],
                    "risk_score": min(risk_score, 100),
                    "risk_level": "low" if risk_score < 20 else "medium" if risk_score < 50 else "high",
                    "risks": risks
                })
        
        return {
            "total_reviewed": len(reviews),
            "focus": focus,
            "reviews": reviews,
            "summary": {
                "high_risk": sum(1 for r in reviews if r.get("risk_level") == "high"),
                "medium_risk": sum(1 for r in reviews if r.get("risk_level") == "medium"),
                "low_risk": sum(1 for r in reviews if r.get("risk_level") == "low")
            }
        }
    
    elif tool_name == "document_history":
        document_id = tool_input.get("document_id", "")
        
        if not document_id:
            return {"error": "Missing document_id"}
        
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Get edit history
            cur.execute("""
                SELECT id, edit_type, description, created_at, 
                       LEFT(old_content, 200) as old_preview,
                       LEFT(new_content, 200) as new_preview
                FROM document_edits
                WHERE document_id::text = %s AND company_id = %s
                ORDER BY created_at DESC
                LIMIT 50
            """, (document_id, company_id))
            
            edits = [dict(r) for r in cur.fetchall()]
            
            return {
                "document_id": document_id,
                "total_edits": len(edits),
                "history": [{
                    "edit_type": e["edit_type"],
                    "description": e.get("description", ""),
                    "old_preview": e.get("old_preview", ""),
                    "new_preview": e.get("new_preview", ""),
                    "created_at": str(e.get("created_at", ""))
                } for e in edits]
            }
    
    elif tool_name == "edit_and_diff_document":
        return await _tool_edit_and_diff_document(tool_input, company_id)
    
    else:
        return {"error": f"Unknown tool: {tool_name}"}


async def _tool_search_law(tool_input: dict, company_id: str) -> dict:
    """Search Indian law database"""
    query = tool_input.get("query", "")
    domains = tool_input.get("domains", None)
    limit = tool_input.get("limit", 10)

    if not domains:
        domains = _detect_domain(query)

    results = _multi_query_search(query, domains, min(limit, 8))

    citations = []
    formatted_results = []
    for i, src in enumerate(results, 1):
        law_title = src.get("law_title", "")
        law_number = src.get("law_number", "N/A")
        article = src.get("article", "N/A")
        content = src.get("content", "")[:1500]

        formatted_results.append({
            "index": i,
            "law_title": law_title,
            "law_number": law_number,
            "article": article,
            "content": content
        })

        citations.append({
            "source": law_title,
            "law_number": law_number,
            "article": article,
            "relevance": float(src.get("rank", 0))
        })

    return {
        "results": formatted_results,
        "total": len(formatted_results),
        "citations": citations
    }


async def _tool_read_contract(tool_input: dict, company_id: str) -> dict:
    """Read a specific contract"""
    contract_id = tool_input.get("contract_id", "")

    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, name, contract_type, extracted_text, parties,
                   start_date, end_date, value, status, notes, created_at
            FROM contracts
            WHERE id::text = %s AND company_id = %s AND status != 'deleted'
        """, (contract_id, company_id))
        contract = cur.fetchone()

    if not contract:
        return {"error": f"Contract not found with ID: {contract_id}"}

    result = dict(contract)
    # Convert dates to strings
    for key in ["start_date", "end_date", "created_at"]:
        if result.get(key):
            result[key] = str(result[key])
    # Parse parties JSON
    if result.get("parties"):
        try:
            if isinstance(result["parties"], str):
                result["parties"] = json.loads(result["parties"])
        except:
            pass

    return {
        "contract": result,
        "text_length": len(result.get("extracted_text", "") or "")
    }


async def _tool_list_contracts(company_id: str) -> dict:
    """List all contracts for a company"""
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, name, contract_type, parties, start_date, end_date,
                   value, status, created_at
            FROM contracts
            WHERE company_id = %s AND status != 'deleted'
            ORDER BY created_at DESC
            LIMIT 50
        """, (company_id,))
        contracts = cur.fetchall()

    results = []
    for c in contracts:
        item = dict(c)
        for key in ["start_date", "end_date", "created_at"]:
            if item.get(key):
                item[key] = str(item[key])
        if item.get("parties"):
            try:
                if isinstance(item["parties"], str):
                    item["parties"] = json.loads(item["parties"])
            except:
                pass
        results.append(item)

    return {
        "contracts": results,
        "total": len(results)
    }


async def _tool_search_company_docs(tool_input: dict, company_id: str) -> dict:
    """Search company's uploaded documents"""
    query = tool_input.get("query", "")

    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, name, doc_type, extracted_text, analysis, created_at
            FROM documents
            WHERE company_id = %s
              AND extracted_text IS NOT NULL
              AND length(extracted_text) > 50
            ORDER BY created_at DESC
            LIMIT 20
        """, (company_id,))
        docs = cur.fetchall()

    # Filter by relevance
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    relevant = []
    for doc in docs:
        text = (doc.get("extracted_text") or "").lower()
        name = (doc.get("name") or "").lower()
        score = sum(1 for w in query_words if w in text or w in name)
        if score > 0 or not query_words:
            relevant.append({
                "id": str(doc["id"]),
                "name": doc["name"],
                "doc_type": doc.get("doc_type"),
                "excerpt": (doc.get("extracted_text") or "")[:1500],
                "relevance_score": score,
                "created_at": str(doc["created_at"]) if doc.get("created_at") else None
            })

    relevant.sort(key=lambda x: x["relevance_score"], reverse=True)
    return {
        "documents": relevant[:10],
        "total": len(relevant)
    }


async def _tool_analyze_contract_risk(tool_input: dict, company_id: str) -> dict:
    """Analyze contract risk — reads contract + searches relevant laws"""
    contract_id = tool_input.get("contract_id", "")

    # Read the contract
    contract_data = await _tool_read_contract({"contract_id": contract_id}, company_id)
    if "error" in contract_data:
        return contract_data

    contract = contract_data["contract"]
    contract_text = contract.get("extracted_text", "")
    contract_type = contract.get("contract_type", "contract")

    if not contract_text or len(contract_text) < 50:
        return {"error": "Contract has no text content to analyse. Please re-upload the contract file."}

    # Search relevant laws for this contract type
    search_query = f"{contract_type} clauses rights obligations Indian law"
    law_results = _multi_query_search(search_query, None, 10)

    law_context = []
    for src in law_results:
        law_context.append({
            "law_title": src.get("law_title", ""),
            "law_number": src.get("law_number", ""),
            "article": src.get("article", ""),
            "content": src.get("content", "")[:1000]
        })

    return {
        "contract_name": contract.get("name", ""),
        "contract_type": contract_type,
        "contract_text": contract_text[:15000],
        "parties": contract.get("parties"),
        "relevant_laws": law_context,
        "instruction": "Analyse the legal risks of this contract based on its content and applicable Indian law. Evaluate: legality, missing clauses, risks for each party, and recommended amendments."
    }


async def _tool_review_contract_ai(tool_input: dict, company_id: str) -> dict:
    """
    Review contract using ContractReviewService — comprehensive risk analysis
    Returns structured review with 10 risk categories, compliance check, recommendations
    """
    from ..services.contract_review import ContractReviewService
    
    contract_id = tool_input.get("contract_id", "")
    
    # Read the contract
    contract_data = await _tool_read_contract({"contract_id": contract_id}, company_id)
    if "error" in contract_data:
        return contract_data
    
    contract = contract_data["contract"]
    contract_text = contract.get("extracted_text", "")
    contract_type = contract.get("contract_type")
    contract_name = contract.get("name", "Contract")
    
    if not contract_text or len(contract_text) < 50:
        return {"error": "Contract has no content to analyse. Please re-upload the contract file."}
    
    # Parse parties
    parties = contract.get("parties")
    if parties and isinstance(parties, str):
        try:
            parties = json.loads(parties)
        except (json.JSONDecodeError, TypeError):
            parties = None
    
    # Run contract review
    reviewer = ContractReviewService()
    review_result = reviewer.review_contract(
        contract_text=contract_text,
        contract_name=contract_name,
        contract_type=contract_type,
        parties=parties
    )
    
    # Save review to database
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        from datetime import datetime
        cur.execute("""
            UPDATE contracts
            SET review_result = %s::jsonb,
                metadata = COALESCE(metadata, '{}'::jsonb) || 
                           jsonb_build_object('last_reviewed_at', %s, 'review_score', %s),
                updated_at = NOW()
            WHERE id = %s
        """, (
            json.dumps(review_result),
            datetime.now().isoformat(),
            review_result["risk_score"],
            contract_id
        ))
        conn.commit()
    
    # Return structured result for AI to parse
    return {
        "success": True,
        "contract_name": contract_name,
        "risk_score": review_result["risk_score"],
        "risk_level": review_result["risk_level"],
        "total_issues": review_result["total_issues"],
        "summary": review_result["summary"],
        "key_issues": review_result["clauses"][:5],  # Top 5 issues
        "missing_clauses": review_result["missing_clauses"],
        "compliance_status": {
            law: details["status"] 
            for law, details in review_result["compliance"].items()
        },
        "top_recommendations": review_result["recommendations"][:3],
        "full_review": review_result,
        "message": f"✅ Reviewed contract '{contract_name}' — Found {review_result['total_issues']} issue(s). Risk score: {review_result['risk_score']}/100 ({review_result['risk_level']})"
    }


async def _tool_draft_document(tool_input: dict, company_id: str) -> dict:
    """Prepare context for document drafting"""
    doc_type = tool_input.get("doc_type", "")
    requirements = tool_input.get("requirements", "")
    template_id = tool_input.get("template_id")

    # Search relevant laws for this doc type
    search_query = doc_type.replace("_", " ") + " template rule regulation"
    law_results = _search_laws(search_query, None, 8)

    law_context = []
    for src in law_results:
        law_context.append({
            "law_title": src.get("law_title", ""),
            "article": src.get("article", ""),
            "content": src.get("content", "")[:1000]
        })

    # Check for template
    template_data = None
    if template_id:
        with _get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT template_id, name, category, description, template_content
                FROM document_templates
                WHERE template_id = %s
                LIMIT 1
            """, (template_id,))
            row = cur.fetchone()
            if row:
                template_data = dict(row)

    return {
        "doc_type": doc_type,
        "requirements": requirements,
        "relevant_laws": law_context,
        "template": template_data,
        "instruction": f"Draft a '{doc_type}' document as requested: {requirements}. Comply with Indian document drafting regulations. Use [NEEDS INFO] for missing information."
    }


async def _tool_get_company_profile(company_id: str) -> dict:
    """Get company profile with stats"""
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Company info
        cur.execute("""
            SELECT id, name, slug, plan, monthly_quota, used_quota, created_at
            FROM companies WHERE id = %s
        """, (company_id,))
        company = cur.fetchone()
        if not company:
            return {"error": "Company information not found"}

        # Contract stats
        cur.execute("""
            SELECT COUNT(*) as total,
                   COUNT(*) FILTER (WHERE status = 'active') as active,
                   COUNT(*) FILTER (WHERE status = 'expired') as expired
            FROM contracts WHERE company_id = %s AND status != 'deleted'
        """, (company_id,))
        contract_stats = cur.fetchone()

        # Document stats
        cur.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT doc_type) as doc_types
            FROM documents WHERE company_id = %s
        """, (company_id,))
        doc_stats = cur.fetchone()

        # User count
        cur.execute("SELECT COUNT(*) as total FROM users WHERE company_id = %s", (company_id,))
        user_stats = cur.fetchone()

    result = dict(company)
    result["created_at"] = str(result["created_at"]) if result.get("created_at") else None
    result["contracts"] = dict(contract_stats) if contract_stats else {}
    result["documents"] = dict(doc_stats) if doc_stats else {}
    result["users"] = dict(user_stats) if user_stats else {}

    return result


async def _tool_compare_contracts(tool_input: dict, company_id: str) -> dict:
    """Compare multiple contracts side-by-side"""
    contract_ids = tool_input.get("contract_ids", [])
    if len(contract_ids) < 2:
        return {"error": "At least 2 contracts are required for comparison"}

    contracts_data = []
    for cid in contract_ids[:5]:
        contract_data = await _tool_read_contract({"contract_id": cid}, company_id)
        if "error" in contract_data:
            return {"error": f"Cannot read contract {cid}: {contract_data['error']}"}
        contracts_data.append(contract_data["contract"])

    comparison = []
    for c in contracts_data:
        comparison.append({
            "id": str(c.get("id", "")),
            "name": c.get("name", ""),
            "contract_type": c.get("contract_type", ""),
            "parties": c.get("parties"),
            "start_date": c.get("start_date"),
            "end_date": c.get("end_date"),
            "value": c.get("value"),
            "text_excerpt": (c.get("extracted_text") or "")[:5000]
        })

    return {
        "contracts": comparison,
        "count": len(comparison),
        "instruction": "Please compare these contracts in detail. Find differences, inconsistencies, and assess which contract is more beneficial for the company."
    }


async def _tool_crawl_legal_document(tool_input: dict, company_id: str) -> dict:
    """Crawl legal document from URL using CrawlKit"""
    url = tool_input.get("url", "")
    
    try:
        from ..services.crawler import LegalCrawler
        crawler = LegalCrawler()
        crawl_result = crawler.crawl_and_index(url, company_id)
        
        if crawl_result["success"]:
            doc = crawl_result["document"]
            return {
                "success": True,
                "title": doc['title'],
                "url": url,
                "content_length": crawl_result['content_length'],
                "chunks": crawl_result['chunks'],
                "source": doc['source'],
                "content_preview": doc['content'][:2000],
                "full_content": doc['content'],
                "message": f"✅ Crawled successfully!\n\n📄 **{doc['title']}**\n🔗 {url}\n📊 {crawl_result['content_length']:,} characters, {crawl_result['chunks']} chunks\n📁 Source: {doc['source']}"
            }
        else:
            return {"error": f"❌ Crawl failed: {crawl_result['error']}"}
    except Exception as e:
        return {"error": f"❌ Crawl error: {str(e)}"}


async def _tool_edit_and_diff_document(tool_input: dict, company_id: str) -> dict:
    """
    Edit a document and generate diff view.
    This tool will:
    1. Read the document
    2. Analyze it for legal issues
    3. Generate an edited version
    4. Create a diff view
    5. Return both versions for display
    """
    from ..services.diff_utils import generate_inline_diff
    
    document_id = tool_input.get("document_id", "")
    edit_instructions = tool_input.get("edit_instructions", "")
    auto_fix = tool_input.get("auto_fix", True)
    
    if not document_id:
        return {"error": "Missing document_id"}
    
    # Read the document
    with _get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Try documents table first
        cur.execute("""
            SELECT id, name, extracted_text, doc_type FROM documents
            WHERE id::text = %s AND company_id = %s AND deleted_at IS NULL
        """, (document_id, company_id))
        doc = cur.fetchone()
        
        # If not found, try contracts table
        if not doc:
            cur.execute("""
                SELECT id, name, content as extracted_text, contract_type as doc_type FROM contracts
                WHERE id::text = %s AND company_id = %s AND status != 'deleted' AND deleted_at IS NULL
            """, (document_id, company_id))
            doc = cur.fetchone()
    
    if not doc:
        return {"error": f"Document not found with ID: {document_id}"}
    
    original_text = doc.get("extracted_text") or doc.get("content", "")
    doc_name = doc.get("name", "document")
    
    if not original_text:
        return {"error": "Document has no content"}
    
    # Generate edited version using AI
    if _llm_provider_manager:
        try:
            # Build edit prompt
            edit_prompt = f"""You are an AI legal assistant. Please edit the following document to fix legal issues.

TO MAINTAIN QUALITY: Only make reasonable changes, do not change more than 20% of the original content.

ORIGINAL DOCUMENT:
{original_text[:10000]}

EDIT REQUIREMENTS:
{edit_instructions if edit_instructions else "Automatically detect and fix legal issues, add missing clauses according to Indian Law"}

{"AUTOMATIC FIX: Add confidentiality, penalty, and termination clauses if missing." if auto_fix else ""}

Please return the ENTIRE edited document (not just the edits). Keep the original formatting, only modify what is necessary."""

            # Call LLM via shared provider manager
            from ..services.llm_provider import GroqProvider
            provider = GroqProvider()

            result = await provider.chat(
                messages=[{"role": "user", "content": edit_prompt}],
                max_tokens=8192
            )

            edited_text = ""
            for block in result.get("content", []):
                if block.get("type") == "text":
                    edited_text += block.get("text", "")
            
            if not edited_text:
                return {"error": "Could not generate edited version"}
            
            # Generate diff
            diff_result = generate_inline_diff(original_text, edited_text)
            
            # Return result with diff metadata
            return {
                "success": True,
                "document_id": document_id,
                "document_name": doc_name,
                "original": original_text,
                "edited": edited_text,
                "diff_html": diff_result["diff_html"],
                "diff_lines": diff_result["diff_lines"],
                "additions": diff_result["additions"],
                "deletions": diff_result["deletions"],
                "changes_count": diff_result["changes_count"],
                "summary": diff_result["summary"],
                "edit_instructions": edit_instructions or "Automatically review and fix legal issues"
            }
            
        except Exception as e:
            return {"error": f"Error during editing: {str(e)}"}
    else:
        return {"error": "LLM provider not configured"}


# ============================================
# Agent Loop (non-streaming)
# ============================================

async def run_agent(
    question: str,
    company_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    chat_history: Optional[list] = None
) -> dict:
    """
    Agent loop with fast path for simple questions.
    Includes company memory injection.
    """
    # Build system prompt with user context + company memory
    system_prompt = AGENT_SYSTEM_PROMPT
    try:
        user_context = await build_user_context(company_id, user_id)
        if user_context:
            system_prompt = system_prompt + "\n\n" + user_context
        memory_context = await get_company_memory(company_id)
        if memory_context:
            system_prompt = system_prompt + "\n\n" + memory_context
    except Exception as e:
        print(f"[agent] Error loading context/memory for company {company_id}: {e}")

    # Fast path — skip tool loop for simple greetings/acknowledgments
    if is_simple_question(question):
        return await quick_answer(question, chat_history)

    # Follow-up fast path
    if is_followup_question(question, chat_history):
        return await quick_answer(question, chat_history)
    
    messages = []
    if chat_history:
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    all_citations = []
    total_input_tokens = 0
    total_output_tokens = 0
    max_iterations = 25

    for i in range(max_iterations):
        response = await _call_llm_with_tools(messages, TOOLS, system=system_prompt, company_id=company_id)

        usage = response.get("usage", {})
        total_input_tokens += usage.get("input_tokens", 0)
        total_output_tokens += usage.get("output_tokens", 0)

        content_blocks = response.get("content", [])
        stop_reason = response.get("stop_reason", "")

        # Check for tool_use blocks
        tool_uses = [b for b in content_blocks if b.get("type") == "tool_use"]

        if not tool_uses or stop_reason == "end_turn":
            # Final text response — no more tool calls
            if not tool_uses:
                text_parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
                final_text = "".join(text_parts)
                return {
                    "answer": final_text,
                    "citations": all_citations,
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "model": response.get("model", "groq-llama"),
                    "tool_calls_made": i
                }

        # Execute tools and feed results back
        messages.append({"role": "assistant", "content": content_blocks})

        tool_results = []
        for tool_use in tool_uses:
            tool_name = tool_use.get("name", "")
            tool_input = tool_use.get("input", {})
            tool_id = tool_use.get("id", "")

            try:
                result = await execute_tool(tool_name, tool_input, company_id)
            except Exception as e:
                result = {"error": f"Tool execution failed: {str(e)}"}

            # Collect citations from search_law
            if tool_name == "search_law" and "citations" in result:
                all_citations.extend(result["citations"])

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": json.dumps(result, ensure_ascii=False, default=str)[:12000]
            })

        messages.append({"role": "user", "content": tool_results})

    # Max iterations reached
    return {
        "answer": "Sorry, I cannot process this request within the allowed steps. Please try again with a more specific question.",
        "citations": all_citations,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "model": "groq-llama",
        "tool_calls_made": max_iterations
    }


# ============================================
# Agent Loop (streaming with SSE)
# ============================================

TOOL_STATUS_LABELS = {
    "summarize_contract": "📋 Summarising contract...",
    "check_legal_compliance": "✅ Checking compliance...",
    "generate_clause": "✍️ Drafting clause...",
    "edit_and_diff_document": "✏️ Editing and generating diff view..."
}




async def run_agent_stream_final_text(
    question: str,
    company_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    chat_history: Optional[list] = None
) -> AsyncGenerator[str, None]:
    """
    Enhanced streaming: tool calls use non-streaming, final text uses true streaming.
    Fast path for simple questions and follow-ups.
    Includes: company memory, contextual suggestions, inline actions.
    """
    # Build system prompt with company memory + user context
    system_prompt = AGENT_SYSTEM_PROMPT
    try:
        # Inject rich user/company context (like OpenClaw)
        user_context = await build_user_context(company_id, user_id)
        if user_context:
            system_prompt = system_prompt + "\n\n" + user_context
        # Add company memory notes
        memory_context = await get_company_memory(company_id)
        if memory_context:
            system_prompt = system_prompt + "\n\n" + memory_context
    except Exception as e:
        print(f"Error loading context: {e}")

    # Fast path — simple questions skip tools entirely
    if is_simple_question(question):
        messages = []
        if chat_history:
            for msg in chat_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": question})
        
        async for event in _stream_final_text(messages, system=system_prompt, company_id=company_id):
            yield event
        # Emit suggestions for simple/greeting messages
        suggestions = generate_quick_replies(question, "", [])
        yield f"data: {json.dumps({'type': 'suggestions', 'items': suggestions}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    # Follow-up fast path — skip tools for conversational follow-ups
    if is_followup_question(question, chat_history):
        messages = []
        if chat_history:
            for msg in chat_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": question})

        full_text_parts = []
        async for event in _stream_final_text(messages, system=system_prompt, company_id=company_id):
            yield event
            # Collect text for suggestions
            if event.startswith("data: "):
                try:
                    evt = json.loads(event[6:].strip())
                    if evt.get("type") == "delta":
                        full_text_parts.append(evt.get("text", ""))
                except:
                    pass

        answer_text = "".join(full_text_parts)
        suggestions = generate_quick_replies(question, answer_text, [])
        yield f"data: {json.dumps({'type': 'suggestions', 'items': suggestions}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id})}\n\n"
        return

    messages = []
    if chat_history:
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    all_citations = []
    all_tools_used = []
    all_tool_results_data = []  # For inline actions extraction
    max_iterations = 25
    full_response_parts = []

    for iteration in range(max_iterations):
        response = await _call_llm_with_tools(messages, TOOLS, system=system_prompt, company_id=company_id)
        content_blocks = response.get("content", [])

        tool_uses = [b for b in content_blocks if b.get("type") == "tool_use"]

        if not tool_uses:
            # Final iteration — use the text we already got (no double-call!)
            # Send citations
            if all_citations:
                yield f"data: {json.dumps({'type': 'citations', 'citations': all_citations}, ensure_ascii=False)}\n\n"

            # Consulted laws
            seen_laws = set()
            consulted = []
            for c in all_citations:
                key = f"{c.get('source', '')} ({c.get('law_number', '')})"
                if key not in seen_laws:
                    seen_laws.add(key)
                    consulted.append(key)
            if consulted:
                yield f"data: {json.dumps({'type': 'sources', 'laws_consulted': consulted[:15]}, ensure_ascii=False)}\n\n"

            # Use the text from the non-streaming response directly (avoid double API call)
            text_parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
            final_text = "".join(text_parts)

            # Stream it in small chunks for smooth UX
            chunk_size = 15
            for ci in range(0, len(final_text), chunk_size):
                chunk = final_text[ci:ci+chunk_size]
                full_response_parts.append(chunk)
                yield f"data: {json.dumps({'type': 'delta', 'text': chunk}, ensure_ascii=False)}\n\n"

            # Emit inline actions from tool results
            answer_text = "".join(full_response_parts)
            inline_actions = extract_inline_actions(answer_text, all_tools_used, all_tool_results_data)
            if inline_actions:
                yield f"data: {json.dumps({'type': 'inline_actions', 'actions': inline_actions}, ensure_ascii=False)}\n\n"

            # Emit contextual quick reply suggestions
            suggestions = generate_quick_replies(question, answer_text, all_tools_used)
            yield f"data: {json.dumps({'type': 'suggestions', 'items': suggestions}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id, 'citations': all_citations}, ensure_ascii=False)}\n\n"
            return

        # Tool calls — execute
        messages.append({"role": "assistant", "content": content_blocks})

        tool_results = []
        for tool_use in tool_uses:
            tool_name = tool_use.get("name", "")
            tool_input = tool_use.get("input", {})
            tool_id = tool_use.get("id", "")

            # Track tools used
            if tool_name not in all_tools_used:
                all_tools_used.append(tool_name)

            label = TOOL_STATUS_LABELS.get(tool_name, f"🔧 Processing {tool_name}...")
            yield f"data: {json.dumps({'type': 'tool_status', 'tool': tool_name, 'status': 'running', 'label': label}, ensure_ascii=False)}\n\n"

            try:
                result = await execute_tool(tool_name, tool_input, company_id)
            except Exception as e:
                result = {"error": str(e)}

            if tool_name == "search_law" and "citations" in result:
                all_citations.extend(result["citations"])
            
            # Special handling for edit_and_diff_document — emit diff event
            if tool_name == "edit_and_diff_document" and result.get("success"):
                yield f"data: {json.dumps({'type': 'document_edit', 'original': result['original'], 'edited': result['edited'], 'filename': result['document_name'], 'changes': result['summary'], 'diff_html': result['diff_html'], 'additions': result['additions'], 'deletions': result['deletions'], 'changes_count': result['changes_count']}, ensure_ascii=False)}\n\n"

            # Store tool result data for inline actions extraction
            all_tool_results_data.append({"tool": tool_name, "data": result})

            yield f"data: {json.dumps({'type': 'tool_status', 'tool': tool_name, 'status': 'done'}, ensure_ascii=False)}\n\n"

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": json.dumps(result, ensure_ascii=False, default=str)[:12000]
            })

        messages.append({"role": "user", "content": tool_results})

    yield f"data: {json.dumps({'type': 'error', 'message': 'Too many processing steps. Please try again with a more specific question.'}, ensure_ascii=False)}\n\n"
