# Sales Intelligence Platform

**AI-Powered Sales Pipeline Analysis with Memory and Continuous Learning**

A production-ready, privacy-first platform that uses memory-powered agentic AI to analyze sales deals, predict outcomes, and provide actionable recommendations based on proven sales frameworks (MEDDIC, BANT).

---

## 🎯 What This Does

This platform transforms your CRM data into actionable intelligence by:

1. **Analyzing deals** against proven sales frameworks (MEDDIC, BANT)
2. **Learning from past experiences** to improve recommendations over time
3. **Predicting outcomes** (win probability, time to close)
4. **Alerting proactively** when deals need attention
5. **Recommending actions** based on what has worked historically

### Key Differentiators

- **Memory-Powered Learning**: The agent gets smarter with every deal it analyzes
- **Privacy-First**: Self-hosted, your data never leaves your infrastructure
- **Framework-Based**: Uses proven sales methodologies (MEDDIC, BANT, SPIN)
- **Model-Agnostic**: Works with any LLM (OpenAI, Anthropic, local models via Ollama)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                       │
│              Dashboard + Agent Chat Interface                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ REST API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Agent Backend (FastAPI)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Pipeline Analyst Agent (Orchestrator)        │  │
│  │                                                       │  │
│  │  Perceive → Plan → Act → Reflect Loop                │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                    │
│         ┌───────────────┼───────────────┐                   │
│         │               │               │                   │
│  ┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐            │
│  │   MEDDIC    │ │   BANT    │ │   Memory    │            │
│  │   Agent     │ │   Agent   │ │   System    │            │
│  └─────────────┘ └───────────┘ └──────┬──────┘            │
│                                        │                    │
└────────────────────────────────────────┼────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────┐
              │                          │                  │
       ┌──────▼──────┐          ┌───────▼────────┐  ┌──────▼──────┐
       │  PostgreSQL │          │ Episodic Memory│  │  Semantic   │
       │  + pgvector │          │ (Interactions) │  │   Memory    │
       └─────────────┘          └────────────────┘  │ (Patterns)  │
                                                     └─────────────┘
```

### Core Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Next.js 14 + TypeScript | Dashboard UI and agent chat |
| **Agent Backend** | FastAPI + Python | REST API and agent orchestration |
| **Pipeline Analyst** | Custom Agent | Main orchestrator (perceive-plan-act-reflect) |
| **MEDDIC Agent** | LLM-powered | Analyzes deals against MEDDIC framework |
| **BANT Agent** | LLM-powered | Qualifies deals using BANT |
| **Memory System** | PostgreSQL | Dual memory (episodic + semantic) |
| **Database** | PostgreSQL 16 + pgvector | Stores deals, interactions, patterns |
| **ML Predictions** | MindsDB | Win probability, time-to-close forecasting |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key (or other LLM provider)
- (Optional) Composio API key for CRM integrations

### 1. Clone and Configure

```bash
git clone <repository-url>
cd sales-intelligence-platform

# Create .env file
cat > .env << EOF
# Database
DB_PASSWORD=your_secure_password

# LLM Configuration
OPENAI_API_KEY=sk-your-openai-key
LLM_MODEL=gpt-4o

# Optional: Composio for CRM integrations
COMPOSIO_API_KEY=your_composio_key
COMPOSIO_USER_ID=default
EOF
```

### 2. Start the Platform

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- MindsDB (port 47334)
- Agent Backend API (port 8000)
- Frontend Dashboard (port 3000)

### 3. Initialize the Database

The database schema is automatically applied on first startup.

### 4. Access the Platform

- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📖 Usage

### Analyze a Deal

```bash
curl -X POST http://localhost:8000/api/deals/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "deal_id": "deal_123",
    "deal_name": "Acme Corp - Enterprise Plan",
    "company_name": "Acme Corp",
    "deal_value": 50000,
    "stage": "negotiation",
    "owner_email": "sales@example.com",
    "raw_data": {
      "notes": "Customer needs solution for 100 users. Budget approved. Talking to VP of Sales.",
      "last_contact": "2025-01-15"
    }
  }'
