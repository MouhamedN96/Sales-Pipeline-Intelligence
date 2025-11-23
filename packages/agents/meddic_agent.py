"""
MEDDIC Framework Agent
Analyzes deals against the MEDDIC sales methodology:
- Metrics: Quantifiable value the customer expects
- Economic Buyer: Person who controls the budget
- Decision Criteria: Customer's evaluation criteria
- Decision Process: Their buying process and timeline
- Identify Pain: Business pain being solved
- Champion: Internal advocate for your solution
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json


@dataclass
class MEDDICScore:
    """Structured MEDDIC analysis result"""
    overall_score: int  # 0-100
    metrics_score: int  # 0-100
    economic_buyer_score: int
    decision_criteria_score: int
    decision_process_score: int
    pain_score: int
    champion_score: int
    gaps: List[str]
    recommendations: List[str]
    reasoning: str


class MEDDICAgent:
    """
    Agent specialized in MEDDIC framework analysis.
    Uses LLM to analyze deal data and score each dimension.
    """
    
    def __init__(self, llm_client, model: str = "gpt-4o"):
        """
        Args:
            llm_client: LiteLLM or OpenAI client
            model: Model identifier (e.g., 'gpt-4o', 'anthropic/claude-3-5-sonnet')
        """
        self.llm = llm_client
        self.model = model
        self.name = "meddic_agent"
    
    def analyze_deal(self, deal_data: Dict[str, Any]) -> MEDDICScore:
        """
        Analyze a deal against MEDDIC framework.
        
        Args:
            deal_data: Dict containing deal information from CRM
        
        Returns:
            MEDDICScore with analysis results
        """
        
        # Build the analysis prompt
        prompt = self._build_analysis_prompt(deal_data)
        
        # Call LLM for analysis
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent scoring
            response_format={"type": "json_object"}
        )
        
        # Parse LLM response
        analysis = json.loads(response.choices[0].message.content)
        
        # Convert to MEDDICScore
        return MEDDICScore(
            overall_score=analysis.get("overall_score", 0),
            metrics_score=analysis.get("metrics_score", 0),
            economic_buyer_score=analysis.get("economic_buyer_score", 0),
            decision_criteria_score=analysis.get("decision_criteria_score", 0),
            decision_process_score=analysis.get("decision_process_score", 0),
            pain_score=analysis.get("pain_score", 0),
            champion_score=analysis.get("champion_score", 0),
            gaps=analysis.get("gaps", []),
            recommendations=analysis.get("recommendations", []),
            reasoning=analysis.get("reasoning", "")
        )
    
    def _get_system_prompt(self) -> str:
        """System prompt defining the agent's role and expertise."""
        return """You are a MEDDIC sales framework expert. Your role is to analyze sales deals and score them against the MEDDIC methodology.

MEDDIC Framework:
1. **Metrics** (0-100): Are there quantifiable metrics showing the value this solution will deliver? (ROI, cost savings, revenue increase, time saved)
2. **Economic Buyer** (0-100): Have we identified and engaged the person with budget authority? Are they actively involved?
3. **Decision Criteria** (0-100): Do we understand their evaluation criteria? Are we aligned with their requirements?
4. **Decision Process** (0-100): Do we know their buying process, timeline, and who's involved in the decision?
5. **Identify Pain** (0-100): Have we identified a clear, urgent business pain? Does the customer acknowledge it?
6. **Champion** (0-100): Do we have an internal advocate who will sell on our behalf? Are they influential and motivated?

Scoring Guidelines:
- 80-100: Excellent - This dimension is well-covered
- 60-79: Good - Some information, but could be stronger
- 40-59: Weak - Significant gaps that need attention
- 0-39: Critical - This dimension is missing or very weak

For each deal, provide:
1. A score (0-100) for each MEDDIC dimension
2. An overall score (weighted average)
3. A list of gaps (what's missing or weak)
4. Specific, actionable recommendations to improve weak areas
5. Your reasoning for the scores

Output must be valid JSON with this structure:
{
    "overall_score": 75,
    "metrics_score": 80,
    "economic_buyer_score": 60,
    "decision_criteria_score": 70,
    "decision_process_score": 75,
    "pain_score": 85,
    "champion_score": 70,
    "gaps": ["Economic buyer not actively engaged", "Champion's influence unclear"],
    "recommendations": ["Schedule meeting with CFO (economic buyer)", "Validate champion's relationship with decision makers"],
    "reasoning": "Deal shows strong pain and metrics, but economic buyer engagement is weak..."
}"""
    
    def _build_analysis_prompt(self, deal_data: Dict[str, Any]) -> str:
        """Build the user prompt with deal information."""
        
        # Extract key fields from deal data
        deal_name = deal_data.get("deal_name", "Unknown Deal")
        company = deal_data.get("company_name", "Unknown Company")
        stage = deal_data.get("stage", "Unknown")
        value = deal_data.get("deal_value", 0)
        
        # Get any notes or context from raw_data
        raw_data = deal_data.get("raw_data", {})
        notes = raw_data.get("notes", "No notes available")
        description = raw_data.get("description", "No description")
        
        prompt = f"""Analyze this deal using the MEDDIC framework:

**Deal Information:**
- Deal Name: {deal_name}
- Company: {company}
- Stage: {stage}
- Value: ${value:,.2f}

**Deal Context:**
{description}

**Notes:**
{notes}

**Additional Data:**
{json.dumps(raw_data, indent=2)}

Provide a comprehensive MEDDIC analysis with scores, gaps, and actionable recommendations."""
        
        return prompt
    
    def get_critical_gaps(self, score: MEDDICScore) -> List[str]:
        """
        Identify the most critical gaps (dimensions scoring < 50).
        """
        critical = []
        
        dimensions = {
            "Metrics": score.metrics_score,
            "Economic Buyer": score.economic_buyer_score,
            "Decision Criteria": score.decision_criteria_score,
            "Decision Process": score.decision_process_score,
            "Pain": score.pain_score,
            "Champion": score.champion_score
        }
        
        for dimension, score_value in dimensions.items():
            if score_value < 50:
                critical.append(f"{dimension} (score: {score_value}/100)")
        
        return critical
    
    def prioritize_recommendations(
        self,
        score: MEDDICScore,
        max_recommendations: int = 3
    ) -> List[str]:
        """
        Prioritize recommendations based on which dimensions are weakest.
        Returns top N most important recommendations.
        """
        # In a real implementation, this would use semantic memory
        # to learn which actions have the highest success rate
        
        # For MVP, we prioritize based on score
        dimension_scores = [
            ("Metrics", score.metrics_score),
            ("Economic Buyer", score.economic_buyer_score),
            ("Decision Criteria", score.decision_criteria_score),
            ("Decision Process", score.decision_process_score),
            ("Pain", score.pain_score),
            ("Champion", score.champion_score)
        ]
        
        # Sort by score (lowest first)
        dimension_scores.sort(key=lambda x: x[1])
        
        # Get recommendations for the weakest dimensions
        prioritized = []
        for dimension, _ in dimension_scores[:max_recommendations]:
            for rec in score.recommendations:
                if dimension.lower() in rec.lower():
                    prioritized.append(rec)
                    break
        
        return prioritized[:max_recommendations]


