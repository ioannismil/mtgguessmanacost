from flask import Flask, render_template, request, jsonify, session
import requests
import re

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route("/")
def index():
    if "lives" not in session:
        session["lives"] = 3
        session["score"] = 0
        session["streak"] = 0
        session["history"] = []
    
    # Ensure history exists if session was old
    if "history" not in session:
        session["history"] = []
        
    return render_template("index.html", 
                         lives=session["lives"], 
                         score=session["score"], 
                         streak=session.get("streak", 0),
                         history=session["history"])

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/robots.txt")
def robots():
    return app.send_static_file("robots.txt")

@app.route("/sitemap.xml")
def sitemap():
    return app.send_static_file("sitemap.xml")

@app.route("/reset_game", methods=["POST"])
def reset_game():
    data = request.get_json() or {}
    mode = data.get("mode", "classic")
    
    if mode == "timed":
        session["lives"] = 999 # Infinite lives effectively
    else:
        session["lives"] = 3
        
    session["score"] = 0
    session["streak"] = 0
    session["history"] = []
    session.pop("current_card_data", None) # Clear cached card
    return jsonify({"message": f"Game restarting in {mode} mode!"})

@app.route("/get_card")
def get_card():
    force_new = request.args.get("new_card", "false").lower() == "true"
    
    # Return cached card if available and not forcing new
    if not force_new and "current_card_data" in session:
        return jsonify(session["current_card_data"])

    selected_set = request.args.get("set", "").lower().strip()
    colors_filter = request.args.get("colors", "").strip()
    formats_filter = request.args.get("formats", "").strip()
    game_mode = request.args.get("mode", "").lower().strip()
    
    # Build the Scryfall query
    # Optimization: Use positive filters where possible. 
    # layout:normal excludes tokens, planes, schemes, vanguards, split cards, adventures, etc. if we want standard cards. 
    # But to be safe and get "cards you cast", we use:
    # game:paper (user requirement)
    # -is:funny (exclude un-sets unless requested)
    # has:mana_cost (exclude lands, suspend-only, etc)
    query_parts = ["game:paper", "layout:normal", "-is:funny","-type:token", "-is:mdfc", "-is:adventure"]
    
    # For price is right, we need USD price. For others, we generally want mana cost.
    # Art detective works with any card, but usually we want things with colored art (so maybe not lands? but lands have art too).
    # Let's keep has:mana_cost for now unless it's art detective where we might want lands? 
    # Actually, sticking to non-lands is safer for consistency with existing filters.
    if game_mode == "price_is_right":
        query_parts.append("has:usd")
        query_parts.append("-type:land") # Price is right is boring with basic lands
    else:
         query_parts.append("has:mana_cost")
         query_parts.append("-type:land")

    if selected_set:
        query_parts.append(f"set:{selected_set}")
    
    if colors_filter:
        # colors_filter will be something like "(c:U) -c:W -c:B -c:R -c:G -c:C"
        query_parts.append(colors_filter)

    if formats_filter:
        # formats_filter will be a comma-separated list like "standard,modern"
        # We want to construct: (legal:standard OR legal:modern)
        f_list = [f.strip() for f in formats_filter.split(",") if f.strip()]
        if f_list:
            format_query = " OR ".join([f"legal:{f}" for f in f_list])
            query_parts.append(f"({format_query})")
    
    full_query = " ".join(query_parts)
    print(f"DEBUG: Scryfall query: {full_query}")
    
    response = requests.get("https://api.scryfall.com/cards/random", params={"q": full_query})
    
    if response.status_code != 200:
        print(f"DEBUG: Scryfall API error: {response.text}")
        return jsonify({"error": "No cards found matching your filters."}), 404

    try:
        data = response.json()
        
        # Helper to get mana cost safely
        mana_cost = data.get("mana_cost")
        if mana_cost is None:
            # Fallback to color_identity if mana_cost doesn't exist (e.g. DFCs if layout:normal failed to exclude them or we want them)
            # note: layout:normal excludes DFCs usually, but just in case.
            if "color_identity" in data and data["color_identity"]:
                mana_cost = f"{{{data['color_identity'][0]}}}"
            else:
                mana_cost = ""

        card = {
            "name": data["name"],
            "image": data["image_uris"]["normal"] if "image_uris" in data else None,
            "art_crop": data["image_uris"]["art_crop"] if "image_uris" in data and "art_crop" in data["image_uris"] else None,
            "mana_cost": mana_cost,
            "cmc": data.get("cmc", 0.0),
            "prices": data.get("prices", {}),
            "color_identity": data.get("color_identity", [])
        }

        # Save Scryfall URI and mana cost to session
        session["current_scryfall_uri"] = data.get("scryfall_uri", "")

        # Clean up for comparison
        session["current_mana_cost"] = card["mana_cost"].upper().replace(" ", "")
        
        # Save full card data to session for persistence
        session["current_card_data"] = card

        return jsonify(card)
    except Exception as e:
        print(f"ERROR: Failed to parse card data: {e}")
        return jsonify({"error": "Failed to process card data."}), 500

