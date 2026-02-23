from langfuse import observe

@observe(name="validate_llm_output")
def validate_llm_output(parsed):

    required_fields = ["intent", "product_name", "quantity"]

    for field in required_fields:
        if field not in parsed:
            return False, f"Missing {field}"

    if parsed["quantity"] and parsed["quantity"] > 10:
        return False, "Quantity exceeds allowed limit"

    return True, "OK"