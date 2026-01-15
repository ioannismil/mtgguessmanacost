from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Score(db.Model):
    """Store player scores for leaderboards across all game modes"""
    __tablename__ = 'scores'
    
    id = db.Column(db.Integer, primary_key=True)
    game_mode = db.Column(db.String(50), nullable=False, index=True)
    username = db.Column(db.String(50), default='Anonymous', nullable=False)
    score = db.Column(db.Integer, nullable=False, index=True)
    streak = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    session_id = db.Column(db.String(100))  # For deduplication
    
    def to_dict(self):
        """Convert score record to dictionary for API responses"""
        return {
            'username': self.username,
            'score': self.score,
            'streak': self.streak,
            'timestamp': self.timestamp.isoformat(),
            'rank': None  # Calculated dynamically in API endpoint
        }
    
    def __repr__(self):
        return f'<Score {self.username}: {self.score} in {self.game_mode}>'


class Card(db.Model):
    """Store MTG card data from Scryfall bulk import"""
    __tablename__ = 'cards'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    mana_cost = db.Column(db.String(50))
    cmc = db.Column(db.Numeric(5, 2), index=True)
    colors = db.Column(db.Text)  # JSON array as string
    color_identity = db.Column(db.Text)  # JSON array as string
    type_line = db.Column(db.String(255))
    oracle_text = db.Column(db.Text)
    power = db.Column(db.String(10))
    toughness = db.Column(db.String(10))
    set_code = db.Column(db.String(10), index=True)
    set_name = db.Column(db.String(255))
    rarity = db.Column(db.String(20), index=True)
    image_normal = db.Column(db.Text)
    image_art_crop = db.Column(db.Text)
    prices_usd = db.Column(db.Numeric(10, 2))
    prices_usd_foil = db.Column(db.Numeric(10, 2))
    legalities = db.Column(db.Text)  # JSON object as string
    released_at = db.Column(db.Date)
    scryfall_uri = db.Column(db.Text)
    
    def to_dict(self):
        """Convert to format compatible with current app"""
        return {
            'id': self.id,
            'name': self.name,
            'mana_cost': self.mana_cost or '',
            'cmc': float(self.cmc) if self.cmc else 0,
            'colors': json.loads(self.colors) if self.colors else [],
            'color_identity': json.loads(self.color_identity) if self.color_identity else [],
            'type_line': self.type_line,
            'image': self.image_normal,
            'art_crop': self.image_art_crop,
            'prices': {
                'usd': str(self.prices_usd) if self.prices_usd else None,
                'usd_foil': str(self.prices_usd_foil) if self.prices_usd_foil else None
            },
            'scryfall_uri': self.scryfall_uri,
            'set': self.set_code,
            'set_name': self.set_name,
            'rarity': self.rarity,
            'power': self.power,
            'toughness': self.toughness
        }
    
    def __repr__(self):
        return f'<Card {self.name} ({self.set_code})>'

