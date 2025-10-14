#!/usr/bin/env python3
"""
Repository Cleanup Script

This script organizes the repository by:
1. Moving old legacy files to a legacy/ directory
2. Keeping only the new AI engineering pipeline structure
3. Maintaining a clean, organized repository
"""

import os
import shutil
from pathlib import Path


def main():
    """Clean up the repository structure."""
    print("🧹 Cleaning up repository structure...")
    
    # Create legacy directory
    legacy_dir = Path("legacy")
    legacy_dir.mkdir(exist_ok=True)
    
    # Files and directories to move to legacy
    legacy_items = [
        # Old Python scripts
        "scrape_manuelita.py",
        "scrape_manuelita_news.py", 
        "cleaner_md.py",
        "news_cleaner_md.py",
        "main.py",
        
        # Old data directories
        "cleaned_manuelita_content",
        "manuelita_content", 
        "manuelita_news_content",
        "manuelita_news_content_cleaned",
        
        # Old documentation
        "COMPLETE_SCRAPING_SUMMARY.md",
        "Manuelita_Complete_Content_Summary.md",
        "Readme.txt",
        
        # Old discovery file
        "discovered_news_links.json",
    ]
    
    moved_items = []
    
    for item in legacy_items:
        item_path = Path(item)
        if item_path.exists():
            target_path = legacy_dir / item
            
            try:
                if item_path.is_dir():
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.move(str(item_path), str(target_path))
                    print(f"  📁 Moved directory: {item} → legacy/{item}")
                else:
                    shutil.move(str(item_path), str(target_path))
                    print(f"  📄 Moved file: {item} → legacy/{item}")
                
                moved_items.append(item)
                
            except Exception as e:
                print(f"  ❌ Error moving {item}: {e}")
        else:
            print(f"  ⏭️  Skipped (not found): {item}")
    
    # Create legacy README
    legacy_readme = legacy_dir / "README.md"
    with open(legacy_readme, "w") as f:
        f.write("""# Legacy Files

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
""")
    
    print(f"\n✅ Repository cleanup completed!")
    print(f"   📦 Moved {len(moved_items)} items to legacy/")
    print(f"   📝 Created legacy/README.md with documentation")
    
    # Show current structure
    print(f"\n📊 Current repository structure:")
    print("   📁 src/manuelita_scraper/ - New AI engineering pipeline")
    print("   📁 configs/ - Environment configurations") 
    print("   📁 data/ - Organized data storage")
    print("   📁 tests/ - Testing framework")
    print("   📁 docs/ - Documentation")
    print("   📁 legacy/ - Original files (for reference)")
    print("   📄 Makefile - Updated automation")
    print("   📄 README.md - Project documentation")
    print("   📄 example_usage.py - Usage examples")


if __name__ == "__main__":
    main()