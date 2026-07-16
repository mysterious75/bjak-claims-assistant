"""Evaluator - Monitoring and evaluation for AI claims assistant"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class InteractionLog:
    """Log entry for each interaction."""
    timestamp: str
    session_id: str
    user_query: str
    assistant_response: str
    action: str
    response_time_ms: float
    sources_used: int
    success: bool
    error_message: Optional[str] = None


class Evaluator:
    """Monitor and evaluate AI claims assistant performance."""
    
    def __init__(self, logs_dir: str = "./logs"):
        self.logs_dir = logs_dir
        os.makedirs(logs_dir, exist_ok=True)
        self.current_session_logs: List[InteractionLog] = []
    
    def log_interaction(
        self,
        session_id: str,
        user_query: str,
        assistant_response: str,
        action: str,
        response_time_ms: float,
        sources_used: int = 0,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log an interaction."""
        log = InteractionLog(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            user_query=user_query[:500],  # Truncate long queries
            assistant_response=assistant_response[:1000],
            action=action,
            response_time_ms=response_time_ms,
            sources_used=sources_used,
            success=success,
            error_message=error_message
        )
        
        self.current_session_logs.append(log)
        
        # Save to file
        self._save_log(log)
    
    def _save_log(self, log: InteractionLog):
        """Save log to file."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.logs_dir, f"interactions_{date_str}.jsonl")
        
        with open(log_file, "a") as f:
            f.write(json.dumps(asdict(log)) + "\n")
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """Get metrics for current session."""
        if not self.current_session_logs:
            return {"total_interactions": 0}
        
        logs = self.current_session_logs
        response_times = [l.response_time_ms for l in logs]
        
        return {
            "total_interactions": len(logs),
            "success_rate": sum(1 for l in logs if l.success) / len(logs),
            "avg_response_time_ms": sum(response_times) / len(response_times),
            "action_distribution": self._get_action_distribution(logs),
            "total_sources_used": sum(l.sources_used for l in logs)
        }
    
    def _get_action_distribution(self, logs: List[InteractionLog]) -> Dict[str, int]:
        """Get distribution of actions taken."""
        dist = {}
        for log in logs:
            dist[log.action] = dist.get(log.action, 0) + 1
        return dist
    
    def get_daily_metrics(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific day."""
        date = date or datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.logs_dir, f"interactions_{date}.jsonl")
        
        if not os.path.exists(log_file):
            return {"date": date, "total_interactions": 0}
        
        logs = []
        with open(log_file, "r") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        
        if not logs:
            return {"date": date, "total_interactions": 0}
        
        response_times = [l["response_time_ms"] for l in logs]
        
        return {
            "date": date,
            "total_interactions": len(logs),
            "success_rate": sum(1 for l in logs if l["success"]) / len(logs),
            "avg_response_time_ms": sum(response_times) / len(response_times),
            "error_count": sum(1 for l in logs if not l["success"]),
            "action_distribution": self._get_action_distribution_from_dicts(logs)
        }
    
    def _get_action_distribution_from_dicts(self, logs: List[Dict]) -> Dict[str, int]:
        """Get action distribution from dict logs."""
        dist = {}
        for log in logs:
            action = log.get("action", "unknown")
            dist[action] = dist.get(action, 0) + 1
        return dist
    
    def calculate_accuracy(
        self,
        test_cases: List[Dict[str, Any]],
        agent_fn
    ) -> Dict[str, Any]:
        """Calculate accuracy on test cases."""
        correct = 0
        total = len(test_cases)
        errors = []
        
        for i, test in enumerate(test_cases):
            try:
                result = agent_fn(test["input"])
                expected_action = test.get("expected_action")
                expected_keywords = test.get("expected_keywords", [])
                
                # Check action match
                action_match = True
                if expected_action:
                    action_match = result.get("action") == expected_action
                
                # Check keyword presence
                keyword_match = True
                if expected_keywords:
                    response_text = result.get("response", "").lower()
                    keyword_match = any(kw.lower() in response_text for kw in expected_keywords)
                
                if action_match and keyword_match:
                    correct += 1
                else:
                    errors.append({
                        "test_index": i,
                        "input": test["input"],
                        "expected_action": expected_action,
                        "got_action": result.get("action"),
                        "action_match": action_match,
                        "keyword_match": keyword_match
                    })
            except Exception as e:
                errors.append({
                    "test_index": i,
                    "input": test["input"],
                    "error": str(e)
                })
        
        return {
            "accuracy": correct / total if total > 0 else 0,
            "correct": correct,
            "total": total,
            "errors": errors
        }
    
    def detect_anomalies(self, logs: List[Dict]) -> List[Dict]:
        """Detect anomalies in interaction logs."""
        anomalies = []
        
        for i, log in enumerate(logs):
            # Check for slow responses
            if log.get("response_time_ms", 0) > 5000:
                anomalies.append({
                    "type": "slow_response",
                    "index": i,
                    "response_time_ms": log["response_time_ms"],
                    "query": log.get("user_query", "")[:100]
                })
            
            # Check for empty responses
            if not log.get("assistant_response"):
                anomalies.append({
                    "type": "empty_response",
                    "index": i,
                    "query": log.get("user_query", "")[:100]
                })
            
            # Check for errors
            if not log.get("success"):
                anomalies.append({
                    "type": "error",
                    "index": i,
                    "error": log.get("error_message", "Unknown"),
                    "query": log.get("user_query", "")[:100]
                })
        
        return anomalies
    
    def export_report(self, output_path: str = "./logs/evaluation_report.json"):
        """Export evaluation report."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "session_metrics": self.get_session_metrics(),
            "daily_metrics": self.get_daily_metrics(),
            "total_sessions": len(set(l.session_id for l in self.current_session_logs))
        }
        
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        
        return report