class BANTAgent:
    """
    Agent specialized in BANT framework analysis.
    Budget, Authority, Need, Timeline
    Simpler than MEDDIC, good for early-stage qualification.
    """
    
    def __init__(self, llm_client, model: str = "gpt-4o"):
        self.llm = llm_client
        self.model = model
        self.name = "bant_agent"
    
    def analyze_deal(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a deal against BANT framework.
        Returns a simplified score structure.
        """
        
        prompt = self._build_bant_prompt(deal_data)
        
        response = self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _get_system_prompt(self) -> str:
        return """You are a BANT qualification expert. Analyze deals using the BANT framework:

**BANT Framework:**
1. **Budget** (0-100): Does the prospect have budget allocated? Can they afford our solution?
2. **Authority** (0-100): Are we talking to the decision maker? Do they have authority to buy?
3. **Need** (0-100): Is there a clear, urgent need for our solution?
4. **Timeline** (0-100): Is there a defined timeline for making a decision?

Provide scores, qualification status (qualified/unqualified), and recommendations.

Output JSON:
{
    "overall_score": 75,
    "budget_score": 80,
    "authority_score": 70,
    "need_score": 85,
    "timeline_score": 65,
    "is_qualified": true,
    "gaps": ["Timeline is unclear"],
    "recommendations": ["Confirm budget cycle and decision timeline"],
    "reasoning": "Strong need and budget, but timeline needs clarification..."
}"""
    
    def _build_bant_prompt(self, deal_data: Dict[str, Any]) -> str:
        deal_name = deal_data.get("deal_name", "Unknown")
        company = deal_data.get("company_name", "Unknown")
        stage = deal_data.get("stage", "Unknown")
        value = deal_data.get("deal_value", 0)
        raw_data = deal_data.get("raw_data", {})
        
        return f"""Analyze this deal using BANT:

**Deal:** {deal_name}
**Company:** {company}
**Stage:** {stage}
**Value:** ${value:,.2f}

**Context:** {json.dumps(raw_data, indent=2)}

Provide BANT qualification analysis."""
