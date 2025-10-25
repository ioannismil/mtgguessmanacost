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
    return render_template("index.html", lives=session["lives"], score=session["score"])

@app.route("/get_card")
def get_card():
    response = requests.get("https://api.scryfall.com/cards/random")
    data = response.json()

    card = {
        "name": data["name"],
        "image": data["image_uris"]["normal"] if "image_uris" in data else None,
        "mana_cost": data.get("mana_cost", ""),  # e.g. "{1}{W}{U}"
    }

    # Clean up for comparison
    session["current_mana_cost"] = card["mana_cost"].upper().replace(" ", "")
    return jsonify(card)

@app.route("/guess", methods=["POST"])
def guess():
    user_guess = request.json["guess"].upper().replace(" ", "")
    correct_cost = session.get("current_mana_cost", "")

    result = {}
    if user_guess == correct_cost:
        session["score"] += 1
        result["correct"] = True
        result["message"] = "✅ Correct!"
    else:
        session["lives"] -= 1
        result["correct"] = False
        result["message"] = "❌ Wrong!"

    result["lives"] = session["lives"]
    result["score"] = session["score"]
    result["game_over"] = session["lives"] <= 0

    # Return the correct mana cost separately for frontend SVG rendering
    result["correct_cost"] = correct_cost

    return jsonify(result)

@app.route("/reset", methods=["POST"])
def reset():
    session["lives"] = 3
    session["score"] = 0
    session["current_card"] = None
    return jsonify({"message": "Game reset", "lives": session["lives"], "score": session["score"]})


if __name__ == "__main__":
    app.run(debug=True)
