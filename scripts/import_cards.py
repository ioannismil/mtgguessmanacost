"""
Import Scryfall bulk card data into local PostgreSQL database

Usage:
    python scripts/import_cards.py

This will:
1. Download the latest "Default Cards" bulk data from Scryfall (~30-40 MB compressed)
2. Import all cards into the 'cards' table
3. Skip tokens, emblems, and art series cards
4. Take approximately 10-15 minutes to complete
"""

import json
import requests
import sys
import os

# Add parent directory to path to import from app
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
    print(f"📅 Updated: {default_cards.get('updated_at', 'unknown')}")
    print(f"⬇️  Downloading from: {download_url}")
    print("   This may take a few minutes...")
    
    # Download with progress
    filename = 'bulk_cards.json'
    
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                f.write(chunk)
                downloaded += len(chunk)
                
                # Show progress every 5 MB
                if downloaded % (5 * 1024 * 1024) < block_size:
                    progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                    print(f"   Downloaded: {downloaded / (1024*1024):.1f} MB ({progress:.0f}%)")
        
        print(f"✅ Download complete: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)


def import_to_database(filepath):
    """Import cards from JSON file to database"""
    print(f"\n📂 Loading {filepath}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            cards_data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load JSON: {e}")
        sys.exit(1)
    
    print(f"📊 Found {len(cards_data)} total entries")
    print("🔧 Filtering and importing cards...")
    print("   (Skipping tokens, emblems, and art series)")
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        batch = []
        imported_count = 0
        skipped_count = 0
        
        for idx, card_data in enumerate(cards_data):
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
                # Parse released_at date string to Python date object
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
                    released_at=released_at,  # Use parsed date object
                    scryfall_uri=card_data.get('scryfall_uri')
                )
                
                batch.append(card)
                imported_count += 1
                
                # Commit in batches of 1000
                if len(batch) >= 1000:
                    try:
                        db.session.bulk_save_objects(batch)
                        db.session.commit()
                        print(f"   Imported {imported_count:,} cards ({skipped_count:,} skipped)...")
                        batch = []
                    except Exception as e:
                        print(f"⚠️  Batch commit error: {e}")
                        db.session.rollback()
                        batch = []
                    
            except Exception as e:
                print(f"⚠️  Error importing card {card_data.get('name', 'unknown')}: {e}")
                db.session.rollback()  # Rollback session after error
                continue
        
        # Commit remaining
        if batch:
            try:
                db.session.bulk_save_objects(batch)
                db.session.commit()
            except Exception as e:
                print(f"⚠️  Final batch commit error: {e}")
                db.session.rollback()
        
        print(f"\n✅ Import complete!")
        print(f"   📊 Imported: {imported_count:,} cards")
        print(f"   ⏭️  Skipped: {skipped_count:,} non-playable cards")
        
        # Verify
        total_in_db = Card.query.count()
        print(f"   💾 Total in database: {total_in_db:,} cards")


def main():
    print("=" * 60)
    print(" SCRYFALL BULK CARD IMPORT")
    print("=" * 60)
    print()
    
    # Check if file already exists
    if os.path.exists('bulk_cards.json'):
        response = input("⚠️  bulk_cards.json already exists. Re-download? (y/N): ")
        if response.lower() == 'y':
            filepath = download_bulk_data()
        else:
            filepath = 'bulk_cards.json'
            print(f"✅ Using existing file: {filepath}")
    else:
        filepath = download_bulk_data()
    
    print()
    import_to_database(filepath)
    
    print()
    print("=" * 60)
    print("🎉 All done! You can now set USE_LOCAL_CARDS=True in app.py")
    print("=" * 60)


if __name__ == '__main__':
    main()
