"""
Sales Intelligence Platform - Agent Backend
FastAPI server that exposes the agentic system via REST API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import sys
from datetime import datetime

# Add packages to path
sys.path.append('/app/packages')

from memory.memory import MemoryAgent
from agents.pipeline_analyst import PipelineAnalystAgent

# Initialize FastAPI app
app = FastAPI(
    title="Sales Intelligence Platform API",
    description="AI-powered sales pipeline analysis with memory and learning",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sales_user:changeme123@localhost:5432/sales_intelligence")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize LLM client
try:
    from openai import OpenAI
    llm_client = OpenAI(api_key=OPENAI_API_KEY)
except ImportError:
    print("WARNING: OpenAI library not installed. Install with: pip install openai")
    llm_client = None

# Initialize memory and agent
memory_agent = MemoryAgent(DATABASE_URL, episodic_capacity=1000)

if llm_client:
    pipeline_analyst = PipelineAnalystAgent(
        llm_client=llm_client,
        memory=memory_agent,
        model=LLM_MODEL
    )
else:
    pipeline_analyst = None


# ============================================================================
# Pydantic Models
# ============================================================================

class DealAnalysisRequest(BaseModel):
    deal_id: str
    deal_name: str
    company_name: str
    deal_value: float
    stage: str
    owner_email: str
    raw_data: Optional[Dict[str, Any]] = {}


class DealAnalysisResponse(BaseModel):
    deal_id: str
    analysis_timestamp: str
    meddic_score: Optional[Dict[str, Any]]
    recommendations: List[str]
    alerts: List[Dict[str, Any]]
    learned_insights: List[Dict[str, Any]]
    actions_taken: List[str]


class MemoryQuery(BaseModel):
    deal_id: str
    limit: int = 10


class PatternQuery(BaseModel):
    context: str
    min_confidence: float = 0.5


# ============================================================================
# Health Check
# ============================================================================

@app.get("/")
def root():
    return {
        "service": "Sales Intelligence Platform",
        "status": "running",
        "version": "1.0.0",
        "agent_ready": pipeline_analyst is not None
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    
    # Check database connection
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "agent": "ready" if pipeline_analyst else "not initialized",
        "llm_model": LLM_MODEL
    }


# ============================================================================
# Deal Analysis Endpoints
# ============================================================================

@app.post("/api/deals/analyze", response_model=DealAnalysisResponse)
async def analyze_deal(request: DealAnalysisRequest):
    """
    Analyze a deal using the Pipeline Analyst Agent.
    This triggers the full perceive-plan-act-reflect loop.
    """
    
    if not pipeline_analyst:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check OPENAI_API_KEY.")
    
    try:
        # Convert request to deal_data dict
        deal_data = {
            "id": request.deal_id,
            "deal_name": request.deal_name,
            "company_name": request.company_name,
            "deal_value": request.deal_value,
            "stage": request.stage,
            "owner_email": request.owner_email,
            "raw_data": request.raw_data,
            "updated_at": datetime.now().isoformat()
        }
        
        # Run analysis
        results = pipeline_analyst.analyze_deal(deal_data)
        
        return DealAnalysisResponse(**results)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/deals/{deal_id}/history")
async def get_deal_history(deal_id: str, limit: int = 10):
    """
    Retrieve episodic memory (interaction history) for a deal.
    """
    
    try:
        history = memory_agent.recall_deal_history(deal_id, limit=limit)
        return {
            "deal_id": deal_id,
            "interactions": history,
            "count": len(history)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@app.get("/api/deals/{deal_id}/similar")
async def get_similar_deals(deal_id: str, context: str, k: int = 5):
    """
    Find similar past deals based on context.
    """
    
    try:
        similar = memory_agent.recall_similar_experiences(context, k=k)
        return {
            "query_context": context,
            "similar_experiences": similar,
            "count": len(similar)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar deals: {str(e)}")


# ============================================================================
# Memory & Learning Endpoints
# ============================================================================

@app.get("/api/patterns")
async def get_learned_patterns(context: Optional[str] = None, min_confidence: float = 0.3):
    """
    Retrieve learned patterns (semantic memory).
    """
    
    try:
        if context:
            patterns = memory_agent.semantic.get_best_actions(
                context=context,
                min_confidence=min_confidence
            )
        else:
            patterns = memory_agent.semantic.get_all_patterns(min_confidence=min_confidence)
        
        return {
            "patterns": patterns,
            "count": len(patterns),
            "context_filter": context
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve patterns: {str(e)}")


@app.get("/api/patterns/{pattern_key}")
async def get_pattern_detail(pattern_key: str):
    """
    Get details of a specific learned pattern.
    """
    
    try:
        pattern = memory_agent.semantic.get_pattern(pattern_key)
        
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        return pattern
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pattern: {str(e)}")


@app.get("/api/memory/stats")
async def get_memory_stats():
    """
    Get statistics about the agent's memory.
    """
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Count episodic memories
        cur.execute("SELECT COUNT(*) as count FROM deal_interactions")
        episodic_count = cur.fetchone()['count']
        
        # Count semantic patterns
        cur.execute("SELECT COUNT(*) as count FROM deal_patterns WHERE confidence_score >= 0.3")
        pattern_count = cur.fetchone()['count']
        
        # Get top patterns
        cur.execute("""
            SELECT pattern_key, success_rate, confidence_score, observation_count
            FROM deal_patterns
            WHERE confidence_score >= 0.5
            ORDER BY success_rate DESC, confidence_score DESC
            LIMIT 5
        """)
        top_patterns = [dict(row) for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        return {
            "episodic_memories": episodic_count,
            "learned_patterns": pattern_count,
            "top_patterns": top_patterns
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory stats: {str(e)}")


# ============================================================================
# Integration Endpoints (Composio)
# ============================================================================

@app.post("/api/integrations/crm/sync")
async def sync_from_crm(background_tasks: BackgroundTasks):
    """
    Trigger CRM sync (HubSpot, Salesforce).
    In production, this would use Composio to pull deals.
    """
    
    # This is a placeholder - actual implementation would use Composio
    return {
        "status": "sync_initiated",
        "message": "CRM sync started in background. This is a placeholder endpoint."
    }


@app.post("/api/integrations/slack/alert")
async def send_slack_alert(deal_id: str, message: str):
    """
    Send alert to Slack.
    In production, this would use Composio Slack integration.
    """
    
    # Placeholder - actual implementation would use Composio
    return {
        "status": "alert_sent",
        "deal_id": deal_id,
        "message": "This is a placeholder. Implement with Composio Slack tool."
    }


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
