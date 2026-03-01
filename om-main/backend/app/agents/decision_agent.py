import json
import os
import random
from datetime import datetime, timedelta
from langfuse import observe
from langchain_core.messages import HumanMessage, SystemMessage

# ✅ Import the LLM so we can use it to generate human-friendly explanations
from app.agents.conversational_agent import llm 
from app.agents.safety_agent import SafetyAgent
from app.agents.execution_agent import ExecutionAgent
from app.agents.guardrail import validate_llm_output

# Path to store order history
ORDER_HISTORY_FILE = "order_history.json"

def pick_variation(phrases_list):
    """Return a random phrase from list for natural variation in responses."""
    return random.choice(phrases_list) if phrases_list else ""

class DecisionAgent:

    def __init__(self):
        self.safety_agent = SafetyAgent()
        self.execution_agent = ExecutionAgent()
        # load order history from file or start fresh
        self.order_history = self._load_order_history()
        # keep track of orders waiting for quantity clarification by session
        self.pending_orders = {}
        # remember latest recommendation list per session for numeric selection
        self.last_recommendations = {}
    
    def _load_order_history(self):
        """Load order history from file."""
        if os.path.exists(ORDER_HISTORY_FILE):
            try:
                with open(ORDER_HISTORY_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Could not load order history: {e}")
        return []
    
    def _save_order_history(self):
        """Save order history to file."""
        try:
            with open(ORDER_HISTORY_FILE, 'w') as f:
                json.dump(self.order_history, f, indent=2, default=str)
        except Exception as e:
            print(f"Could not save order history: {e}")

    def _format_order_history(self, orders, limit=None):
        """Format order list as readable history with dates."""
        if not orders:
            return "You haven't placed any orders yet."
        
        response = "📋 **Your Order History**\n\n"
        to_display = orders[:limit] if limit else orders
        
        for i, order in enumerate(to_display, 1):
            product_name = order.get('product_name', 'Unknown')
            quantity = order.get('quantity', 1)
            price = order.get('total_price', 0)
            created = order.get('created_at')
            
            # Format date if it exists
            date_str = ""
            if created:
                if isinstance(created, str):
                    date_str = created.split('T')[0]  # "YYYY-MM-DD"
                else:
                    date_str = created.strftime('%Y-%m-%d')
            
            response += f"{i}. **{product_name}** × {quantity} units - ${price} ({date_str})\n"
        
        if limit and len(orders) > limit:
            response += f"\n... and {len(orders) - limit} more orders."
        
        return response

    def _get_recent_orders(self, days_back=30):
        """Get orders from the last N days."""
        if not self.order_history:
            return []
        
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        recent = []
        
        for order in self.order_history:
            created = order.get('created_at')
            if created:
                if isinstance(created, str):
                    created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                if created >= cutoff:
                    recent.append(order)
        
        return recent

    @observe(name="decide_on_user_intent")
    async def decide(self, parsed_input, raw_message: str = None, session_id: str = None):
        # 1. Handle string input from LLM and clean JSON code blocks
        if isinstance(parsed_input, str):
            try:
                clean_input = parsed_input.replace("```json", "").replace("```", "").strip()
                parsed_input = json.loads(clean_input)
            except Exception:
                return {"message": "I'm sorry, I'm having trouble processing that request. Could you please specify how I can help?"}

        # Extract core fields
        intent = parsed_input.get("intent")
        product_name = parsed_input.get("product_name")
        symptom = parsed_input.get("symptom") # ✅ Important for symptom check
        quantity = parsed_input.get("quantity")
        friendly_msg = parsed_input.get("friendly_response", "")
        selected_from_recommendation = False

        # If user just sends a number on its own and we don't know which product
        # they're referring to, respond with a helpful prompt rather than trying
        # to guess.  However, if we already have a pending product stored we
        # should let the quantity override logic run instead.
        if raw_message and raw_message.strip().isdigit() and not product_name:
            choice = int(raw_message.strip())
            recs = self.last_recommendations.get(session_id, []) if session_id else []
            if recs:
                if 1 <= choice <= len(recs):
                    product_name = recs[choice - 1]
                    intent = "order"
                    quantity = None  # Numeric input here means item selection.
                    parsed_input["intent"] = intent
                    parsed_input["product_name"] = product_name
                    parsed_input["quantity"] = None
                    parsed_input["missing"] = "quantity"
                    selected_from_recommendation = True
                    self.last_recommendations.pop(session_id, None)
                else:
                    return {"message": f"Please choose a number between 1 and {len(recs)} from the recommendations."}
            else:
                pending = self.pending_orders.get(session_id) if session_id else None
                if not pending:
                    return {
                        "message": (
                            "It looks like you entered a number, but I need to know which "
                            "medicine you want. For example, you can say 'Order 2 Paracetamol' "
                            "or describe your symptoms."
                        )
                    }


        # ----------------------------------------------------------------
        # SPECIAL CASE: user responded with a quantity after being asked for it
        # ----------------------------------------------------------------
        # When a previous message prompted for quantity we store the product in
        # `pending_orders`.  If the current turn includes a quantity, we want to
        # *always* attribute it to the pending product, even if the LLM parser
        # erroneously tries to re‑infer something else based on chat history.
        if session_id and quantity and not selected_from_recommendation:
            pending = self.pending_orders.get(session_id)
            if pending and pending.get("product_name"):
                # override only when parser gave no name or a mismatched name
                if not product_name or product_name != pending["product_name"]:
                    product_name = pending["product_name"]
                    intent = pending.get("intent", intent)
                    parsed_input["product_name"] = product_name
                    parsed_input["intent"] = intent
                # note: we *don't* clear the pending entry here because the
                # order may still fail (e.g. quantity limit) and we want to
                # remember the product for the next attempt.

        # apply any pending‑order override first
        if session_id and quantity and not selected_from_recommendation:
            pending = self.pending_orders.get(session_id)
            if pending and pending.get("product_name"):
                if not product_name or product_name != pending["product_name"]:
                    product_name = pending["product_name"]
                    intent = pending.get("intent", intent)
                    parsed_input["product_name"] = product_name
                    parsed_input["intent"] = intent
        # keep the pending entry until the order actually succeeds

        # now update the remembered product on every order turn
        if session_id and intent == "order" and product_name:
            self.pending_orders[session_id] = {"product_name": product_name, "intent": intent}

        # ---------------------------------------------------------
        # EARLY CHECK: Did the user ask about order history?
        # ---------------------------------------------------------
        if raw_message:
            lower = raw_message.lower()
            
            # Check for history/orders queries (with more natural variations)
            history_keywords = ["history", "all my orders", "show orders", "show my orders", "my orders", "order list", "previous orders", "where are my orders", "can you show", "my order", "booked"]
            if any(kw in lower for kw in history_keywords):
                if self.order_history:
                    return {"message": self._format_order_history(self.order_history)}
                else:
                    return {"message": "You haven't placed any orders yet."}
            
            # Check for recent orders (7, 30 days, "this month", etc.)
            recent_keywords = {"last week": 7, "last month": 30, "this month": 30, "recent": 7, "lately": 7}
            for kw, days in recent_keywords.items():
                if kw in lower:
                    recent = self._get_recent_orders(days)
                    if recent:
                        return {"message": self._format_order_history(recent)}
                    else:
                        return {"message": f"You haven't placed any orders in the last {days} days."}
            
            # Check for single "previous" reference (most recent only)
            if "previous" in lower or "last" in lower or "earlier" in lower:
                if self.order_history and (intent == "product_info" or intent == "general_chat"):
                    last_order = self.order_history[-1]
                    return {
                        "message": f"🔁 You previously ordered **{last_order.get('product_name')}**. Would you like more details or to reorder?"
                    }

        # ---------------------------------------------------------
        # CASE 1: SYMPTOM CHECK (SMART RECOMMENDATION)
        # ---------------------------------------------------------
        # ✅ PRIORITY: If the user mentions a symptom, we process this FIRST.
        if intent == "symptom_check" or (not product_name and symptom):
            search_query = symptom or product_name or friendly_msg
            if session_id:
                # New symptom flow starts a fresh recommendation context.
                self.pending_orders.pop(session_id, None)
            
            # 1. Use advanced symptom matcher to find products
            results = self.execution_agent.recommend_products(search_query)
            
            if not results.get("found") or results.get("total_matches", 0) == 0:
                return {"message": f"I analyzed our inventory for '{search_query}', but couldn't find specific matches. Please consult a doctor for clinical advice, or describe your symptoms differently."}
            
            matches = results["matches"]
            symptom_categories = results.get("symptom_categories", [])
            total_matches = results.get("total_matches", 0)
            if session_id:
                self.last_recommendations[session_id] = [
                    m.get("product_name") for m in matches if m.get("product_name")
                ]

            # 2. Generate a user-friendly response showing the matches
            response = f"💊 **Recommended Medicines for '{search_query}'**\n\n"
            response += f"*Found {total_matches} matching products (showing top results)*\n\n"
            
            for i, match in enumerate(matches, 1):
                product_name = match.get("product_name", "Unknown")
                price = match.get("price", 0)
                stock = match.get("stock", 0)
                similarity = match.get("similarity", 0)
                desc = match.get("description", "")
                suitable = match.get("suitable", True)
                
                # Truncate description if too long
                if len(desc) > 120:
                    desc = desc[:120] + "..."
                
                stock_indicator = "✅ In Stock" if stock > 0 else "❌ Out of Stock"
                
                response += f"**{i}. {product_name}**\n"
                response += f"   💰 Price: ${price} per unit\n"
                response += f"   📦 {stock_indicator} ({stock} units)\n"
                response += f"   📊 Match: {similarity*100:.0f}% relevant\n"
                response += f"   ℹ️ {desc}\n"
                if not suitable:
                    response += "   ⚠️ This product is not typically used for the symptom you've described.\n"
                response += "\n"
            
            response += "**Would you like to order any of these medicines? Just tell me the number!**"
            return {"message": response}

        # ---------------------------------------------------------
        # CASE 2: GENERAL CHAT
        # ---------------------------------------------------------
        # before treating as simple chat, check for affirmative response when
        # there is a pending product waiting for quantity
        if intent == "general_chat":
            if raw_message and session_id:
                lower = raw_message.lower()
                affirmatives = ["yes", "yeah", "sure", "please", "ok", "order that", "yep"]
                pending = self.pending_orders.get(session_id)
                if pending and any(aff in lower for aff in affirmatives):
                    prod = pending.get("product_name")
                    return {"message": f"I've found **{prod}** in our system. How many units or strips would you like to order?"}
            return {"message": friendly_msg or "Hello! How can I help you today?"}

        # ---------------------------------------------------------
        # CASE 3: MISSING PRODUCT NAME (Only for direct Orders/Info)
        # ---------------------------------------------------------
        # If we reached here, it means no symptom was detected. 
        # Now we check if they are trying to order/get info but forgot the name.
        if (intent == "order" or intent == "product_info") and not product_name:
            return {"message": friendly_msg or "Which medicine are you inquiring about? Or you can tell me your symptoms."}

        # ---------------------------------------------------------
        # CASE A: PRODUCT INFO / PRICE CHECK
        # ---------------------------------------------------------
        if intent == "product_info":
            data = self.execution_agent.get_product_details(product_name=product_name)

            if not data.get("found"):
                return {"message": f"I checked our inventory, but I couldn't find **{product_name}**. Please double-check the spelling!"}

            product = data.get("product", {})
            price = product.get("price", 0)
            description = product.get("description", "No description available.")
            
            # remember this product so a follow-up 'yes' can turn into an order
            if session_id and product_name:
                self.pending_orders[session_id] = {"product_name": product_name, "intent": "order"}

            return {
                "message": f"🔍 **Medicine Information**\n\n**Name:** {product.get('product_name')}\n**Price:** ${price} per unit\n**Description:** {description}\n\nWould you like me to place an order for you?"
            }

        # ---------------------------------------------------------
        # CASE B: PLACING AN ORDER
        # ---------------------------------------------------------
        if intent == "order":
            if parsed_input.get("missing") == "quantity" or not quantity:
                # remember what product they were asking about so quantity replies can be linked
                if session_id and product_name:
                    self.pending_orders[session_id] = {
                        "product_name": product_name,
                        "intent": "order"
                    }
                quantity_ask = pick_variation([
                    f"I've found **{product_name}** in our system. How many units or strips would you like to order?",
                    f"**{product_name}** is available. How many would you like?",
                    f"Perfect! **{product_name}** is in stock. What quantity works best for you?",
                ])
                return {"message": quantity_ask}

            valid, reason = validate_llm_output(parsed_input)
            if not valid:
                return {"message": f"**Order Notice**: {reason}"}

            pid = session_id or 1
            safety = self.safety_agent.validate_order(patient_id=pid, product_name=product_name, quantity=quantity)
            if not safety["approved"]:
                return {"message": f"**Safety Check Failed**: {safety['reason']}"}
            execution_result = await self.execution_agent.execute_order(
                patient_id=pid, product_name=product_name, quantity=quantity
            )

            if execution_result.get("approved"):
                # clear any pending order for this session since it's now complete
                if session_id:
                    self.pending_orders.pop(session_id, None)
                # add to order history for tracking and save to file
                self.order_history.append(execution_result['order'])
                self._save_order_history()  # Persist to file
                total = execution_result['order']['total_price']
                order_id = execution_result['order']['order_id']
                rem_stock = execution_result.get("remaining_stock")
                rem_text = f"\n\nYou now have **{rem_stock}** units of {product_name} remaining in stock." if rem_stock is not None else ""
                notif = ""
                if execution_result.get("notification_sent"):
                    phone = execution_result.get("notification_phone")
                    notif = f"\n\nA confirmation message has been sent to {phone}."
                
                # use varied success phrases
                success_prefix = pick_variation([
                    "Your order has been confirmed!",
                    "Perfect! Your order is confirmed.",
                    "Excellent! Your order has been placed.",
                    "All set! Your order is ready for delivery."
                ])
                return {
                    "message": f"{success_prefix}\n\nI have successfully ordered **{quantity}x {product_name}** for you.\n\n**Total:** ${total}\n**Order ID:** `{order_id}`{rem_text}{notif}\n\nYour medicine will be prepared shortly.\n\n💡 **Tip:** Say 'Show my orders' to see all your previous orders!"
                }
            else:
                return {"message": f"**Fulfillment Error**: {execution_result.get('error', 'I could not process the order at this time.')}"}
        # Fallback
        return {"message": friendly_msg or "I'm here to help with your pharmacy needs."}
