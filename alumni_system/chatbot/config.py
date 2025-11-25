"""
Chatbot configuration.
Uses environment variables for API keys.
"""

import os


def get_openai_config() -> dict:
    """
    Get OpenAI configuration from environment variables.
    
    Environment variables:
        - OPENAI_API_KEY: OpenAI API key (optional, for advanced NLP)
    
    Returns:
        Dictionary containing OpenAI configuration.
    """
    return {
        "api_key": os.environ.get("OPENAI_API_KEY", ""),
        "model": os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
    }


# Chatbot settings
MAX_RESULTS = int(os.environ.get("CHATBOT_MAX_RESULTS", "10"))
CONFIDENCE_THRESHOLD = float(os.environ.get("CHATBOT_CONFIDENCE_THRESHOLD", "0.5"))
