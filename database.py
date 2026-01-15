from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
