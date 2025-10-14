# Manuelita Scraper - AI Engineering Pipeline

AI-powered web scraping pipeline for Manuelita corporate content extraction.

## Features

- **Complete ETL Pipeline**: Extract → Transform → Load architecture
- **Intelligent Content Extraction**: Corporate and news content with auto-discovery
- **Advanced Content Cleaning**: Date-preserving transformers with configurable patterns
- **Environment Configuration**: Development and production settings
- **Structured Logging**: Performance monitoring and error tracking
- **CLI Interface**: Easy-to-use command-line tools

## Quick Start

```bash
# Install dependencies
uv sync

# Run the example demo
python example_usage.py

# Use CLI interface
python -m manuelita_scraper.cli --help
```

## Usage Examples

```bash
# Run complete pipeline
python -m manuelita_scraper.cli pipeline --type full

# Extract only corporate content
python -m manuelita_scraper.cli extract --type corporate

# Clean existing content
python -m manuelita_scraper.cli clean --input-dir manuelita_content --output-dir cleaned

# Check pipeline status
python -m manuelita_scraper.cli status
```

## Architecture

- **Extractors**: Web scraping with session management and rate limiting
- **Transformers**: Content cleaning with specialized corporate and news processors
- **Loaders**: Organized file output with metadata generation
- **Pipeline**: Orchestrates complete ETL workflow
- **Configuration**: YAML-based environment management

## Development

This project follows AI engineering best practices with structured logging, 
configuration management, and modular architecture.