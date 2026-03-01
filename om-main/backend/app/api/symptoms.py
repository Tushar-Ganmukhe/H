from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.execution_agent import ExecutionAgent

router = APIRouter()


class SymptomRequest(BaseModel):
    symptom: str
    n_results: int = 3
    threshold: float = 0.5


@router.post("/recommend", tags=["symptoms"])
def recommend(req: SymptomRequest):
    """Recommend products for a given symptom using the ExecutionAgent.

    Returns a JSON payload with matches, their scores, price and stock.
    """
    if not req.symptom or not req.symptom.strip():
        raise HTTPException(status_code=400, detail="Please provide a symptom description")

    agent = ExecutionAgent()
    result = agent.recommend_products(req.symptom)

    matches = result.get("matches", [])
    # Respect requested number of results
    matches = matches[: max(0, int(req.n_results))]

    return {
        "found": bool(result.get("found", False)),
        "matches": matches,
        "symptom_categories": result.get("symptom_categories", []),
        "total_matches": result.get("total_matches", 0),
    }
