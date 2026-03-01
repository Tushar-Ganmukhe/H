from fastapi import APIRouter
from langfuse import observe
from app.agents.refill_agent import RefillAgent

router = APIRouter(prefix="/refill", tags=["Refill Intelligence"])


@router.get("/refill-alerts")
@observe(name="get_refill_alerts")
def get_alerts():
    agent = RefillAgent()
    return agent.check_refills()