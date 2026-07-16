"""Claims Agent - AI Agent for insurance claims workflow"""

import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from .llm_client import LLMClient
from .rag_engine import RAGEngine
from .document_parser import DocumentParser
from .config_loader import get_config


class ClaimsAgent:
    """AI Agent for managing insurance claims."""
    
    def __init__(self, llm_client: LLMClient, rag_engine: RAGEngine):
        config = get_config()
        claims_config = config.get("claims", {})
        
        self.llm = llm_client
        self.rag = rag_engine
        self.parser = DocumentParser(llm_client)
        
        self.claim_types = claims_config.get("claim_types", ["health", "motor", "life", "travel"])
        self.valid_statuses = claims_config.get("statuses", ["DRAFT", "SUBMITTED", "UNDER_REVIEW", "APPROVED", "REJECTED", "PAID"])
        
        # In-memory storage (demo purposes)
        self.claims: Dict[str, Dict] = {}
        self.conversations: Dict[str, List[Dict]] = {}
    
    def _generate_claim_id(self) -> str:
        """Generate unique claim ID."""
        return f"BJK-{uuid.uuid4().hex[:8].upper()}"
    
    def file_claim(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """File a new insurance claim."""
        claim_id = self._generate_claim_id()
        
        # Validate required fields
        required = ["claim_type", "description", "claimant_name"]
        missing = [f for f in required if f not in user_data or not user_data[f]]
        
        if missing:
            return {
                "success": False,
                "error": f"Missing required fields: {', '.join(missing)}",
                "missing_fields": missing
            }
        
        # Create claim
        claim = {
            "claim_id": claim_id,
            "status": "SUBMITTED",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "claim_type": user_data["claim_type"],
            "claimant_name": user_data["claimant_name"],
            "description": user_data.get("description", ""),
            "amount_claimed": user_data.get("amount_claimed", 0),
            "policy_number": user_data.get("policy_number", ""),
            "documents": user_data.get("documents", []),
            "timeline": [
                {
                    "status": "SUBMITTED",
                    "timestamp": datetime.now().isoformat(),
                    "note": "Claim submitted successfully"
                }
            ]
        }
        
        self.claims[claim_id] = claim
        
        return {
            "success": True,
            "claim_id": claim_id,
            "message": f"Claim {claim_id} submitted successfully",
            "claim": claim
        }
    
    def check_status(self, claim_id: str) -> Dict[str, Any]:
        """Check status of an existing claim."""
        if claim_id not in self.claims:
            return {
                "success": False,
                "error": f"Claim {claim_id} not found"
            }
        
        claim = self.claims[claim_id]
        return {
            "success": True,
            "claim_id": claim_id,
            "status": claim["status"],
            "timeline": claim["timeline"],
            "claim": claim
        }
    
    def ask_faq(self, question: str) -> Dict[str, Any]:
        """Answer FAQ using RAG."""
        result = self.rag.query(question)
        return {
            "success": True,
            "question": question,
            "answer": result["answer"],
            "sources": result.get("sources", [])
        }
    
    def upload_documents(self, claim_id: str, documents: List[Dict]) -> Dict[str, Any]:
        """Upload documents for a claim."""
        if claim_id not in self.claims:
            return {"success": False, "error": f"Claim {claim_id} not found"}
        
        parsed_docs = []
        for doc in documents:
            if "content" in doc and "filename" in doc:
                result = self.parser.parse(doc["content"], doc["filename"])
                parsed_docs.append(result)
        
        self.claims[claim_id]["documents"].extend(parsed_docs)
        self.claims[claim_id]["updated_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "claim_id": claim_id,
            "documents_uploaded": len(parsed_docs),
            "parsed_results": parsed_docs
        }
    
    def escalate_to_human(self, claim_id: str, reason: str) -> Dict[str, Any]:
        """Escalate claim to human agent."""
        if claim_id not in self.claims:
            return {"success": False, "error": f"Claim {claim_id} not found"}
        
        self.claims[claim_id]["status"] = "ESCALATED"
        self.claims[claim_id]["timeline"].append({
            "status": "ESCALATED",
            "timestamp": datetime.now().isoformat(),
            "note": f"Escalated to human: {reason}"
        })
        
        return {
            "success": True,
            "claim_id": claim_id,
            "message": "Claim escalated to human agent. You will be contacted within 24 hours."
        }
    
    def get_tools_description(self) -> str:
        """Return tools description for the agent."""
        return """
Available tools:
1. file_claim - File a new insurance claim
   - Requires: claim_type, claimant_name, description
   - Optional: amount_claimed, policy_number, documents

2. check_status - Check claim status
   - Requires: claim_id

3. ask_faq - Ask insurance FAQ questions
   - Requires: question

4. upload_documents - Upload documents for a claim
   - Requires: claim_id, documents (list of file contents)

5. escalate_to_human - Escalate to human agent
   - Requires: claim_id, reason
"""
    
    def process_message(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """Process user message and decide next action."""
        # Initialize conversation history
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        self.conversations[session_id].append({
            "role": "user",
            "content": message
        })
        
        # Use LLM to decide action
        prompt = f"""You are an insurance claims assistant for BJAK.
Analyze the user message and determine the best action.

{self.get_tools_description()}

User message: "{message}"

Previous context:
{json.dumps(self.conversations[session_id][-3:], indent=2) if self.conversations[session_id] else "None"}

Respond with a JSON object:
{{
    "action": "one of: file_claim, check_status, ask_faq, escalate, respond",
    "parameters": {{}},
    "response": "Your response to the user",
    "needs_info": ["list of missing info needed"]
}}

Only use "respond" if no tool is needed."""
        
        try:
            response = self.llm.generate(prompt, temperature=0.1)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(response)
        except Exception:
            result = {
                "action": "respond",
                "parameters": {},
                "response": "I'm here to help with your insurance claim. Could you please provide more details?",
                "needs_info": []
            }
        
        # Execute action
        action = result.get("action", "respond")
        params = result.get("parameters", {})
        
        if action == "file_claim":
            tool_result = self.file_claim(params)
        elif action == "check_status":
            tool_result = self.check_status(params.get("claim_id", ""))
        elif action == "ask_faq":
            tool_result = self.ask_faq(params.get("question", message))
        elif action == "escalate":
            tool_result = self.escalate_to_human(
                params.get("claim_id", ""),
                params.get("reason", "User requested human agent")
            )
        else:
            tool_result = {"response": result.get("response", "")}
        
        # Update conversation
        assistant_msg = result.get("response", str(tool_result))
        self.conversations[session_id].append({
            "role": "assistant",
            "content": assistant_msg,
            "action": action,
            "tool_result": tool_result
        })
        
        return {
            "action": action,
            "response": assistant_msg,
            "tool_result": tool_result,
            "session_id": session_id
        }
