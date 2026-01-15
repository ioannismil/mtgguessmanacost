# Card Database Import

This directory contains scripts for importing Scryfall's bulk card data into the local PostgreSQL database.

## Quick Start

1. **Run the import script**:
   ```bash
   python scripts/import_cards.py
   ```

2. **Enable local cards** in production:
   - Set environment variable: `USE_LOCAL_CARDS=true`
   - Or modify `app.py` line 11

## What It Does

- Downloads ~40 MB of compressed card data from Scryfall
- Imports ~30,000-40,000 playable cards
- Takes approximately 10-15 minutes
- Creates `cards` table with full card data
- Skips tokens, emblems, and art series cards

## Files

- `import_cards.py` - Main import script
- `../card_queries.py` - Database query helpers  
- `../bulk_cards.json` - Downloaded data (git ignored)

## After Import

Test locally by setting in your environment or app.py:
```python
USE_LOCAL_CARDS = True
```

Then run your app and cards will be loaded from PostgreSQL instead of Scryfall API!

## Updating Cards

To refresh card data (when new sets release):
1. Delete `bulk_cards.json`
2. Run `python scripts/import_cards.py` again
3. It will download fresh data and re-import

## Production Deployment

On Render:
1. SSH into your Render instance or use a one-off job
2. Run: `python scripts/import_cards.py`
3. Set `USE_LOCAL_CARDS=true` environment variable in Render dashboard
4. Restart your web service
