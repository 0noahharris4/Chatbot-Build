from __future__ import annotations
import os
from flask import Flask, request, jsonify, render_template
from openai import OpenAI

# ── Property context ───────────────────────────────────────────────────────────
PROPERTY_CONTEXT = """
You are Dave, an expert property assistant for Clear Water Apartments, a luxury apartment building in Malibu, California. You have extensive knowledge of the property, units available, leasing information, nearby amenities, and the local area. Your role is to provide accurate and helpful information to prospective and current residents about the property, leasing processes, amenities, and local attractions.

Current Property Information:
- Available Units:
  * Unit 101: 1 bed, 1 bath - $2,500/month - Available March 1, 2026
  * Unit 201: 2 bed, 2 bath - $3,800/month - Available February 15, 2026
  * Unit 202: 2 bed, 2 bath - $3,800/month - Available April 1, 2026
  * Unit 301: 1 bed, 1 bath - $2,500/month - Available February 20, 2026
  * Unit 302: 3 bed, 2 bath - $5,200/month - Available May 1, 2026
- Pricing:
  * 1 Bedroom: Starting at $2,500/month
  * 2 Bedroom: $3,800/month
  * 3 Bedroom: Starting at $5,200/month
  * All prices include utilities (water, trash, high-speed internet)
  * Discounts available for longer lease commitments
- Building Amenities: Fitness center, movie theater, tennis courts, swimming pool, rooftop lounge, 24/7 concierge, underground parking
- Lease Terms: Month-to-month, 3 months, 6 months, 12 months. Typically 30-day notice for move-out.
- Move-in Costs: $100 security deposit (returned after move-out if no damage), $25 application fee
- Pet Policy: Up to 2 pets allowed with $300 pet deposit per pet

Always be professional, warm, and helpful. Encourage prospective residents to contact the leasing office or schedule a tour.
"""

# ── App ────────────────────────────────────────────────────────────────────────
app = Flask(__name__)

_openai_client: OpenAI | None = None

def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _openai_client


# ── Rule-based response engine ─────────────────────────────────────────────────
def get_bot_response(user_input: str) -> str:
    t = user_input.lower()

    # Late payment
    if ("late" in t and "payment" in t) or "late fee" in t:
        return "Rent is due on the 1st of each month. A late fee of $50 applies if payment is received after the 5th. Please check your lease for full details."

    # Portal access
    if ("access" in t and "portal" in t) or ("how" in t and "portal" in t):
        return "The resident payment portal is available through our website or the resident app. Log in with your email and password. Contact the office if you need help accessing your account."

    # Rent due date
    if ("when" in t and "rent" in t and "due" in t) or "rent due" in t:
        return "Rent is due on the 1st of each month. A $50 late fee applies after the 5th."

    # Package delivery
    if ("package" in t or "packages" in t) and ("deliver" in t or "delivery" in t or "delivered" in t):
        return "Packages are delivered to your front door, your mailbox, or the package room depending on size. You'll receive a notification via the resident app when your package arrives."

    # Office hours
    if "office hours" in t or ("when" in t and "office" in t) or ("hours" in t and "open" in t):
        return "Our leasing office is open Monday–Friday 9am–5pm and Saturday 10am–4pm. We're closed Sundays and major holidays."

    # Maintenance
    if ("maintenance" in t or "repair" in t or "broken" in t) and ("submit" in t or "request" in t or "how" in t):
        return "Submit a maintenance request through the resident portal under 'Maintenance.' For emergencies such as leaks or no heat, please call our 24/7 emergency line immediately."

    # Parking
    if "parking" in t or "garage" in t or ("permit" in t and "parking" in t):
        return "Each resident is assigned a dedicated parking spot in our underground garage. Parking permits are issued through the leasing office. Guest parking is available but limited."

    # Move-out
    if ("move" in t and "out" in t) or "move-out" in t or ("notice" in t and "move" in t):
        return "Our move-out policy requires a 30-day written notice. Please refer to your lease agreement for specific details and any associated fees."

    # Contact
    if ("contact" in t and ("office" in t or "leasing" in t)) or ("how" in t and "reach" in t) or ("email" in t and "phone" in t):
        return "You can reach our leasing office by calling (555) 123-4567 or emailing leasing@clearwaterapts.com. We're here Monday–Saturday to help!"

    # Utilities
    if "utilities" in t or (("water" in t or "electric" in t or "gas" in t or "wifi" in t or "internet" in t) and ("included" in t or "bill" in t or "pay" in t)):
        return "All units include water, trash, and high-speed internet in the monthly rent. Electricity is billed separately through the utility provider."

    # Greetings
    if any(w in t for w in ("hello", "hi", "hey", "good morning", "good afternoon")):
        return "Hello! Welcome to Clear Water Apartments. I'm Dave, your virtual property assistant. How can I help you today?"

    # Thanks
    if any(w in t for w in ("thank", "thanks", "thx")):
        return "You're welcome! Is there anything else I can help you with?"

    # Fallback to OpenAI
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": PROPERTY_CONTEXT},
                {"role": "user", "content": user_input},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        return response.choices[0].message.content
    except Exception:
        return "I'm not sure I have the answer to that. Please contact our leasing office at (555) 123-4567 or email leasing@clearwaterapts.com — we'd be happy to help!"


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_input = data.get("message", "").strip()
    if not user_input:
        return jsonify({"error": "No message provided"}), 400
    reply = get_bot_response(user_input)
    return jsonify({"reply": reply})


# ── Entry ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
