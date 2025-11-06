# Manuelita Scraper - AI Engineering Pipeline Makefile

# Setup and dependencies
setup:
	uv sync

install: setup

# Pipeline operations using new AI engineering structure
pipeline-full:
	--> uv run python -m manuelita_scraper.cli pipeline --type full
	uv run python -m manuelita_scraper.cli pipeline --type full --env development

pipeline-corporate:
	uv run python -m manuelita_scraper.cli pipeline --type corporate --env development

pipeline-news:
	uv run python -m manuelita_scraper.cli pipeline --type news --env development

# Individual pipeline steps
extract-corporate:
	uv run python -m manuelita_scraper.cli extract --type corporate --env development

extract-news:
	uv run python -m manuelita_scraper.cli extract --type news --env development

# Content cleaning operations
clean-corporate:
	--> uv run python -m manuelita_scraper.cli clean --input-dir data/raw/processed/corporate --output-dir data/cleaned/corporate --type corporate
	uv run python -m manuelita_scraper.cli clean --input-dir manuelita_content --output-dir data/cleaned/corporate --type corporate

clean-news:
	--> uv run python -m manuelita_scraper.cli clean --input-dir data/raw/processed/news --output-dir data/cleaned/news --type news
	uv run python -m manuelita_scraper.cli clean --input-dir manuelita_news_content --output-dir data/cleaned/news --type news

# Pipeline status and monitoring
status:
	uv run python -m manuelita_scraper.cli --env development status

config:
	uv run python -m manuelita_scraper.cli --env development config

# Testing and development
test-demo:
	uv run python example_usage.py

count-files:
	uv run python -m manuelita_scraper.cli count manuelita_content

# Repository maintenance
cleanup:
	uv run python scripts/cleanup_repository.py

# Legacy support (using old scripts - will be moved to legacy/ after cleanup)
legacy-scraping:
	uv run python legacy/scrape_manuelita.py

legacy-news-scraping:
	uv run python legacy/scrape_manuelita_news.py

# Production pipeline runs
production-full:
	uv run python -m manuelita_scraper.cli pipeline --type full --env production

production-corporate:
	uv run python -m manuelita_scraper.cli pipeline --type corporate --env production

production-news:
	uv run python -m manuelita_scraper.cli pipeline --type news --env production

# Help target
help:
	@echo "Manuelita Scraper - AI Engineering Pipeline"
	@echo "=========================================="
	@echo "Setup:"
	@echo "  setup              - Install dependencies with uv"
	@echo ""
	@echo "Development Pipeline:"
	@echo "  pipeline-full       - Run complete ETL pipeline (corporate + news)"
	@echo "  pipeline-corporate  - Run corporate content pipeline"
	@echo "  pipeline-news       - Run news content pipeline"
	@echo ""
	@echo "Individual Operations:"
	@echo "  extract-corporate   - Extract corporate content only"
	@echo "  extract-news        - Extract news content only"
	@echo "  clean-corporate     - Clean existing corporate content"
	@echo "  clean-news          - Clean existing news content"
	@echo ""
	@echo "Monitoring:"
	@echo "  status              - Show pipeline status"
	@echo "  config              - Show configuration"
	@echo "  count-files         - Count files in directories"
	@echo ""
	@echo "Testing:"
	@echo "  test-demo           - Run example demo script"
	@echo ""
	@echo "Repository Maintenance:"
	@echo "  cleanup             - Move old files to legacy/ directory"
	@echo ""
	@echo "Production:"
	@echo "  production-full     - Run full pipeline in production mode"
	@echo "  production-corporate - Run corporate pipeline in production mode"
	@echo "  production-news     - Run news pipeline in production mode"
	@echo ""
	@echo "Legacy Support:"
	@echo "  legacy-scraping     - Run old scrape_manuelita.py script"
	@echo "  legacy-news-scraping - Run old scrape_manuelita_news.py script"

.DEFAULT_GOAL := help