```

**Response:**

```json
{
  "deal_id": "deal_123",
  "analysis_timestamp": "2025-01-20T10:30:00",
  "meddic_score": {
    "overall": 72,
    "dimensions": {
      "metrics": 80,
      "economic_buyer": 60,
      "decision_criteria": 75,
      "decision_process": 70,
      "pain": 85,
      "champion": 65
    },
    "gaps": [
      "Economic buyer not directly engaged",
      "Champion's influence level unclear"
    ],
    "reasoning": "Deal shows strong pain and clear metrics, but economic buyer engagement is weak..."
  },
  "recommendations": [
    "Schedule meeting with CFO (economic buyer)",
    "Validate champion's relationship with decision makers",
    "Document quantifiable ROI metrics"
  ],
  "alerts": [],
  "learned_insights": [
    {
      "action": "engage_economic_buyer",
      "success_rate": 0.85,
      "learned_rule": "Deals that engage economic buyer in negotiation stage close 30% faster"
    }
  ],
  "actions_taken": [
    "MEDDIC analysis completed",
    "Generated prioritized recommendations",
    "Applied learned strategy"
  ]
}
```

### View Deal History (Episodic Memory)

```bash
curl http://localhost:8000/api/deals/deal_123/history?limit=5
```

### View Learned Patterns (Semantic Memory)

```bash
curl http://localhost:8000/api/patterns?context=negotiation&min_confidence=0.5
```

### Get Memory Statistics

```bash
curl http://localhost:8000/api/memory/stats
```

---

## 🧠 How the Agent Learns

The platform implements a **dual-memory architecture** inspired by human cognition:

### 1. Episodic Memory (Specific Experiences)

Stores every interaction with a deal:
- What was the context? (stage, days in stage, last activity)
- What action did the agent take? (MEDDIC analysis, recommendation)
- What was the outcome? (score, user feedback)
- Was it successful?

**Example:**
```json
{
  "deal_id": "deal_123",
  "context": "Deal in negotiation stage, 15 days in stage",
  "action": "run_meddic_analysis, generate_recommendations",
  "outcome": "MEDDIC score: 72. Recommended engaging economic buyer.",
  "success": true
}
```

### 2. Semantic Memory (Generalized Patterns)

Learns patterns across all deals:
- "Deals with an internal champion close 85% of the time"
- "Engaging the economic buyer in qualification stage increases win rate by 35%"
- "Deals that stall for 10+ days in negotiation have 45% recovery rate with proactive follow-up"

**Example:**
```json
{
  "pattern_key": "has_champion_all_stages",
  "success_rate": 0.85,
  "confidence_score": 0.92,
  "observation_count": 120,
  "learned_rule": "Deals with an internal champion close 85% of the time, 20% faster than average"
}
```

### 3. Continuous Improvement

The agent improves over time:
- **Session 1**: Applies generic MEDDIC framework
- **Session 10**: Notices patterns specific to your sales process
- **Session 50**: Provides highly personalized recommendations based on what works for YOUR team

---

## 🔧 Configuration

### LLM Models

The platform is **model-agnostic**. Change the model in `.env`:

```bash
# OpenAI
LLM_MODEL=gpt-4o

# Anthropic Claude
LLM_MODEL=anthropic/claude-3-5-sonnet-20240620

# Local model via Ollama
LLM_MODEL=ollama/llama3

# Groq (for speed)
LLM_MODEL=groq/llama3-70b-8192
```

### Memory Capacity

Adjust episodic memory capacity in `main.py`:

```python
memory_agent = MemoryAgent(DATABASE_URL, episodic_capacity=1000)  # Keep last 1000 interactions
```

### Framework Selection

Enable/disable frameworks in the agent initialization:

```python
# Use MEDDIC only
pipeline_analyst = PipelineAnalystAgent(
    llm_client=llm_client,
    memory=memory_agent,
    frameworks=['meddic']
)

