#!/usr/bin/env python3
"""
Example usage of the Manuelita Scraper Pipeline

This script demonstrates how to use the new AI engineering pipeline.
"""

import sys
sys.path.insert(0, 'src')

from manuelita_scraper import ManuelitaPipeline


def main():
    """Demonstrate pipeline usage."""
    print("🚀 Manuelita Scraper Pipeline Demo")
    print("=" * 50)
    
    try:
        # Initialize pipeline with development environment
        print("1. Initializing pipeline...")
        pipeline = ManuelitaPipeline(environment="development")
        
        # Show pipeline status
        print("\n2. Pipeline Status:")
        status = pipeline.get_pipeline_status()
        print(f"   Corporate URLs configured: {status['corporate_urls_configured']}")
        print(f"   News URLs configured: {status['news_urls_configured']}")
        print(f"   Output directory: {status['output_directory']}")
        
        # Run a simple test - extract just a few corporate pages
        print("\n3. Testing corporate extraction...")
        corporate_data = pipeline.extract_corporate_content()
        print(f"   ✅ Extracted {len(corporate_data)} corporate pages")
        
        if corporate_data:
            # Transform the extracted content
            print("\n4. Testing content transformation...")
            transformed_data = pipeline.transform_corporate_content(corporate_data[:2])  # Just first 2 items
            print(f"   ✅ Transformed {len(transformed_data)} pages")
            
            # Load the transformed content
            print("\n5. Testing content loading...")
            output_paths = pipeline.load_content(transformed_data, "demo")
            print(f"   ✅ Loaded {len(output_paths)} files")
            print(f"   Files saved to: {output_paths[0] if output_paths else 'None'}")
        
        print("\n🎉 Demo completed successfully!")
        print("\nTo use the CLI interface:")
        print("   python -m manuelita_scraper.cli --help")
        print("   python -m manuelita_scraper.cli pipeline --type corporate")
        print("   python -m manuelita_scraper.cli status")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        print("\nThis is normal if you haven't installed dependencies yet.")
        print("To install: uv sync")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())