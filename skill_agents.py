"""
Multi-agent system for concurrent skill evaluation.
"""
import threading
import queue
import json
from typing import Dict, List, Any, Optional, Callable
from datamanager.data_manager import DataManager
from datamanager.data_model import Training


class EvaluationResult:
    """Container for evaluation results from agents."""
    
    def __init__(self, skill_scores: Dict[str, float] = None, 
                 suggestions: List[Dict] = None, 
                 error: Optional[str] = None):
        self.skill_scores = skill_scores or {}
        self.suggestions = suggestions or []
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": "error" if self.error else "success",
            "skill_scores": self.skill_scores,
            "suggestions": self.suggestions,
            **({"error": self.error} if self.error else {})
        }


class SkillEvaluationAgent(threading.Thread):
    """Worker thread for evaluating specific skill aspects."""
    
    def __init__(self, 
                 agent_id: str,
                 input_queue: queue.Queue,
                 output_queue: queue.Queue,
                 data_manager: DataManager,
                 evaluator_func: Callable):
        super().__init__(daemon=True)
        self.agent_id = agent_id
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.dm = data_manager
        self.evaluator_func = evaluator_func
        self.running = True
    
    def run(self):
        """Main agent loop."""
        while self.running:
            try:
                # Get task from queue with timeout to allow checking self.running
                try:
                    task = self.input_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                    
                if task is None:  # Sentinel value to stop the thread
                    break
                    
                user_id = task.get('user_id')
                messages = task.get('messages', [])
                
                try:
                    # Process the task using the provided evaluation function
                    result = self.evaluator_func(user_id, messages, self.dm)
                    self.output_queue.put({
                        'agent_id': self.agent_id,
                        'result': result
                    })
                except Exception as e:
                    self.output_queue.put({
                        'agent_id': self.agent_id,
                        'error': str(e)
                    })
                
                self.input_queue.task_done()
                
            except Exception as e:
                self.output_queue.put({
                    'agent_id': self.agent_id,
                    'error': f"Unexpected error: {str(e)}"
                })
    
    def stop(self):
        """Gracefully stop the agent."""
        self.running = False


