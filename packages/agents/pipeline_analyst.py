"""
Pipeline Analyst Agent
Main orchestrator that uses memory and specialized agents to analyze deals.
Implements the perceive -> plan -> act -> reflect loop for continuous learning.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime, timedelta

from .meddic_agent import MEDDICAgent, BANTAgent
from ..memory.memory import MemoryAgent


@dataclass
class DealState:
    """Current state of a deal"""
    deal_id: str
    deal_data: Dict[str, Any]
    stage: str
    days_in_stage: int
    last_activity_days_ago: int
    intent: str  # 'analyze', 'monitor', 'alert', 'recommend'


class PipelineAnalystAgent:
    """
    Main agent that orchestrates deal analysis using memory and specialized agents.
    Implements continuous learning through the perceive-plan-act-reflect cycle.
    """
    
    def __init__(
        self,
        llm_client,
        memory: MemoryAgent,
        model: str = "gpt-4o"
    ):
        """
        Args:
            llm_client: LiteLLM or OpenAI client
            memory: MemoryAgent instance for episodic/semantic memory
            model: LLM model identifier
        """
        self.llm = llm_client
        self.memory = memory
        self.model = model
        self.name = "pipeline_analyst"
        
        # Initialize specialized agents
        self.meddic_agent = MEDDICAgent(llm_client, model)
        self.bant_agent = BANTAgent(llm_client, model)
        
        self.current_plan = []
    
    def analyze_deal(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point: Analyze a deal using the full agentic loop.
        
        Returns:
            Complete analysis with scores, predictions, and recommendations
        """
        
        # PERCEIVE: Understand the current state
        state = self.perceive(deal_data)
        
        # PLAN: Create action plan based on state and memory
        plan = self.plan(state)
        
        # ACT: Execute the plan
        results = self.act(plan, state)
        
        # REFLECT: Store experience and learn
        self.reflect(state, plan, results)
        
        return results
    
    def perceive(self, deal_data: Dict[str, Any]) -> DealState:
        """
        PERCEIVE: Understand the current state of the deal.
        - Retrieve similar past experiences from memory
        - Determine intent (what needs to be done)
        """
        
        deal_id = deal_data.get("id")
        stage = deal_data.get("stage", "unknown")
        
        # Calculate time metrics
        updated_at = deal_data.get("updated_at", datetime.now())
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        last_activity_days_ago = (datetime.now(updated_at.tzinfo) - updated_at).days
        
        # Retrieve deal history from episodic memory
        deal_history = self.memory.recall_deal_history(deal_id, limit=5)
        
        # Determine intent based on deal state
        intent = self._determine_intent(deal_data, deal_history, last_activity_days_ago)
        
        return DealState(
            deal_id=deal_id,
            deal_data=deal_data,
            stage=stage,
            days_in_stage=last_activity_days_ago,  # Simplified for MVP
            last_activity_days_ago=last_activity_days_ago,
            intent=intent
        )
    
    def plan(self, state: DealState) -> List[Tuple[str, Any]]:
        """
        PLAN: Create an action plan based on current state and learned patterns.
        Uses semantic memory to inform planning.
        """
        
        plan = []
        
        # Retrieve learned strategies for this stage
        learned_strategies = self.memory.get_learned_strategies(
            context=state.stage,
            min_confidence=0.3
        )
        
        # Base plan on intent
        if state.intent == 'analyze':
            # Full analysis needed
            plan.append(('run_meddic_analysis', state.deal_data))
            plan.append(('generate_recommendations', None))
        
        elif state.intent == 'monitor':
            # Regular monitoring
            plan.append(('check_health', state.deal_data))
            
            # If we've learned that certain actions work well in this stage, suggest them
            if learned_strategies:
                best_strategy = learned_strategies[0]
                plan.append(('suggest_action', best_strategy))
        
        elif state.intent == 'alert':
            # Deal needs attention
            plan.append(('run_meddic_analysis', state.deal_data))
            plan.append(('create_alert', 'deal_stalled'))
            plan.append(('generate_recovery_plan', learned_strategies))
        
        elif state.intent == 'recommend':
            # User requested recommendations
            plan.append(('run_meddic_analysis', state.deal_data))
            plan.append(('prioritize_actions', learned_strategies))
        
        self.current_plan = plan
        return plan
    
    def act(self, plan: List[Tuple[str, Any]], state: DealState) -> Dict[str, Any]:
        """
        ACT: Execute the plan and collect results.
        """
        
        results = {
            "deal_id": state.deal_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "actions_taken": [],
            "meddic_score": None,
            "recommendations": [],
            "alerts": [],
            "learned_insights": []
        }
        
        for action_type, action_param in plan:
            
            if action_type == 'run_meddic_analysis':
                # Run MEDDIC analysis
                meddic_score = self.meddic_agent.analyze_deal(action_param)
                results["meddic_score"] = {
                    "overall": meddic_score.overall_score,
                    "dimensions": {
                        "metrics": meddic_score.metrics_score,
                        "economic_buyer": meddic_score.economic_buyer_score,
                        "decision_criteria": meddic_score.decision_criteria_score,
                        "decision_process": meddic_score.decision_process_score,
                        "pain": meddic_score.pain_score,
                        "champion": meddic_score.champion_score
                    },
                    "gaps": meddic_score.gaps,
                    "reasoning": meddic_score.reasoning
                }
                results["actions_taken"].append("MEDDIC analysis completed")
            
            elif action_type == 'generate_recommendations':
                # Generate recommendations based on MEDDIC score
                if results["meddic_score"]:
                    meddic_obj = self._reconstruct_meddic_score(results["meddic_score"])
                    recommendations = self.meddic_agent.prioritize_recommendations(meddic_obj, max_recommendations=3)
                    results["recommendations"] = recommendations
                    results["actions_taken"].append("Generated prioritized recommendations")
            
            elif action_type == 'check_health':
                # Quick health check
                health_status = self._assess_deal_health(state)
                results["health_status"] = health_status
                results["actions_taken"].append("Health check completed")
            
            elif action_type == 'create_alert':
                # Create an alert
                alert = self._create_alert(state, action_param)
                results["alerts"].append(alert)
                results["actions_taken"].append(f"Alert created: {action_param}")
            
            elif action_type == 'suggest_action':
                # Suggest action based on learned pattern
                pattern = action_param
                suggestion = {
                    "action": pattern.get("action"),
                    "success_rate": pattern.get("success_rate"),
                    "learned_rule": pattern.get("learned_rule")
                }
                results["learned_insights"].append(suggestion)
                results["actions_taken"].append("Applied learned strategy")
            
            elif action_type == 'prioritize_actions':
                # Prioritize actions using learned patterns
                if action_param:  # learned_strategies
                    top_actions = [
                        {
                            "action": p.get("action"),
                            "success_rate": p.get("success_rate"),
                            "confidence": p.get("confidence_score")
                        }
                        for p in action_param[:3]
                    ]
                    results["learned_insights"] = top_actions
                    results["actions_taken"].append("Prioritized actions using learned patterns")
        
        return results
    
    def reflect(
        self,
        state: DealState,
        plan: List[Tuple[str, Any]],
        results: Dict[str, Any]
    ):
        """
        REFLECT: Store the experience in memory and update patterns.
        This is where learning happens.
        """
        
        # Determine if this interaction was successful
        success = self._evaluate_success(state, results)
        
        # Store episodic memory
        context = f"Deal in {state.stage} stage, {state.days_in_stage} days in stage"
        action = ", ".join([action_type for action_type, _ in plan])
        outcome = f"Analysis completed. MEDDIC score: {results.get('meddic_score', {}).get('overall', 'N/A')}"
        
        self.memory.remember_interaction(
            deal_id=state.deal_id,
            agent_name=self.name,
            context=context,
            action=action,
            outcome=outcome,
            success=success,
            metadata={
                "intent": state.intent,
                "meddic_score": results.get("meddic_score"),
                "recommendations_count": len(results.get("recommendations", []))
            }
        )
    
    def _determine_intent(
        self,
        deal_data: Dict[str, Any],
        deal_history: List[Dict[str, Any]],
        last_activity_days_ago: int
    ) -> str:
        """Determine what needs to be done with this deal."""
        
        stage = deal_data.get("stage", "")
        
        # Alert if deal has stalled
        if last_activity_days_ago > 10 and stage not in ['closed_won', 'closed_lost']:
            return 'alert'
        
        # Analyze if no recent analysis
        if not deal_history or len(deal_history) == 0:
            return 'analyze'
        
        # Monitor if recently analyzed
        last_interaction = deal_history[0] if deal_history else None
        if last_interaction:
            last_interaction_date = last_interaction.get('created_at')
            if isinstance(last_interaction_date, str):
                last_interaction_date = datetime.fromisoformat(last_interaction_date.replace('Z', '+00:00'))
            days_since_analysis = (datetime.now(last_interaction_date.tzinfo) - last_interaction_date).days
            
            if days_since_analysis < 3:
                return 'monitor'
        
        return 'analyze'
    
    def _assess_deal_health(self, state: DealState) -> str:
        """Quick health assessment."""
        if state.last_activity_days_ago > 14:
            return "critical"
        elif state.last_activity_days_ago > 7:
            return "at_risk"
        else:
            return "healthy"
    
    def _create_alert(self, state: DealState, alert_type: str) -> Dict[str, Any]:
        """Create an alert for the deal."""
        return {
            "type": alert_type,
            "severity": "high",
            "message": f"Deal {state.deal_data.get('deal_name')} has stalled for {state.last_activity_days_ago} days",
            "recommended_action": "Schedule follow-up call with decision maker"
        }
    
    def _evaluate_success(self, state: DealState, results: Dict[str, Any]) -> bool:
        """
        Evaluate if the interaction was successful.
        In production, this would be based on user feedback or deal outcomes.
        For MVP, we use heuristics.
        """
        
        # If we generated recommendations, consider it successful
        if results.get("recommendations"):
            return True
        
        # If MEDDIC score is above 60, consider analysis successful
        meddic_score = results.get("meddic_score", {}).get("overall", 0)
        if meddic_score > 60:
            return True
        
        return False
    
    def _reconstruct_meddic_score(self, score_dict: Dict[str, Any]):
        """Helper to reconstruct MEDDICScore from dict."""
        from .meddic_agent import MEDDICScore
        
        return MEDDICScore(
            overall_score=score_dict.get("overall", 0),
            metrics_score=score_dict.get("dimensions", {}).get("metrics", 0),
            economic_buyer_score=score_dict.get("dimensions", {}).get("economic_buyer", 0),
            decision_criteria_score=score_dict.get("dimensions", {}).get("decision_criteria", 0),
            decision_process_score=score_dict.get("dimensions", {}).get("decision_process", 0),
            pain_score=score_dict.get("dimensions", {}).get("pain", 0),
            champion_score=score_dict.get("dimensions", {}).get("champion", 0),
            gaps=score_dict.get("gaps", []),
            recommendations=[],
            reasoning=score_dict.get("reasoning", "")
        )
