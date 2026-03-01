import sys, os
import pytest
import asyncio
import pandas as pd

# make sure backend module is on sys.path for imports when pytest runs from workspace root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.agents.decision_agent import DecisionAgent
from backend.app.services.user_service import UserService


def _run_test_logic():
    da = DecisionAgent()

    # register a user with a random phone to avoid collisions in repeated runs
    import uuid
    phone = "555" + uuid.uuid4().hex[:6]
    reg = UserService.register_user("PendingTester", phone, None, "pw", None, "user")
    assert reg.get("success"), "user registration failed in test"
    session = reg.get("user", {}).get("id")
    assert session, "Session ID should not be None"

    # ask to order a medicine but omit the quantity requirement
    first_msg = "Order Cystinol akut"
    parsed1 = {
        "intent": "order",
        "product_name": "Cystinol akut",
        "quantity": None,
        "missing": "quantity",
        "symptom": None,
        "friendly_response": ""
    }
    resp1 = asyncio.run(da.decide(parsed1, raw_message=first_msg, session_id=session))
    assert "Cystinol" in resp1.get("message", ""), "Initial prompt should reference Cystinol"

    # now send only a number as the user's message
    second_msg = "5"
    parsed2 = {
        "intent": "order",
        "product_name": None,
        "quantity": 5,
        "missing": None,
        "symptom": None,
        "friendly_response": ""
    }
    resp2 = asyncio.run(da.decide(parsed2, raw_message=second_msg, session_id=session))

    # verify the final order used the correct product (or reported stock error for it)
    msg2 = resp2.get("message", "")
    assert "Cystinol" in msg2 or "Only" in msg2, "Quantity reply should reference Cystinol or show stock error"
    if "Order Confirmed" in msg2:
        assert "Cystinol" in msg2


# additional scenario: quantity reply that includes wrong product name

def _run_misleading_product():
    da = DecisionAgent()
    import uuid
    phone = "555" + uuid.uuid4().hex[:6]
    reg = UserService.register_user("PendingTester", phone, None, "pw", None, "user")
    session = reg.get("user", {}).get("id")

    # prompt for NORSAN but LLM later mis-parses the follow-up quantity as Nurofen
    first_msg = "Order NORSAN Omega-3 Vegan"
    parsed1 = {
        "intent": "order",
        "product_name": "NORSAN Omega-3 Vegan",
        "quantity": None,
        "missing": "quantity",
        "symptom": None,
        "friendly_response": ""
    }
    resp1 = asyncio.run(da.decide(parsed1, raw_message=first_msg, session_id=session))
    assert "NORSAN" in resp1.get("message", "")

    # now the user replies with a number but parser wrongly assigns Nurofen
    second_msg = "1"
    parsed2 = {
        "intent": "order",
        "product_name": "Nurofen 200 mg Schmelztabletten Lemon",  # incorrect parse
        "quantity": 1,
        "missing": None,
        "symptom": None,
        "friendly_response": ""
    }
    resp2 = asyncio.run(da.decide(parsed2, raw_message=second_msg, session_id=session))

    # we expect the decision agent to ignore the wrong name and use pending product
    assert "NORSAN" in resp2.get("message", ""), "Should have ordered NORSAN despite parser mistake"
    assert "Order Confirmed" in resp2.get("message", "")


def _run_complex_history():
    """Simulate a user ordering Nurofen then later Kijimea and replying with
    just numbers; ensure we always attach the correct product to the quantity."""
    da = DecisionAgent()
    import uuid
    phone = "555" + uuid.uuid4().hex[:6]
    reg = UserService.register_user("PendingTester", phone, None, "pw", None, "user")
    session = reg.get("user", {}).get("id")

    # first order some product that has sufficient stock (avoid running out)
    from backend.app.services.product_service import ProductService
    ps = ProductService()
    # try Cystinol first or any with >=10 units
    prod = ps.get_product_by_name("Cystinol akut")
    if not prod or prod.get("stock",0) < 10:
        # scan for any with enough stock
        for row in ps.df.iterrows():
            r = row[1]
            st = r.get("stock",0)
            if not pd.isna(st) and int(st) >= 10:
                prod = {"product_name": r.get("product name"), "stock": int(st)}
                break
    prod_name = prod.get("product_name")
    parsed1 = {"intent":"order","product_name":prod_name,"quantity":5,"missing":None,"symptom":None,"friendly_response":""}
    resp1 = asyncio.run(da.decide(parsed1, raw_message=f"Order 5 {prod_name}", session_id=session))
    assert prod_name.split()[0] in resp1.get("message", "")

    # show history doesn't disturb pending state
    history_msg = "show my order"
    parsed_h = {"intent":"general_chat","product_name":None,"quantity":None,"missing":None,"symptom":None,"friendly_response":""}
    _ = asyncio.run(da.decide(parsed_h, raw_message=history_msg, session_id=session))

    # also test that a bare number without a product returns our polite prompt
    resp_num = asyncio.run(da.decide({"intent":"general_chat"}, raw_message="20", session_id=session))
    assert "entered a number" in resp_num.get("message", ""), "Should get guidance when just a number is sent"

    # now order Kijimea with quantity included as well
    parsed2 = {"intent":"order","product_name":"Kijimea Reizdarm PRO","quantity":None,"missing":"quantity","symptom":None,"friendly_response":""}
    resp2 = asyncio.run(da.decide(parsed2, raw_message="Order Kijimea Reizdarm PRO", session_id=session))
    assert "Kijimea" in resp2.get("message", "")

    # confirmation scenario: show info for Cystinol, then say 'yes'
    info_msg = "Cystinol akut"
    parsed_info = {"intent":"product_info","product_name":"Cystinol akut","quantity":None,"missing":None,"symptom":None,"friendly_response":""}
    resp_info = asyncio.run(da.decide(parsed_info, raw_message=info_msg, session_id=session))
    assert "Medicine Information" in resp_info.get("message", "")
    # now user says yes, should prompt for quantity of Cystinol
    resp_yes = asyncio.run(da.decide({"intent":"general_chat"}, raw_message="yes", session_id=session))
    assert "Cystinol" in resp_yes.get("message", "") and "How many units" in resp_yes.get("message", "")

    # reply with 20 -> quantity limit check
    parsed3 = {"intent":"order","product_name":None,"quantity":20,"missing":None,"symptom":None,"friendly_response":""}
    resp3 = asyncio.run(da.decide(parsed3, raw_message="20", session_id=session))
    assert "Quantity exceeds" in resp3.get("message", "")

    # now send 10 and parser mistakenly returns Nurofen; stock is low
    parsed4 = {"intent":"order","product_name":"Nurofen 200 mg Schmelztabletten Lemon","quantity":10,"missing":None,"symptom":None,"friendly_response":""}
    resp4 = asyncio.run(da.decide(parsed4, raw_message="10", session_id=session))
    # we should *not* accidentally mention Nurofen; the stock error may
    assert "Nurofen" not in resp4.get("message", ""), "Should not switch back to Nurofen"
    assert "Only" in resp4.get("message", "") and "available" in resp4.get("message", ""), "Expected a stock error"

def test_quantity_followup_preserves_product():
    _run_test_logic()
    _run_misleading_product()
    _run_complex_history()
