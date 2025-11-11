"""
Assessment repository for persistence and history.

Stores assessment results, routing decisions, and policy outcomes in SQLite.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AssessmentRepo:
    """
    Repository for persisting and retrieving assessment data.
    
    Uses SQLite database to store:
    - Assessment results
    - Routing decisions
    - Policy outcomes
    """
    
    def __init__(self, db_path: str = "data/assessments.db"):
        """
        Initialize assessment repository.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    scale TEXT NOT NULL,
                    score REAL NOT NULL,
                    severity TEXT NOT NULL,
                    rigid REAL NOT NULL,
                    route TEXT NOT NULL,
                    flags_json TEXT,
                    preview_text TEXT,
                    assessment_json TEXT,
                    decision_json TEXT,
                    result_json TEXT
                )
            """)
            
            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id_ts 
                ON assessments(user_id, ts DESC)
            """)
            
            conn.commit()
            logger.debug(f"Initialized database at {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
        try:
            yield conn
        finally:
            conn.close()
    
    async def save(
        self,
        user_id: str,
        assessment: Dict[str, Any],
        decision: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save assessment, routing decision, and policy result.
        
        Args:
            user_id: User identifier
            assessment: Assessment result dictionary
            decision: Routing decision dictionary
            result: Policy result dictionary (optional)
        """
        try:
            # Extract fields
            scale = assessment.get("scale", "unknown")
            score = assessment.get("total_score", 0.0)
            severity = assessment.get("severity_level", "unknown")
            rigid = decision.get("rigid_score", 0.0)
            route = decision.get("route", "unknown")
            
            # Extract flags
            flags = assessment.get("flags", {})
            flags_json = json.dumps(flags) if flags else None
            
            # Extract preview text (first 200 chars of response)
            preview_text = None
            if result:
                response = result.get("response", "")
                preview_text = response[:200] if response else None
            
            # Store full JSON for debugging/analysis
            assessment_json = json.dumps(assessment)
            decision_json = json.dumps(decision)
            result_json = json.dumps(result) if result else None
            
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO assessments (
                        user_id, ts, scale, score, severity, rigid, route,
                        flags_json, preview_text,
                        assessment_json, decision_json, result_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    datetime.now().isoformat(),
                    scale,
                    score,
                    severity,
                    rigid,
                    route,
                    flags_json,
                    preview_text,
                    assessment_json,
                    decision_json,
                    result_json
                ))
                conn.commit()
                
            logger.info(f"Saved assessment for user {user_id} (route={route}, severity={severity})")
            
        except Exception as e:
            logger.error(f"Error saving assessment for user {user_id}: {e}", exc_info=True)
            raise
    
    async def history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get assessment history for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of records to return
            
        Returns:
            List of assessment records, most recent first
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        id, user_id, ts, scale, score, severity, 
                        rigid, route, flags_json, preview_text
                    FROM assessments
                    WHERE user_id = ?
                    ORDER BY ts DESC
                    LIMIT ?
                """, (user_id, limit))
                
                rows = cursor.fetchall()
                
                # Convert rows to dictionaries
                history = []
                for row in rows:
                    record = {
                        "id": row["id"],
                        "user_id": row["user_id"],
                        "ts": row["ts"],
                        "scale": row["scale"],
                        "score": row["score"],
                        "severity": row["severity"],
                        "rigid": row["rigid"],
                        "route": row["route"],
                        "preview_text": row["preview_text"],
                    }
                    
                    # Parse flags JSON
                    if row["flags_json"]:
                        try:
                            record["flags"] = json.loads(row["flags_json"])
                        except json.JSONDecodeError:
                            record["flags"] = {}
                    else:
                        record["flags"] = {}
                    
                    history.append(record)
                
                logger.debug(f"Retrieved {len(history)} assessment records for user {user_id}")
                return history
                
        except Exception as e:
            logger.error(f"Error retrieving history for user {user_id}: {e}", exc_info=True)
            return []
    
    async def has_prior_assessment(self, user_id: str) -> bool:
        """
        Check if user has any prior assessments.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user has prior assessments, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM assessments
                    WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                return row["count"] > 0 if row else False
                
        except Exception as e:
            logger.error(f"Error checking prior assessments for user {user_id}: {e}")
            return False

