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
    return render_template("index.html", lives=session["lives"], score=session["score"], streak=session.get("streak", 0))

@app.route("/reset_game", methods=["POST"])
def reset_game():
    session["lives"] = 3
    session["score"] = 0
    session["streak"] = 0
    return jsonify({"message": "Game restarting!"})

@app.route("/get_card")
def get_card():
    selected_set = request.args.get("set", "").lower().strip()
    colors_filter = request.args.get("colors", "").strip()
    formats_filter = request.args.get("formats", "").strip()
    
    # Build the Scryfall query
    query_parts = ["-type:land", "-type:token", "-is:mdfc", "-is:adventure","game:paper","-type:emblem","-type:conspiracy",
    "-set:unk","-type:Battle","-set_type:memorabilia","-is:playtest","-type:plane"]
    
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
        card = {
            "name": data["name"],
            "image": data["image_uris"]["normal"] if "image_uris" in data else None,
            "mana_cost": data.get("mana_cost", ""),  # e.g. "{1}{W}{U}"
        }

        # Save Scryfall URI and mana cost to session
        session["current_scryfall_uri"] = data.get("scryfall_uri", "")

        # Clean up for comparison
        session["current_mana_cost"] = card["mana_cost"].upper().replace(" ", "")
        return jsonify(card)
    except Exception as e:
        print(f"ERROR: Failed to parse card data: {e}")
        return jsonify({"error": "Failed to process card data."}), 500

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
@app.route("/guess", methods=["POST"])
def guess():
    user_guess = request.json["guess"].upper().replace(" ", "")
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
    session["lives"] = 3
    session["score"] = 0
    session["streak"] = 0
    session["current_card"] = None
    return jsonify({"message": "Game reset", "lives": session["lives"], "score": session["score"], "streak": session["streak"]})


if __name__ == "__main__":
    app.run(debug=True)
