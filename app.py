from flask import Flask, render_template, request, jsonify, session, send_file
import os
from itsdangerous import URLSafeTimedSerializer
import requests
import re
from datetime import datetime, timedelta
from database import db, Score

def normalize_mana_cost(cost):
    if not cost:
        return ""
    # Extract all symbols in braces, sort them, and join them back
    symbols = re.findall(r"\{[^}]+\}", cost)
    if not symbols:
        return cost
    symbols.sort()
    return "".join(symbols)

app = Flask(__name__)
app = Flask(__name__)
# Use environment variable for secret key in production
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key_change_me")
serializer = URLSafeTimedSerializer(app.secret_key)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///leaderboard.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Cache for Scryfall sets data (reduces API calls)
_sets_cache = None
_sets_cache_time = None
CACHE_DURATION = timedelta(hours=24)  # Refresh daily

def generate_card_token(card_data):
    """Encrypts card data into a token."""
    return serializer.dumps(card_data)

def verify_card_token(token):
    """Decrypts token to get card data."""
    try:
        return serializer.loads(token, max_age=3600) # Token valid for 1 hour
    except Exception:
        return None

# Initialize database tables on first request
@app.before_request
def create_tables():
    """Create database tables if they don't exist"""
    if not hasattr(app, '_tables_created'):
        with app.app_context():
            db.create_all()
        app._tables_created = True

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
    return send_file('static/sitemap.xml', mimetype='application/xml')

@app.route("/favicon.ico")
def favicon():
    return app.send_static_file("favicon.ico")

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
    # force_new is deprecated with queue system but kept for compatibility
    # if not force_new and "current_card_data" in session:
    #     return jsonify(session["current_card_data"])

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
    # query_parts = ["is:hybrid"]
    
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

        # Save Scryfall URI to session (optional, but better in token)
        session["current_scryfall_uri"] = data.get("scryfall_uri", "") 

        # Generate secure token
        token_data = {
            "name": card["name"],
            "mana_cost": card["mana_cost"],
            "cmc": card["cmc"],
            "image": card["image"],
            "scryfall_uri": data.get("scryfall_uri", "")
        }
        card["token"] = generate_card_token(token_data)

        # Remove sensitive data from clear text response
        # We need mana_cost for history BUT we shouldn't send it to client if we want to prevent cheating.
        # However, for Art Detective or Price is Right, mana_cost might be public?
        # For "Guess Mana Cost", we MUST HIDE it.
        # For now, let's redact it. Use token for validation.
        # card["mana_cost"] = "???" # Client needs to handle this.
        # Actually existing frontend relies on card.mana_cost to NOT be shown? 
        # No, frontend receives it and hides it via CSS (insecure).
        # We will DELETE it from response for Guess Game.
        if game_mode == "guess_mana" or not game_mode: # Default mode
             del card["mana_cost"]
             del card["cmc"]

        # Session storage is no longer primary source of truth for the active card
        # session["current_card_data"] = card 

        return jsonify(card)
    except Exception as e:
        print(f"ERROR: Failed to parse card data: {e}")
        return jsonify({"error": "Failed to process card data."}), 500

@app.route("/higher_lower")
def higher_lower():
    return render_template("higher_lower.html")

@app.route("/get_sets")
def get_sets():
    global _sets_cache, _sets_cache_time
    
    # Check if cache is valid (exists and not expired)
    if _sets_cache and _sets_cache_time and datetime.now() - _sets_cache_time < CACHE_DURATION:
        return jsonify(_sets_cache)
    
    # Cache miss or expired - fetch fresh data from Scryfall
    r = requests.get("https://api.scryfall.com/sets")
    data = r.json()

    sets = [
        {"code": s["code"], "name": s["name"]}
        for s in data.get("data", [])
        if not s["set_type"] in ["token", "promo", "memorabilia"]
    ]
    
    # Update cache
    _sets_cache = sets
    _sets_cache_time = datetime.now()

    return jsonify(sets)

