from typing import Dict, Any
from fastapi import Depends, HTTPException
from tradingagents.portfolio.supabase_client import SupabaseClient
from tradingagents.portfolio.exceptions import PortfolioError
import logging

logger = logging.getLogger("agent_os")

async def get_current_user():
    # V1 (Single Tenant): Just return a hardcoded user/workspace ID
    # V2 (Multi-Tenant): Decode the JWT using supabase-py and return auth.uid()
    return {"user_id": "tenant_001", "role": "admin"}

def get_db_client() -> SupabaseClient:
    try:
        return SupabaseClient.get_instance()
    except PortfolioError as e:
        logger.warning(f"Database not available: {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"Portfolio database not configured. Set SUPABASE_CONNECTION_STRING in .env. Error: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating DB client: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Database connection error: {e}"
        )
