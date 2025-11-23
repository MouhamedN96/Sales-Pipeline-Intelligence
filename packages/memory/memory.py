"""
Memory Module: Episodic and Semantic Memory for Sales Intelligence Agents
Implements the dual-memory architecture for continuous learning
"""

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


class EpisodicMemory:
    """
    Stores specific deal experiences and interactions.
    Each episode captures: context, action, outcome, success
    """
    
    def __init__(self, db_connection_string: str, capacity: int = 1000):
        self.conn_string = db_connection_string
        self.capacity = capacity
    
    def store(
        self,
        deal_id: str,
        interaction_type: str,
        agent_name: str,
        context: str,
        action_taken: str,
        outcome: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a new episodic memory (interaction) for a deal.
        
        Returns:
            interaction_id: UUID of the stored interaction
        """
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO deal_interactions 
                (deal_id, interaction_type, agent_name, context, action_taken, outcome, success, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (deal_id, interaction_type, agent_name, context, action_taken, outcome, success, Json(metadata or {})))
            
            interaction_id = cur.fetchone()[0]
            conn.commit()
            
            # Enforce capacity: delete oldest if we exceed limit
            self._enforce_capacity(cur, conn)
            
            return str(interaction_id)
        
        finally:
            cur.close()
            conn.close()
    
    def retrieve_by_deal(self, deal_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent interactions for a specific deal.
        """
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT * FROM deal_interactions
                WHERE deal_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (deal_id, limit))
            
            return [dict(row) for row in cur.fetchall()]
        
        finally:
            cur.close()
            conn.close()
    
    def retrieve_similar(self, context: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve similar past interactions based on context.
        In a production system, this would use vector embeddings.
        For MVP, we use simple text matching.
        """
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Simple keyword-based similarity (MVP approach)
            # In production, use pgvector with embeddings
            cur.execute("""
                SELECT * FROM deal_interactions
                WHERE context ILIKE %s OR action_taken ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (f'%{context}%', f'%{context}%', k))
            
            return [dict(row) for row in cur.fetchall()]
        
        finally:
            cur.close()
            conn.close()
    
    def _enforce_capacity(self, cur, conn):
        """Delete oldest interactions if we exceed capacity."""
        cur.execute("""
            DELETE FROM deal_interactions
            WHERE id IN (
                SELECT id FROM deal_interactions
                ORDER BY created_at DESC
                OFFSET %s
            )
        """, (self.capacity,))
        conn.commit()


