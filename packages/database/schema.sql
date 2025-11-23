-- Sales Intelligence Platform Database Schema
-- PostgreSQL 16 with pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================================================
-- CORE TABLES: Deal Management
-- ============================================================================

CREATE TABLE deals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL, -- CRM deal ID (HubSpot, Salesforce)
    company_name VARCHAR(255) NOT NULL,
    deal_name VARCHAR(255) NOT NULL,
    deal_value DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    stage VARCHAR(100) NOT NULL, -- e.g., 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost'
    probability INTEGER CHECK (probability >= 0 AND probability <= 100),
    expected_close_date DATE,
    actual_close_date DATE,
    owner_name VARCHAR(255),
    owner_email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    crm_source VARCHAR(50) NOT NULL, -- 'hubspot', 'salesforce', 'pipedrive'
    raw_data JSONB, -- Store full CRM payload for reference
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_deals_stage ON deals(stage);
CREATE INDEX idx_deals_owner_email ON deals(owner_email);
CREATE INDEX idx_deals_expected_close_date ON deals(expected_close_date);
CREATE INDEX idx_deals_external_id ON deals(external_id);

-- ============================================================================
-- EPISODIC MEMORY: Deal Interactions
-- ============================================================================

CREATE TABLE deal_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    interaction_type VARCHAR(50) NOT NULL, -- 'agent_analysis', 'user_feedback', 'stage_change', 'recommendation'
    agent_name VARCHAR(100), -- Which agent performed the action (e.g., 'meddic_agent', 'pipeline_analyst')
    context TEXT NOT NULL, -- What was the state when this happened
    action_taken TEXT NOT NULL, -- What action was performed
    outcome TEXT, -- Result of the action
    success BOOLEAN, -- Was this action successful/helpful?
    metadata JSONB, -- Additional structured data (scores, predictions, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_interactions_deal_id ON deal_interactions(deal_id);
CREATE INDEX idx_interactions_type ON deal_interactions(interaction_type);
CREATE INDEX idx_interactions_created_at ON deal_interactions(created_at DESC);

-- ============================================================================
-- SEMANTIC MEMORY: Learned Patterns
-- ============================================================================

CREATE TABLE deal_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_key VARCHAR(255) UNIQUE NOT NULL, -- e.g., 'has_champion_qualification_stage'
    pattern_description TEXT NOT NULL,
    context VARCHAR(100) NOT NULL, -- e.g., 'qualification', 'negotiation', 'all_stages'
    action VARCHAR(255) NOT NULL, -- The action this pattern relates to
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5, 4), -- Calculated: success_count / (success_count + failure_count)
    confidence_score DECIMAL(5, 4), -- How confident are we in this pattern (based on sample size)
    avg_impact DECIMAL(10, 2), -- Average impact on deal value or close time
    learned_rule TEXT, -- Human-readable rule derived from this pattern
    metadata JSONB, -- Additional pattern-specific data
    first_observed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    observation_count INTEGER DEFAULT 0
);

CREATE INDEX idx_patterns_context ON deal_patterns(context);
CREATE INDEX idx_patterns_success_rate ON deal_patterns(success_rate DESC);

-- ============================================================================
-- FRAMEWORK SCORES: MEDDIC, BANT, etc.
-- ============================================================================

CREATE TABLE framework_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    framework VARCHAR(50) NOT NULL, -- 'meddic', 'bant', 'spin', 'challenger'
    overall_score INTEGER CHECK (overall_score >= 0 AND overall_score <= 100),
    dimension_scores JSONB NOT NULL, -- e.g., {"metrics": 80, "economic_buyer": 60, ...}
    gaps JSONB, -- Array of identified gaps
    recommendations JSONB, -- Array of recommended actions
    agent_reasoning TEXT, -- Why did the agent score it this way?
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) -- Which agent created this score
);

