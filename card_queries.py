"""
Helper functions for querying cards from local database

These functions replicate the Scryfall API behavior but query the local PostgreSQL database instead.
"""

from database import db, Card

def get_card_from_database(selected_set=None, colors_filter=None, formats_filter=None, game_mode=None):
    """
    Query a random card from the local database with filters
    
    Args:
        selected_set: Set code (e.g., 'mid')
        colors_filter: Color filter string from frontend (e.g., 'c<=UBR')
        formats_filter: Comma-separated format list (e.g., 'standard,modern')
        game_mode: Game mode to optimize query for
    
    Returns:
        dict: Card data in Scryfall-compatible format
    """
    query = Card.query
    
    # Filter by set
    if selected_set:
        query = query.filter(Card.set_code == selected_set.lower())
    
    # Filter by colors (complex)
    if colors_filter:
        query = apply_color_filter(query, colors_filter)
    
    # Filter by format legalities
    if formats_filter:
        query = apply_format_filter(query, formats_filter)
    
    # Game mode specific filters
    if game_mode == 'price_is_right':
        # Need cards with USD price
        query = query.filter(
            (Card.prices_usd.isnot(None)) | (Card.prices_usd_foil.isnot(None))
        )
        # Exclude lands
        query = query.filter(~Card.type_line.like('%Land%'))
    else:
        # Need cards with mana cost
        query = query.filter(Card.mana_cost.isnot(None))
        query = query.filter(~Card.type_line.like('%Land%'))
    
    # Get random card using PostgreSQL's random()
    card = query.order_by(db.func.random()).first()
    
    if not card:
        return None
    
    return card.to_dict()


def apply_color_filter(query, colors_filter):
    """
    Apply color filtering to the query
    
    Color filter format from frontend:
    - "c<=UBR" means colors must be subset of U, B, R
    - "-c:W" means exclude white
    - "-c:C" means exclude colorless
    
    Examples:
    - "c<=U -c:W -c:B -c:R -c:G -c:C" = exactly blue
    - "c<=UB" = blue and/or black only
    """
    # Parse the color filter
    # This is a simplified version - the full version would handle all Scryfall syntax
    
    if 'c<=' in colors_filter:
        # Extract allowed colors
        import re
        match = re.search(r'c<=(\w+)', colors_filter)
        if match:
            allowed_colors = list(match.group(1))
            
            # Card colors must be subset of allowed colors
            # This requires checking the JSON array
            for color in ['W', 'U', 'B', 'R', 'G']:
                if color not in allowed_colors:
                    # Exclude cards with this color
                    query = query.filter(~Card.colors.contains(f'"{color}"'))
    
    # Handle explicit exclusions
    if '-c:C' in colors_filter:
        # Exclude colorless (empty color array)
        query = query.filter(Card.colors != '[]')
    
    return query


def apply_format_filter(query, formats_filter):
    """
    Apply format legality filtering
    
    Args:
        formats_filter: Comma-separated list like "standard,modern"
    
    Returns cards that are legal in at least one of the specified formats
    """
    formats = [f.strip() for f in formats_filter.split(',') if f.strip()]
    
    if not formats:
        return query
    
    # Build OR conditions for format legality
    # legalities is stored as JSON: {"standard":"legal","modern":"not_legal",...}
    conditions = []
    for format_name in formats:
        # Check if JSON contains "format_name":"legal"
        conditions.append(Card.legalities.contains(f'"{format_name}":"legal"'))
    
    if conditions:
        query = query.filter(db.or_(*conditions))
    
    return query
