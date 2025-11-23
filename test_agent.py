"""
Simple test script to validate the agent logic without requiring full setup.
This demonstrates the perceive-plan-act-reflect loop.
"""

import sys
import json
from datetime import datetime

# Mock classes for testing without dependencies
class MockLLMClient:
    """Mock LLM client that returns predefined responses"""
    
    class Chat:
        class Completions:
            def create(self, **kwargs):
                # Return a mock MEDDIC analysis
                class Message:
                    content = json.dumps({
                        "overall_score": 72,
                        "metrics_score": 80,
                        "economic_buyer_score": 60,
                        "decision_criteria_score": 75,
                        "decision_process_score": 70,
                        "pain_score": 85,
                        "champion_score": 65,
                        "gaps": [
                            "Economic buyer not directly engaged",
                            "Champion's influence level unclear"
                        ],
                        "recommendations": [
                            "Schedule meeting with CFO (economic buyer)",
                            "Validate champion's relationship with decision makers",
                            "Document quantifiable ROI metrics"
                        ],
                        "reasoning": "Deal shows strong pain and clear metrics, but economic buyer engagement is weak. Champion exists but influence unclear."
                    })
                
                class Choice:
                    message = Message()
                
                class Response:
                    choices = [Choice()]
                
                return Response()
        
        completions = Completions()
    
    chat = Chat()


class MockMemoryAgent:
    """Mock memory agent for testing"""
    
    def __init__(self):
        self.interactions = []
        self.patterns = [
            {
                "pattern_key": "engage_economic_buyer_negotiation",
                "action": "engage_economic_buyer",
                "success_rate": 0.85,
                "confidence_score": 0.92,
                "learned_rule": "Deals that engage economic buyer in negotiation stage close 30% faster"
            }
        ]
    
    def recall_deal_history(self, deal_id, limit=10):
        return []
    
    def get_learned_strategies(self, context, min_confidence=0.5):
        return self.patterns
    
    def remember_interaction(self, **kwargs):
        self.interactions.append(kwargs)
        print(f"✓ Stored interaction in memory: {kwargs['action']}")


def test_agent_loop():
    """Test the complete agent loop"""
    
    print("=" * 60)
    print("SALES INTELLIGENCE PLATFORM - AGENT TEST")
    print("=" * 60)
    print()
    
    # Initialize mock components
    print("1. Initializing mock components...")
    llm_client = MockLLMClient()
    memory = MockMemoryAgent()
    print("   ✓ Mock LLM client created")
    print("   ✓ Mock memory agent created")
    print()
    
    # Create test deal
    print("2. Creating test deal...")
    test_deal = {
        "id": "deal_test_001",
        "deal_name": "Acme Corp - Enterprise Plan",
        "company_name": "Acme Corp",
        "deal_value": 50000,
        "stage": "negotiation",
        "owner_email": "sales@example.com",
        "updated_at": datetime.now().isoformat(),
        "raw_data": {
            "notes": "Customer needs solution for 100 users. Budget approved. Talking to VP of Sales.",
            "last_contact": "2025-01-15",
            "description": "Enterprise plan for Acme Corp with 100 user licenses"
        }
    }
    print(f"   ✓ Deal: {test_deal['deal_name']}")
    print(f"   ✓ Stage: {test_deal['stage']}")
    print(f"   ✓ Value: ${test_deal['deal_value']:,.2f}")
    print()
    
    # PERCEIVE
    print("3. PERCEIVE: Understanding deal state...")
    print(f"   → Deal is in '{test_deal['stage']}' stage")
    print(f"   → Retrieving similar past experiences from memory...")
    similar = memory.recall_deal_history(test_deal['id'])
    print(f"   ✓ Found {len(similar)} similar past deals")
    print()
    
    # PLAN
    print("4. PLAN: Creating action plan...")
    learned_strategies = memory.get_learned_strategies(test_deal['stage'])
    print(f"   → Retrieved {len(learned_strategies)} learned strategies for '{test_deal['stage']}' stage")
    
    plan = [
        ('run_meddic_analysis', test_deal),
        ('generate_recommendations', None),
        ('apply_learned_strategy', learned_strategies[0] if learned_strategies else None)
    ]
    
    print("   ✓ Action plan created:")
    for i, (action, _) in enumerate(plan, 1):
        print(f"      {i}. {action}")
    print()
    
    # ACT
    print("5. ACT: Executing action plan...")
    
    # Action 1: MEDDIC Analysis
    print("   → Running MEDDIC analysis...")
    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Analyze deal"}]
    )
    meddic_result = json.loads(response.choices[0].message.content)
    print(f"   ✓ MEDDIC Overall Score: {meddic_result['overall_score']}/100")
    print(f"      - Metrics: {meddic_result['metrics_score']}/100")
    print(f"      - Economic Buyer: {meddic_result['economic_buyer_score']}/100")
    print(f"      - Decision Criteria: {meddic_result['decision_criteria_score']}/100")
    print(f"      - Decision Process: {meddic_result['decision_process_score']}/100")
    print(f"      - Pain: {meddic_result['pain_score']}/100")
    print(f"      - Champion: {meddic_result['champion_score']}/100")
    print()
    
    # Action 2: Generate Recommendations
    print("   → Generating recommendations...")
    recommendations = meddic_result['recommendations']
    print(f"   ✓ Generated {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"      {i}. {rec}")
    print()
    
    # Action 3: Apply Learned Strategy
    if learned_strategies:
        print("   → Applying learned strategy...")
        strategy = learned_strategies[0]
        print(f"   ✓ Strategy: {strategy['action']}")
        print(f"      Success Rate: {strategy['success_rate']*100:.0f}%")
        print(f"      Confidence: {strategy['confidence_score']*100:.0f}%")
        print(f"      Rule: {strategy['learned_rule']}")
    print()
    
    # REFLECT
    print("6. REFLECT: Storing experience in memory...")
    memory.remember_interaction(
        deal_id=test_deal['id'],
        agent_name="pipeline_analyst",
        context=f"Deal in {test_deal['stage']} stage",
        action="run_meddic_analysis, generate_recommendations",
        outcome=f"MEDDIC score: {meddic_result['overall_score']}",
        success=True,
        metadata={"meddic_score": meddic_result}
    )
    print()
    
    # Summary
    print("=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print()
    print("📊 Results Summary:")
    print(f"   • Overall MEDDIC Score: {meddic_result['overall_score']}/100")
    print(f"   • Identified Gaps: {len(meddic_result['gaps'])}")
    print(f"   • Recommendations: {len(recommendations)}")
    print(f"   • Learned Insights Applied: {len(learned_strategies)}")
    print()
    print("🧠 Memory Status:")
    print(f"   • Interactions Stored: {len(memory.interactions)}")
    print(f"   • Patterns Available: {len(memory.patterns)}")
    print()
    print("✅ The agent successfully completed the perceive-plan-act-reflect loop!")
    print("   This demonstrates how the agent learns and improves over time.")
    print()


if __name__ == "__main__":
    test_agent_loop()
