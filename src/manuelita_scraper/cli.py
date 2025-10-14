"""
Command Line Interface for Manuelita Scraper

Provides a CLI for running the scraping pipeline operations.
"""

import click
import json
import sys
from pathlib import Path
from typing import Optional

from .pipeline import ManuelitaPipeline
from .transformers.corporate import CorporateTransformer
from .transformers.news import NewsTransformer
from .config import init_config


def print_json(data):
    """Pretty print JSON data."""
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


def print_success(message: str):
    """Print success message in green."""
    click.echo(click.style(f"✅ {message}", fg='green'))


def print_error(message: str):
    """Print error message in red."""
    click.echo(click.style(f"❌ {message}", fg='red'), err=True)


def print_warning(message: str):
    """Print warning message in yellow."""
    click.echo(click.style(f"⚠️ {message}", fg='yellow'))


@click.group()
@click.option('--env', '--environment', default='development', 
              help='Environment configuration to use (development/production)')
@click.pass_context
def cli(ctx, env):
    """Manuelita Scraper - AI-powered web scraping pipeline for Manuelita content extraction."""
    ctx.ensure_object(dict)
    ctx.obj['environment'] = env


@cli.command()
@click.option('--type', 'content_type', 
              type=click.Choice(['corporate', 'news', 'both']), 
              default='both',
              help='Type of content to extract')
@click.pass_context
def extract(ctx, content_type):
    """Extract content from configured URLs."""
    env = ctx.obj['environment']
    
    try:
        pipeline = ManuelitaPipeline(env)
        click.echo(f"🚀 Starting extraction with {env} environment...")
        
        if content_type == 'corporate':
            result = pipeline.extract_corporate_content()
            if result:
                print_success(f"Extracted {len(result)} corporate pages")
            else:
                print_warning("No corporate content extracted")
                
        elif content_type == 'news':
            result, discovered_links = pipeline.extract_news_content()
            if result:
                print_success(f"Extracted {len(result)} news items, discovered {len(discovered_links)} links")
            else:
                print_warning("No news content extracted")
                
        elif content_type == 'both':
            corporate_result = pipeline.extract_corporate_content()
            news_result, discovered_links = pipeline.extract_news_content()
            
            total_extracted = len(corporate_result) + len(news_result)
            print_success(f"Extracted {total_extracted} items total")
            click.echo(f"  - Corporate: {len(corporate_result)}")
            click.echo(f"  - News: {len(news_result)} (discovered {len(discovered_links)} links)")
            
    except Exception as e:
        print_error(f"Extraction failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--input-dir', required=True, 
              help='Input directory containing content to clean')
@click.option('--output-dir', required=True,
              help='Output directory for cleaned content') 
@click.option('--type', 'content_type',
              type=click.Choice(['corporate', 'news']),
              default='corporate',
              help='Type of content to clean')
@click.pass_context
def clean(ctx, input_dir, output_dir, content_type):
    """Clean existing content files."""
    env = ctx.obj['environment']
    
    try:
        config = init_config(env)
        
        if content_type == 'corporate':
            transformer = CorporateTransformer(config.cleaning)
        else:
            transformer = NewsTransformer(config.cleaning)
        
        click.echo(f"🧹 Cleaning {content_type} content...")
        click.echo(f"  Input: {input_dir}")
        click.echo(f"  Output: {output_dir}")
        
        results = transformer.transform_directory(input_dir, output_dir)
        
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        if successful == total:
            print_success(f"Successfully cleaned {successful}/{total} files")
        else:
            print_warning(f"Cleaned {successful}/{total} files ({total - successful} failed)")
            
        if successful < total:
            click.echo("\nFailed files:")
            for filename, success in results.items():
                if not success:
                    click.echo(f"  - {filename}")
                    
    except Exception as e:
        print_error(f"Cleaning failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--type', 'pipeline_type',
              type=click.Choice(['corporate', 'news', 'full']),
              default='full',
              help='Type of pipeline to run')