CREATE INDEX idx_framework_scores_deal_id ON framework_scores(deal_id);
CREATE INDEX idx_framework_scores_framework ON framework_scores(framework);
CREATE INDEX idx_framework_scores_created_at ON framework_scores(created_at DESC);

-- ============================================================================
-- PREDICTIONS: Win Probability, Time to Close
-- ============================================================================

CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    prediction_type VARCHAR(50) NOT NULL, -- 'win_probability', 'time_to_close', 'deal_value'
    predicted_value DECIMAL(10, 2) NOT NULL,
    confidence_interval_lower DECIMAL(10, 2),
    confidence_interval_upper DECIMAL(10, 2),
    confidence_score DECIMAL(5, 4), -- 0.0 to 1.0
    model_used VARCHAR(100), -- 'mindsdb_win_predictor', 'semantic_memory_pattern'
    features_used JSONB, -- What features went into this prediction
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_predictions_deal_id ON predictions(deal_id);
CREATE INDEX idx_predictions_type ON predictions(prediction_type);
CREATE INDEX idx_predictions_created_at ON predictions(created_at DESC);

-- ============================================================================
-- ALERTS: Proactive Notifications
-- ============================================================================

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deal_id UUID NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL, -- 'deal_stalled', 'high_risk', 'opportunity', 'missing_info'
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    recommended_action TEXT,
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP WITH TIME ZONE,
    sent_via VARCHAR(50), -- 'slack', 'email', 'in_app'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(255)
);

CREATE INDEX idx_alerts_deal_id ON alerts(deal_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_is_sent ON alerts(is_sent);

-- ============================================================================
-- USERS: Basic user management (optional, for multi-tenant)
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user', -- 'admin', 'user', 'viewer'
    crm_user_id VARCHAR(255), -- Link to CRM user
    preferences JSONB, -- User-specific settings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);

-- ============================================================================
-- FUNCTIONS: Auto-update timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_deals_updated_at
    BEFORE UPDATE ON deals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS: Useful aggregations
-- ============================================================================

-- View: Deal health summary
CREATE VIEW deal_health_summary AS
SELECT 
    d.id,
    d.deal_name,
    d.company_name,
    d.stage,
    d.deal_value,
    d.expected_close_date,
    p.predicted_value as win_probability,
    fs.overall_score as latest_meddic_score,
    COUNT(DISTINCT a.id) as open_alerts_count,
    MAX(di.created_at) as last_interaction_at
FROM deals d
LEFT JOIN predictions p ON d.id = p.deal_id AND p.prediction_type = 'win_probability'
LEFT JOIN framework_scores fs ON d.id = fs.deal_id AND fs.framework = 'meddic'
LEFT JOIN alerts a ON d.id = a.deal_id AND a.is_sent = FALSE
LEFT JOIN deal_interactions di ON d.id = di.deal_id
WHERE d.is_active = TRUE
GROUP BY d.id, d.deal_name, d.company_name, d.stage, d.deal_value, d.expected_close_date, p.predicted_value, fs.overall_score;

-- ============================================================================
-- SEED DATA: Example patterns (optional, for demo)
-- ============================================================================

INSERT INTO deal_patterns (pattern_key, pattern_description, context, action, success_count, failure_count, success_rate, confidence_score, learned_rule)
VALUES 
    ('has_champion_all_stages', 'Deals with an identified internal champion', 'all_stages', 'identify_champion', 85, 15, 0.85, 0.92, 'Deals with an internal champion close 85% of the time, 20% faster than average'),
    ('missing_economic_buyer_qualification', 'Deals in qualification stage without economic buyer engagement', 'qualification', 'engage_economic_buyer', 12, 38, 0.24, 0.78, 'Deals that fail to engage the economic buyer in qualification stage have only 24% win rate'),
    ('stalled_10_days_negotiation', 'Deals in negotiation stage with no activity for 10+ days', 'negotiation', 'send_follow_up', 45, 55, 0.45, 0.85, 'Deals that stall for 10+ days in negotiation have 45% recovery rate with proactive follow-up');