class SkillEvaluationOrchestrator:
    """Manages multiple evaluation agents and coordinates their work."""
    
    def __init__(self, data_manager: DataManager, num_workers: int = 3):
        self.dm = data_manager
        self.num_workers = num_workers
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.agents: List[SkillEvaluationAgent] = []
        self.skills = {
            "active_listening": {
                "description": "Ability to actively listen and respond appropriately",
                "keywords": ["i understand", "i hear you", "that makes sense"],
            },
            "empathy": {
                "description": "Ability to show understanding and share feelings",
                "keywords": ["i understand how you feel", "that must be"],
            },
            "clarity": {
                "description": "Clear and concise communication",
                "keywords": ["let me explain", "to clarify"],
            }
        }
        self._init_agents()
    
    def _init_agents(self):
        """Initialize worker agents with different evaluation functions."""
        # Keyword-based evaluator agent
        self._add_agent("keyword_evaluator", self._evaluate_keywords)
        
        # Sentiment analysis agent (placeholder for actual implementation)
        self._add_agent("sentiment_analyzer", self._analyze_sentiment)
        
        # Web research agent
        self._add_agent("web_researcher", self._research_skills)
    
    def _add_agent(self, agent_id: str, evaluator_func: Callable):
        """Add a new agent to the pool."""
        agent = SkillEvaluationAgent(
            agent_id=agent_id,
            input_queue=self.input_queue,
            output_queue=self.output_queue,
            data_manager=self.dm,
            evaluator_func=evaluator_func
        )
        self.agents.append(agent)
        agent.start()
    
    def evaluate_skills(self, user_id: int, messages: List[Dict]) -> Dict[str, Any]:
        """
        Evaluate user skills using multiple agents.
        
        Args:
            user_id: ID of the user to evaluate
            messages: List of message dicts with 'role' and 'content' keys
            
        Returns:
            Dictionary containing combined evaluation results
        """
        # Prepare task for agents
        task = {
            'user_id': user_id,
            'messages': messages
        }
        
        # Submit task to all agents
        for _ in self.agents:
            self.input_queue.put(task)
        
        # Collect results
        results = []
        for _ in self.agents:
            try:
                result = self.output_queue.get(timeout=10.0)  # 10 second timeout
                results.append(result)
            except queue.Empty:
                continue
        
        # Combine results
        return self._combine_results(results)
    
    def _combine_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Combine results from multiple agents."""
        combined_scores = {skill: 0.0 for skill in self.skills}
        all_suggestions = []
        errors = []
        
        for result in results:
            if 'error' in result:
                errors.append(f"{result.get('agent_id')}: {result['error']}")
            else:
                res = result.get('result', {})
                # Sum scores from all agents
                for skill, score in res.get('skill_scores', {}).items():
                    if skill in combined_scores:
                        combined_scores[skill] = min(10.0, combined_scores[skill] + score)
                
                # Collect suggestions
                all_suggestions.extend(res.get('suggestions', []))
        
        # Normalize scores (0-1 range)
        max_score = max(combined_scores.values()) if combined_scores else 1.0
        if max_score > 0:
            combined_scores = {k: v/max(1, max_score) for k, v in combined_scores.items()}
        
        return {
            'status': 'error' if errors else 'success',
            'skill_scores': combined_scores,
            'suggestions': all_suggestions[:5],  # Return top 5 suggestions
            **({'errors': errors} if errors else {})
        }
    
    def stop(self):
        """Stop all agents and clean up resources."""
        for _ in self.agents:
            self.input_queue.put(None)  # Sentinel value to stop agents
        
        for agent in self.agents:
            agent.stop()
            agent.join(timeout=5.0)
    
    # Agent evaluation functions
    def _evaluate_keywords(self, user_id: int, messages: List[Dict], dm: DataManager) -> Dict[str, Any]:
        """Evaluate skills based on keyword matching."""
        scores = {skill: 0.0 for skill in self.skills}
        user_messages = [msg['content'].lower() 
                        for msg in messages 
                        if msg.get('role') == 'user']
        
        for message in user_messages[-10:]:  # Last 10 messages
            for skill, data in self.skills.items():
                for keyword in data["keywords"]:
                    if keyword in message:
                        scores[skill] = min(1.0, scores[skill] + 0.1)
        
        return {
            'skill_scores': scores,
            'suggestions': [f"Consider working on {skill}" for skill, score in scores.items() if score < 0.5]
        }
    
    def _analyze_sentiment(self, user_id: int, messages: List[Dict], dm: DataManager) -> Dict[str, Any]:
        """Analyze sentiment and emotional intelligence."""
        # Placeholder for actual sentiment analysis
        # In a real implementation, this would use a sentiment analysis library
        return {
            'skill_scores': {},
            'suggestions': []
        }
    
    def _research_skills(self, user_id: int, messages: List[Dict], dm: DataManager) -> Dict[str, Any]:
        """Research skills using web search."""
        from langchain_tavily import TavilySearch
        
        search = TavilySearch(max_results=3)
        combined_text = " ".join(
            msg['content'] 
            for msg in messages[-5:]  # Last 5 messages for context
            if msg.get('role') == 'user'
        )
        
        try:
            results = search.invoke({
                "query": f"latest research on social skills {combined_text}"
            })
            
            # Simple analysis of search results
            scores = {skill: 0.0 for skill in self.skills}
            search_text = str(results).lower()
            
            for skill in self.skills:
                skill_terms = [skill] + self.skills[skill]["keywords"]
                if any(term in search_text for term in skill_terms):
                    scores[skill] = 0.3  # Small boost for relevant research
            
            return {
                'skill_scores': scores,
                'suggestions': [
                    "Consider reading latest research on social skills",
                    "New techniques in social skills development might be helpful"
                ]
            }
            
        except Exception as e:
            return {
                'skill_scores': {},
                'suggestions': [],
                'error': str(e)
            }


# Singleton instance for the orchestrator
_orchestrator_instance = None

def get_evaluation_orchestrator(data_manager: DataManager) -> 'SkillEvaluationOrchestrator':
    """Get or create the singleton orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = SkillEvaluationOrchestrator(data_manager)
    return _orchestrator_instance

def stop_evaluation_orchestrator():
    """Stop the orchestrator and clean up resources."""
    global _orchestrator_instance
    if _orchestrator_instance is not None:
        _orchestrator_instance.stop()
        _orchestrator_instance = None
