"""
Contract Review AI Service (LLM-based)
Uses Ollama to analyze contracts
"""

import os
import json
import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime
from src.services.llm_provider import OllamaProvider

logger = logging.getLogger(__name__)


# System prompt for contract review
REVIEW_SYSTEM_PROMPT = """You are an Indian legal expert with 20 years of experience reviewing contracts.

Analyze the following contract and return a JSON with this structure:

{
  "contract_title": "name of the contract",
  "contract_type": "type of contract (employment/lease/sale/service/...)",
  "parties": ["Party A", "Party B"],
  "risk_score": 0-100 (0=safe, 100=very risky),
  "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
  "summary": "2-3 sentences summary of the contract and main risks",
  "clauses": [
    {
      "clause_number": "Clause X",
      "title": "clause title",
      "content": "verbatim text of the risky part",
      "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
      "risk_score": 0-100,
      "issue": "what is the issue",
      "law_reference": "Section X of Act Y states...",
      "suggestion": "specific suggestion to fix",
      "category": "penalty/liability/ip/dispute/termination/..."
    }
  ],
  "missing_clauses": [
    {
      "clause": "name of missing clause",
      "importance": "HIGH/MEDIUM/LOW",
      "suggestion": "should add clause... as per Section X"
    }
  ],
  "compliance": {
    "indian_contract_act_1872": {"status": "OK/PARTIAL/VIOLATION", "issues": []},
    "companies_act_2013": {"status": "OK/PARTIAL/VIOLATION/N_A", "issues": []},
    "labour_codes_2020": {"status": "OK/PARTIAL/VIOLATION/N_A", "issues": []},
    "consumer_protection_act_2019": {"status": "OK/PARTIAL/VIOLATION/N_A", "issues": []}
  },
  "recommendations": [
    {
      "priority": 1,
      "action": "specific action",
      "reason": "reason, legal citation"
    }
  ]
}

Analysis Rules:
1. Penalty for breach of contract must be reasonable compensation (Section 74, Indian Contract Act).
2. Probation period typically 3-6 months based on Standing Orders/Appointment letter.
3. No statutory minimum for probation salary, but minimum wages must apply (Code on Wages, 2019).
4. Employment contracts must comply with EPF, ESI, Gratuity (Social Security Code 2020).
5. Working hours ≤ 8h/day, 48h/week (Factories Act / OSH Code 2020).
6. Interest rates subject to RBI guidelines and Usurious Loans Act state-level limits.
7. Contracts must have a dispute resolution clause (Arbitration & Conciliation Act 1996).
8. Force majeure (Section 56 Indian Contract Act).
9. Confidentiality clauses must have a specific duration.
10. Intellectual Property rights must be clearly defined (IT Act, Copyright Act, Patents Act).

RETURN ONLY JSON, do not explain further."""


class ContractReviewService:
    """
    Contract Review AI - Uses Ollama LLM for intelligent contract analysis
    """
    
    def __init__(self):
        self.provider = OllamaProvider()
    
    async def review_contract_async(
        self,
        contract_text: str,
        contract_name: str = "",
        contract_type: Optional[str] = None,
        parties: Optional[list] = None
    ) -> Dict:
        """
        Main review function — uses Ollama to analyze contract
        """
        if len(contract_text.strip()) < 50:
            return {
                "success": False,
                "error": "Contract content is too short to analyze"
            }
        
        # Truncate if too long
        max_chars = 100000 
        if len(contract_text) > max_chars:
            contract_text = contract_text[:max_chars] + "\n\n[... content truncated due to length ...]"
        
        # Build user message
        user_message = f"""Review the following contract:

Title: {contract_name or 'Unknown'}
Type: {contract_type or 'Auto-detect'}

---CONTRACT CONTENT---
{contract_text}
---END CONTENT---

Fully analyze all risk categories and return a JSON."""

        try:
            # Call Ollama API
            response = await self.provider.chat(
                system=REVIEW_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
                max_tokens=4096
            )
            
            # Extract JSON from response
            response_text = response["content"][0]["text"].strip()
            
            # Try to parse JSON (Ollama might wrap in ```json blocks)
            if response_text.startswith("```"):
                # Remove markdown code block
                lines = response_text.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith("```") and not in_block:
                        in_block = True
                        continue
                    elif line.startswith("```") and in_block:
                        break
                    elif in_block:
                        json_lines.append(line)
                response_text = "\n".join(json_lines)
            
            review_result = json.loads(response_text)
            review_result["success"] = True
            review_result["ai_model"] = self.provider.model
            
            # Add metadata
            review_result["review_id"] = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            review_result["reviewed_at"] = datetime.now().isoformat()
            review_result["total_issues"] = len(review_result.get("clauses", []))
            
            # Ensure contract_title is set
            if not review_result.get("contract_title"):
                review_result["contract_title"] = contract_name or "Contract"
            
            return review_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama response as JSON: {e}")
            return {
                "success": True,
                "raw_analysis": response_text,
                "parse_error": "AI returned invalid JSON, showing text format",
                "ai_model": self.provider.model,
                "contract_title": contract_name or "Contract",
                "reviewed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Contract review failed: {e}")
            return {
                "success": False,
                "error": f"Analysis error: {str(e)}"
            }
            
    def review_contract(self, *args, **kwargs) -> Dict:
        """Sync wrapper for async method"""
        return asyncio.run(self.review_contract_async(*args, **kwargs))
