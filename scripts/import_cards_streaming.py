"""
Memory-efficient streaming import for Scryfall bulk data

This version processes cards one at a time instead of loading the entire JSON into memory.
Suitable for low-memory environments like Render's free tier.

Usage:
    python scripts/import_cards_streaming.py
"""

import json
import requests
import sys
import os
import ijson  # Streaming JSON parser

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import db, Card
from app import app


def download_bulk_data():
    """Download latest bulk data from Scryfall"""
    print("🔍 Fetching bulk data info from Scryfall...")
    
    try:
        response = requests.get('https://api.scryfall.com/bulk-data')
        response.raise_for_status()
        bulk_info = response.json()
    except Exception as e:
        print(f"❌ Failed to fetch bulk data info: {e}")
        sys.exit(1)
    
    # Find "Default Cards" entry
    default_cards = next(
        (item for item in bulk_info['data'] if item['type'] == 'default_cards'),
        None
    )
    
    if not default_cards:
        print("❌ Could not find 'default_cards' bulk data")
        sys.exit(1)
    
    download_url = default_cards['download_uri']
    file_size_mb = default_cards.get('size', 0) / (1024 * 1024)
    
    print(f"📦 Found bulk data: {default_cards['name']}")
    print(f"📏 Size: {file_size_mb:.1f} MB")
    print(f"⬇️  Downloading from: {download_url}")
    
    filename = 'bulk_cards.json'
    
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                
                if downloaded % (5 * 1024 * 1024) < 8192:
                    progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                    print(f"   Downloaded: {downloaded / (1024*1024):.1f} MB ({progress:.0f}%)")
        
        print(f"✅ Download complete: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)


def import_to_database_streaming(filepath):
    """Import cards using streaming parser (memory efficient)"""
    print(f"\n📂 Opening {filepath} for streaming import...")
    print("💾 This uses minimal memory by processing one card at a time")
    
    with app.app_context():
        db.create_all()
        
        batch = []
        imported_count = 0
        skipped_count = 0
        
        # Stream parse the JSON file
        with open(filepath, 'rb') as f:
            # ijson.items streams through array items one at a time
            parser = ijson.items(f, 'item')
            
            for card_data in parser:
                # Skip non-playable cards
                layout = card_data.get('layout', '')
                if layout in ['token', 'emblem', 'art_series', 'double_faced_token']:
                    skipped_count += 1
                    continue
                
                # Skip cards without images
                if 'image_uris' not in card_data:
                    skipped_count += 1
                    continue
                
                try:
                    # Parse date
                    released_at = None
                    if card_data.get('released_at'):
                        from datetime import datetime
                        released_at = datetime.strptime(card_data['released_at'], '%Y-%m-%d').date()
                    
                    # Create Card object
                    card = Card(
                        id=card_data['id'],
                        name=card_data['name'],
                        mana_cost=card_data.get('mana_cost'),
                        cmc=card_data.get('cmc'),
                        colors=json.dumps(card_data.get('colors', [])),
                        color_identity=json.dumps(card_data.get('color_identity', [])),
                        type_line=card_data.get('type_line'),
                        oracle_text=card_data.get('oracle_text'),
                        power=card_data.get('power'),
                        toughness=card_data.get('toughness'),
                        set_code=card_data.get('set'),
                        set_name=card_data.get('set_name'),
                        rarity=card_data.get('rarity'),
                        image_normal=card_data.get('image_uris', {}).get('normal'),
                        image_art_crop=card_data.get('image_uris', {}).get('art_crop'),
                        prices_usd=card_data.get('prices', {}).get('usd'),
                        prices_usd_foil=card_data.get('prices', {}).get('usd_foil'),
                        legalities=json.dumps(card_data.get('legalities', {})),
                        released_at=released_at,
                        scryfall_uri=card_data.get('scryfall_uri')
                    )
                    
                    batch.append(card)
                    imported_count += 1
                    
                    # Commit in batches of 500 (smaller batches for lower memory)
                    if len(batch) >= 500:
                        try:
                            db.session.bulk_save_objects(batch)
                            db.session.commit()
                            print(f"   ✅ Imported {imported_count:,} cards ({skipped_count:,} skipped)")
                            batch = []
                        except Exception as e:
                            print(f"⚠️  Batch error: {e}")
                            db.session.rollback()
                            batch = []
                        
                except Exception as e:
                    # Skip problematic cards
                    continue
        
        # Commit remaining
        if batch:
            try:
                db.session.bulk_save_objects(batch)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
        
        print(f"\n✅ Import complete!")
        print(f"   📊 Imported: {imported_count:,} cards")
        print(f"   ⏭️  Skipped: {skipped_count:,} cards")
        
        total_in_db = Card.query.count()
        print(f"   💾 Total in database: {total_in_db:,} cards")


def main():
    print("=" * 60)
    print(" SCRYFALL BULK IMPORT (STREAMING - LOW MEMORY)")
    print("=" * 60)
    print()
    
    # Check for ijson
    try:
        import ijson
    except ImportError:
        print("❌ Missing required package: ijson")
        print("   Install with: pip install ijson")
        sys.exit(1)
    
    # Check if file exists
    if os.path.exists('bulk_cards.json'):
        response = input("⚠️  bulk_cards.json exists. Re-download? (y/N): ")
        if response.lower() == 'y':
            filepath = download_bulk_data()
        else:
            filepath = 'bulk_cards.json'
            print(f"✅ Using existing file: {filepath}")
    else:
        filepath = download_bulk_data()
    
    print()
    import_to_database_streaming(filepath)
    
    print()
    print("=" * 60)
    print("🎉 Done! Set USE_LOCAL_CARDS=true in Render")
    print("=" * 60)


if __name__ == '__main__':
    main()