# Use both MEDDIC and BANT
pipeline_analyst = PipelineAnalystAgent(
    llm_client=llm_client,
    memory=memory_agent,
    frameworks=['meddic', 'bant']
)
```

---

## 🔌 Integrations (via Composio)

### Connect to HubSpot

```python
from composio_llamaindex import ComposioToolSet

toolset = ComposioToolSet(api_key=COMPOSIO_API_KEY)
tools = toolset.get_tools(apps=["HUBSPOT"])

# Pull deals from HubSpot
deals = tools.hubspot_get_deals(user_id="default")
```

### Send Slack Alerts

```python
tools = toolset.get_tools(apps=["SLACK"])

# Send alert when deal stalls
tools.slack_send_message(
    channel="#sales-alerts",
    text="🚨 Deal 'Acme Corp' has stalled for 10 days in negotiation stage"
)
```

---

## 📊 Database Schema

### Core Tables

- **deals**: CRM deal data
- **deal_interactions**: Episodic memory (agent actions and outcomes)
- **deal_patterns**: Semantic memory (learned patterns)
- **framework_scores**: MEDDIC/BANT scores over time
- **predictions**: ML predictions (win probability, time to close)
- **alerts**: Proactive notifications

See `packages/database/schema.sql` for full schema.

---

## 🎨 Customization

### Add a New Sales Framework

1. Create a new agent in `packages/agents/`:

```python
class SPINAgent:
    def analyze_deal(self, deal_data):
        # Implement SPIN (Situation, Problem, Implication, Need-payoff) analysis
        pass
```

2. Register it in `pipeline_analyst.py`:

```python
self.spin_agent = SPINAgent(llm_client, model)
```

3. Add it to the action plan in the `plan()` method.

### Customize Learned Rules

Edit the seed data in `schema.sql` to pre-load your organization's best practices:

```sql
INSERT INTO deal_patterns (pattern_key, learned_rule, success_rate)
VALUES ('custom_rule', 'Your custom rule here', 0.90);
```

---

## 🧪 Testing

### Run Unit Tests

```bash
cd apps/agent-os
pytest tests/
```

### Test the Agent Loop

```python
from agents.pipeline_analyst import PipelineAnalystAgent
from memory.memory import MemoryAgent

# Initialize
memory = MemoryAgent(DATABASE_URL)
agent = PipelineAnalystAgent(llm_client, memory)

# Test analysis
result = agent.analyze_deal({
    "id": "test_deal",
    "deal_name": "Test Deal",
    "company_name": "Test Co",
    "stage": "qualification",
    "deal_value": 10000,
    "raw_data": {"notes": "Initial contact made"}
})

print(result)
```

---

## 📦 Deployment

### Production Deployment

1. **Use environment-specific configs**:
   - Production `.env` with strong passwords
   - Restrict CORS origins in `main.py`

2. **Scale with Docker Swarm or Kubernetes**:
   ```bash
   docker stack deploy -c docker-compose.yml sales_intel
   ```

3. **Add authentication** (e.g., Clerk, Auth0)

4. **Set up monitoring** (Prometheus, Grafana)

### Cloud Deployment

The platform can be deployed on:
- **AWS**: ECS + RDS + S3
- **GCP**: Cloud Run + Cloud SQL
- **Azure**: Container Instances + PostgreSQL

---

## 🤝 Contributing

This is an open-source project. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🆘 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

## 🎯 Roadmap

- [ ] Add support for Salesforce, Pipedrive
- [ ] Implement SPIN and Challenger frameworks
- [ ] Add multi-tenant support
- [ ] Build Chrome extension for inline CRM analysis
- [ ] Add voice interface for sales reps
- [ ] Implement A/B testing for recommendations

---

**Built with ❤️ for sales teams who want AI that actually learns and improves.**