@click.pass_context
def pipeline(ctx, pipeline_type):
    """Run the complete ETL pipeline."""
    env = ctx.obj['environment']
    
    try:
        pipeline_instance = ManuelitaPipeline(env)
        click.echo(f"🏗️ Starting {pipeline_type} pipeline with {env} environment...")
        
        if pipeline_type == 'corporate':
            result = pipeline_instance.run_corporate_pipeline()
        elif pipeline_type == 'news':
            result = pipeline_instance.run_news_pipeline()
        else:  # full
            result = pipeline_instance.run_full_pipeline()
        
        if result['success']:
            print_success("Pipeline completed successfully!")
            
            if pipeline_type == 'full':
                click.echo(f"📊 Summary:")
                click.echo(f"  Total extracted: {result['total_extracted']}")
                click.echo(f"  Total loaded: {result['total_loaded']}")
                click.echo(f"  Corporate files: {result['corporate']['loaded_count']}")
                click.echo(f"  News files: {result['news']['loaded_count']}")
            else:
                click.echo(f"📊 Summary:")
                click.echo(f"  Extracted: {result.get('extracted_count', 0)}")
                click.echo(f"  Transformed: {result.get('transformed_count', 0)}")
                click.echo(f"  Loaded: {result.get('loaded_count', 0)}")
                
                if 'discovered_links_count' in result:
                    click.echo(f"  Discovered links: {result['discovered_links_count']}")
        else:
            print_error(f"Pipeline failed: {result.get('message', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Pipeline execution failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show pipeline status and configuration."""
    env = ctx.obj['environment']
    
    try:
        pipeline = ManuelitaPipeline(env)
        status_info = pipeline.get_pipeline_status()
        
        click.echo(f"📋 Pipeline Status ({env} environment)")
        click.echo("=" * 50)
        
        click.echo(f"Corporate URLs: {status_info['corporate_urls_configured']}")
        click.echo(f"News URLs: {status_info['news_urls_configured']}")
        click.echo(f"Output directory: {status_info['output_directory']}")
        click.echo(f"File format: {status_info['file_format']}")
        
        metrics = status_info.get('metrics_summary')
        if metrics:
            click.echo("\n📊 Metrics Summary:")
            click.echo(f"  Total duration: {metrics['total_duration']:.2f}s")
            
            if metrics['counters']:
                click.echo("  Counters:")
                for name, value in metrics['counters'].items():
                    click.echo(f"    {name}: {value}")
            
            if metrics['timings']:
                click.echo("  Average timings:")
                for name, timing_data in metrics['timings'].items():
                    avg_time = timing_data['average']
                    click.echo(f"    {name}: {avg_time:.2f}s")
        
    except Exception as e:
        print_error(f"Failed to get status: {str(e)}")
        sys.exit(1)


@cli.command()
@click.pass_context
def config(ctx):
    """Show current configuration."""
    env = ctx.obj['environment']
    
    try:
        config_obj = init_config(env)
        
        click.echo(f"⚙️ Configuration ({env} environment)")
        click.echo("=" * 50)
        
        # Convert pydantic model to dict for display
        config_dict = config_obj.dict()
        print_json(config_dict)
        
    except Exception as e:
        print_error(f"Failed to load configuration: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--pattern', default='*.md', help='File pattern to match')
def count(directory, pattern):
    """Count files in a directory."""
    try:
        path = Path(directory)
        files = list(path.glob(pattern))
        
        click.echo(f"📁 Directory: {directory}")
        click.echo(f"📄 Files matching '{pattern}': {len(files)}")
        
        if files:
            total_size = sum(f.stat().st_size for f in files)
            avg_size = total_size / len(files)
            
            click.echo(f"📊 Total size: {total_size:,} bytes")
            click.echo(f"📊 Average size: {avg_size:,.0f} bytes")
            
    except Exception as e:
        print_error(f"Failed to count files: {str(e)}")
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()