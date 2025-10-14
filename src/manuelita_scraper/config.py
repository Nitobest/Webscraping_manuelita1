"""
Configuration Management Module

This module handles loading, validation, and management of configuration files
for the Manuelita scraper pipeline.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator


class ScrapingTargets(BaseModel):
    """Configuration for scraping targets."""
    corporate_urls: list[str] = Field(default_factory=list)
    news_base_urls: list[str] = Field(default_factory=list)
    excluded_patterns: list[str] = Field(default_factory=list)


class ScrapingSettings(BaseModel):
    """Configuration for scraping behavior."""
    request_delay: float = Field(default=2.0, ge=0.5, le=10.0)
    timeout: int = Field(default=30, ge=5, le=60)
    max_retries: int = Field(default=3, ge=0, le=5)
    user_agent: str = Field(default="Mozilla/5.0 (compatible; ManuelitaScraper/1.0)")
    
    @validator('user_agent')
    def validate_user_agent(cls, v):
        if len(v) < 10:
            raise ValueError("User agent must be at least 10 characters")
        return v


class OutputSettings(BaseModel):
    """Configuration for output handling."""
    base_directory: str = Field(default="data/raw")
    file_format: str = Field(default="markdown", pattern="^(markdown|html|json)$")
    include_metadata: bool = Field(default=True)


class ScrapingConfig(BaseModel):
    """Main scraping configuration."""
    targets: ScrapingTargets = Field(default_factory=ScrapingTargets)
    settings: ScrapingSettings = Field(default_factory=ScrapingSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)


class CleaningPattern(BaseModel):
    """Configuration for a single cleaning pattern."""
    name: str
    pattern: str
    replacement: str = ""


class CleaningPatterns(BaseModel):
    """Configuration for content cleaning patterns."""
    remove_navigation: bool = Field(default=True)
    remove_social_media: bool = Field(default=True)
    preserve_dates: bool = Field(default=True)
    custom_patterns: list[CleaningPattern] = Field(default_factory=list)


class CleaningConfig(BaseModel):
    """Configuration for content cleaning."""
    patterns: CleaningPatterns = Field(default_factory=CleaningPatterns)


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = Field(default="text", pattern="^(json|text)$")
    file_path: str = Field(default="logs/application.log")
    console_output: bool = Field(default=True)


class MonitoringConfig(BaseModel):
    """Configuration for monitoring and metrics."""
    metrics_enabled: bool = Field(default=True)
    error_tracking: bool = Field(default=True)
    performance_tracking: bool = Field(default=True)


class AppConfig(BaseModel):
    """Main application configuration."""
    scraping: ScrapingConfig = Field(default_factory=ScrapingConfig)
    cleaning: CleaningConfig = Field(default_factory=CleaningConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)


class ConfigManager:
    """Manages application configuration loading and validation."""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.environments_dir = self.config_dir / "environments"
        self.schemas_dir = self.config_dir / "schemas"
        self._config: Optional[AppConfig] = None
    
    def load_environment_config(self, environment: str = "development") -> AppConfig:
        """
        Load configuration for a specific environment.
        
        Args:
            environment: Environment name (development, production, etc.)
            
        Returns:
            Validated application configuration
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValidationError: If configuration is invalid
        """
        config_file = self.environments_dir / f"{environment}.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Validate and create configuration object
        self._config = AppConfig(**config_data)
        return self._config
    
    def get_config(self) -> AppConfig:
        """Get the current loaded configuration."""
        if self._config is None:
            self._config = self.load_environment_config()
        return self._config
    
    def reload_config(self, environment: str = "development") -> AppConfig:
        """Reload configuration from file."""
        return self.load_environment_config(environment)
    
    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> AppConfig:
        """Create configuration from dictionary."""
        return AppConfig(**config_dict)
    
    @staticmethod
    def from_env() -> AppConfig:
        """Load configuration from environment variables."""
        # This would implement loading from environment variables
        # For now, return default configuration
        return AppConfig()
    
    def create_directories(self) -> None:
        """Create necessary directories based on configuration."""
        config = self.get_config()
        
        # Create output directory
        output_dir = Path(config.scraping.output.base_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logs directory
        log_path = Path(config.logging.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create data processing directories
        for subdir in ["processed", "cleaned"]:
            (Path("data") / subdir).mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config_manager = ConfigManager()

def get_config(environment: Optional[str] = None) -> AppConfig:
    """Get the global configuration instance."""
    if environment:
        return _config_manager.load_environment_config(environment)
    return _config_manager.get_config()


def init_config(environment: str = "development") -> AppConfig:
    """Initialize the global configuration."""
    config = _config_manager.load_environment_config(environment)
    _config_manager.create_directories()
    return config