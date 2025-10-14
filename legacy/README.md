# Legacy Files

This directory contains the original Manuelita scraping scripts and data
that were replaced by the new AI engineering pipeline.

## Original Structure

- `scrape_manuelita.py` - Original corporate content scraper
- `scrape_manuelita_news.py` - Original news content scraper  
- `cleaner_md.py` - Original corporate content cleaner
- `news_cleaner_md.py` - Original news content cleaner
- `manuelita_content/` - Original scraped corporate content (39 files)
- `manuelita_news_content/` - Original scraped news content (138+ files)
- `cleaned_manuelita_content/` - Original cleaned corporate content
- `manuelita_news_content_cleaned/` - Original cleaned news content

## Migration to AI Engineering Pipeline

These files have been replaced by the new structured pipeline in:
- `src/manuelita_scraper/` - New modular pipeline architecture
- `configs/` - Environment-based configuration
- `data/` - Organized data storage
- `Makefile` - Updated automation

The new pipeline provides the same functionality with:
- Better organization and maintainability
- Environment configuration support
- Comprehensive logging and monitoring
- CLI interface for easy usage
- Modular ETL architecture

## Usage

To use the legacy scripts directly:
```bash
cd legacy/
python scrape_manuelita.py
python scrape_manuelita_news.py
```

However, it's recommended to use the new pipeline:
```bash
make pipeline-full
```