class SemanticMemory:
    """
    Stores generalized patterns learned across all deals.
    Patterns are aggregated from episodic memories.
    """
    
    def __init__(self, db_connection_string: str):
        self.conn_string = db_connection_string
    
    def record_pattern(
        self,
        context: str,
        action: str,
        success: bool,
        pattern_key: Optional[str] = None,
        impact: Optional[float] = None
    ):
        """
        Record an observation and update the pattern's success rate.
        If pattern doesn't exist, create it.
        """
        if pattern_key is None:
            pattern_key = f"{context}_{action}".replace(" ", "_").lower()
        
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor()
        
        try:
            # Check if pattern exists
            cur.execute("""
                SELECT id, success_count, failure_count, observation_count
                FROM deal_patterns
                WHERE pattern_key = %s
            """, (pattern_key,))
            
            result = cur.fetchone()
            
            if result:
                # Update existing pattern
                pattern_id, success_count, failure_count, obs_count = result
                
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                
                obs_count += 1
                total = success_count + failure_count
                success_rate = success_count / total if total > 0 else 0.0
                
                # Confidence increases with more observations (capped at 1.0)
                confidence_score = min(1.0, obs_count / 100.0)
                
                cur.execute("""
                    UPDATE deal_patterns
                    SET success_count = %s,
                        failure_count = %s,
                        success_rate = %s,
                        confidence_score = %s,
                        observation_count = %s,
                        last_updated_at = NOW()
                    WHERE id = %s
                """, (success_count, failure_count, success_rate, confidence_score, obs_count, pattern_id))
            
            else:
                # Create new pattern
                success_count = 1 if success else 0
                failure_count = 0 if success else 1
                total = success_count + failure_count
                success_rate = success_count / total if total > 0 else 0.0
                confidence_score = 0.01  # Low confidence with just 1 observation
                
                cur.execute("""
                    INSERT INTO deal_patterns
                    (pattern_key, pattern_description, context, action, success_count, failure_count, success_rate, confidence_score, observation_count, learned_rule)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
                """, (
                    pattern_key,
                    f"Pattern for {action} in {context}",
                    context,
                    action,
                    success_count,
                    failure_count,
                    success_rate,
                    confidence_score,
                    f"Early pattern: {action} in {context} context"
                ))
            
            conn.commit()
        
        finally:
            cur.close()
            conn.close()
    
    def get_best_actions(
        self,
        context: str,
        min_confidence: float = 0.5,
        min_success_rate: float = 0.6,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get the best actions for a given context based on learned patterns.
        """
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT * FROM deal_patterns
                WHERE context = %s
                  AND confidence_score >= %s
                  AND success_rate >= %s
                ORDER BY success_rate DESC, confidence_score DESC
                LIMIT %s
            """, (context, min_confidence, min_success_rate, limit))
            
            return [dict(row) for row in cur.fetchall()]
        
        finally:
            cur.close()
            conn.close()
    
    def get_pattern(self, pattern_key: str) -> Optional[Dict[str, Any]]:
        """Get a specific pattern by key."""
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute("""
                SELECT * FROM deal_patterns
                WHERE pattern_key = %s
            """, (pattern_key,))
            
            result = cur.fetchone()
            return dict(result) if result else None
        
        finally:
            cur.close()
            conn.close()
    
    def get_all_patterns(
        self,
        min_confidence: float = 0.3,
        order_by: str = 'success_rate'
    ) -> List[Dict[str, Any]]:
        """
        Get all learned patterns above a confidence threshold.
        """
        conn = psycopg2.connect(self.conn_string)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cur.execute(f"""
                SELECT * FROM deal_patterns
                WHERE confidence_score >= %s
                ORDER BY {order_by} DESC
            """, (min_confidence,))
            
            return [dict(row) for row in cur.fetchall()]
        
        finally:
            cur.close()
            conn.close()


class MemoryAgent:
    """
    Unified memory interface combining episodic and semantic memory.
    This is what agents will use to store and retrieve memories.
    """
    
    def __init__(self, db_connection_string: str, episodic_capacity: int = 1000):
        self.episodic = EpisodicMemory(db_connection_string, episodic_capacity)
        self.semantic = SemanticMemory(db_connection_string)
    
    def remember_interaction(
        self,
        deal_id: str,
        agent_name: str,
        context: str,
        action: str,
        outcome: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store both episodic and semantic memory for an interaction.
        This is the main method agents should call after each action.
        """
        # Store episodic memory
        self.episodic.store(
            deal_id=deal_id,
            interaction_type='agent_action',
            agent_name=agent_name,
            context=context,
            action_taken=action,
            outcome=outcome,
            success=success,
            metadata=metadata
        )
        
        # Update semantic memory (patterns)
        self.semantic.record_pattern(
            context=context,
            action=action,
            success=success
        )
    
    def recall_deal_history(self, deal_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Recall recent interactions for a specific deal."""
        return self.episodic.retrieve_by_deal(deal_id, limit)
    
    def recall_similar_experiences(self, context: str, k: int = 5) -> List[Dict[str, Any]]:
        """Recall similar past experiences."""
        return self.episodic.retrieve_similar(context, k)
    
    def get_learned_strategies(
        self,
        context: str,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Get the best learned strategies for a given context."""
        return self.semantic.get_best_actions(context, min_confidence=min_confidence)