@app.route("/price_is_right")
def price_is_right():
    return render_template("price_is_right.html")

@app.route("/leaderboard")
def leaderboard_page():
    """Display the leaderboard page"""
    return render_template("leaderboard.html")

@app.route("/api/submit_score", methods=["POST"])
def submit_score():
    """Submit a score to the leaderboard"""
    data = request.get_json()
    
    # Validate required fields
    game_mode = data.get("game_mode")
    score = data.get("score")
    streak = data.get("streak", 0)
    username = data.get("username", "Anonymous")[:50]  # Limit length
    
    if not game_mode or score is None:
        return jsonify({"error": "Missing required fields"}), 400
    
    # Generate or retrieve session ID for deduplication
    if "session_id" not in session:
        import uuid
        session["session_id"] = str(uuid.uuid4())
    
    session_id = session["session_id"]
    
    # Prevent duplicate submissions from same session (cooldown: 60 seconds)
    recent = Score.query.filter_by(
        session_id=session_id, 
        game_mode=game_mode
    ).order_by(Score.timestamp.desc()).first()
    
    if recent and (datetime.utcnow() - recent.timestamp).seconds < 60:
        return jsonify({"error": "Please wait before submitting another score"}), 429
    
    # Save score
    new_score = Score(
        game_mode=game_mode,
        username=username,
        score=score,
        streak=streak,
        session_id=session_id
    )
    db.session.add(new_score)
    db.session.commit()
    
    # Calculate rank (count how many scores are better)
    rank = Score.query.filter(
        Score.game_mode == game_mode,
        Score.score > score
    ).count() + 1
    
    return jsonify({
        "message": "Score submitted!",
        "rank": rank,
        "username": username
    })

@app.route("/api/leaderboard/<game_mode>")
def get_leaderboard(game_mode):
    """Get leaderboard for a specific game mode"""
    timeframe = request.args.get("timeframe", "all_time")  # all_time, weekly, daily
    limit = int(request.args.get("limit", 100))
    
    query = Score.query.filter_by(game_mode=game_mode)
    
    # Filter by timeframe
    if timeframe == "daily":
        cutoff = datetime.utcnow() - timedelta(days=1)
        query = query.filter(Score.timestamp >= cutoff)
    elif timeframe == "weekly":
        cutoff = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Score.timestamp >= cutoff)
    
    # Order by score DESC, then streak DESC, then timestamp ASC (earlier submission wins ties)
    scores = query.order_by(
        Score.score.desc(),
        Score.streak.desc(),
        Score.timestamp.asc()
    ).limit(limit).all()
    
    # Add rank to each entry
    results = []
    for idx, score_entry in enumerate(scores, start=1):
        score_dict = score_entry.to_dict()
        score_dict['rank'] = idx
        results.append(score_dict)
    
    return jsonify(results)

@app.route("/guess", methods=["POST"])
def guess():
    user_guess = request.json["guess"].upper().replace(" ", "").replace("/", "")
    
    # Stateless validation: prefer mana cost sent by client (for queue/prefetch scenarios)
    # Secure validation using Token
    token = request.json.get("token")
    if not token:
        return jsonify({"error": "Missing game token"}), 400
    
    card_data = verify_card_token(token)
    if not card_data:
        return jsonify({"error": "Invalid or expired token"}), 400

    correct_cost = card_data["mana_cost"].upper().replace(" ", "").replace("/", "")

    allow_anagrams = request.json.get("allow_anagrams", False)
    
    if allow_anagrams:
        is_correct = normalize_mana_cost(user_guess) == normalize_mana_cost(correct_cost)
    else:
        is_correct = user_guess == correct_cost

    result = {}
    if is_correct:
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
    # card_data comes from token now
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
    result["scryfall_uri"] = card_data.get("scryfall_uri", "")

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