@app.route("/higher_lower")
def higher_lower():
    return render_template("higher_lower.html")

@app.route("/get_sets")
def get_sets():
    r = requests.get("https://api.scryfall.com/sets")
    data = r.json()

    sets = [
        {"code": s["code"], "name": s["name"]}
        for s in data.get("data", [])
        if not s["set_type"] in ["token", "promo", "memorabilia"]
    ]

    return jsonify(sets)

@app.route("/art_detective")
def art_detective():
    return render_template("art_detective.html")

@app.route("/price_is_right")
def price_is_right():
    return render_template("price_is_right.html")

@app.route("/guess", methods=["POST"])
def guess():
    user_guess = request.json["guess"].upper().replace(" ", "")
    
    # Stateless validation: prefer mana cost sent by client (for queue/prefetch scenarios)
    if "actual_mana_cost" in request.json:
        correct_cost = request.json["actual_mana_cost"].upper().replace(" ", "").replace("/", "")
    else:
        correct_cost = session.get("current_mana_cost", "").replace("/", "")
    result = {}
    if user_guess == correct_cost:
        session["score"] += 1
        session["streak"] = session.get("streak", 0) + 1
        result["correct"] = True
        result["message"] = "✅ Correct!"
    else:
        session["lives"] -= 1
        session["streak"] = 0
        result["correct"] = False
        result["message"] = "❌ Wrong!"

    # Add to history
    card_data = session.get("current_card_data", {})
    if card_data:
        if "history" not in session:
            session["history"] = []
        
        # Prepend to history (max 10)
        history_item = {
            "name": card_data.get("name"),
            "image": card_data.get("image"),
            "correct_cost": correct_cost,
            "is_correct": result["correct"]
        }
        
        # We need to manage the list manually to prepend
        current_history = session["history"]
        current_history.insert(0, history_item)
        if len(current_history) > 10:
            current_history.pop()
        session["history"] = current_history
        session.modified = True


    result["lives"] = session["lives"]
    result["score"] = session["score"]
    result["streak"] = session.get("streak", 0)
    result["game_over"] = session["lives"] <= 0

    # Return the correct mana cost separately for frontend SVG rendering
    # Return the correct mana cost and Scryfall URI
    result["correct_cost"] = correct_cost
    result["scryfall_uri"] = session.get("current_scryfall_uri", "")

    return jsonify(result)

@app.route("/reset", methods=["POST"])
def reset():
    data = request.get_json() or {}
    mode = data.get("mode", "classic")
    
    if mode == "timed":
        session["lives"] = 999
    else:
        session["lives"] = 3
        
    session["score"] = 0
    session["streak"] = 0
    session["current_card"] = None
    session["history"] = []
    session.pop("current_card_data", None) # Clear cached card
    return jsonify({"message": "Game reset", "lives": session["lives"], "score": session["score"], "streak": session["streak"]})


if __name__ == "__main__":
    app.run(debug=True)
