from fastapi import APIRouter, HTTPException
from langfuse import observe
from app.agents.refill_agent import RefillAgent

router = APIRouter(prefix="/refill", tags=["Refill Intelligence"])

@router.get("/refill-alerts")
@observe(name="get_refill_alerts_api")
def get_alerts():
    try:
        agent = RefillAgent()
        results = agent.check_refills()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Predictive Agent Error: {str(e)}")