"""
OpenAI client configuration and initialization.
"""
import os
from openai import OpenAI
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Singleton OpenAI client wrapper."""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenAIClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            api_key = getattr(settings, 'OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))
            base_url = getattr(settings, 'OPENAI_BASE_URL', os.getenv('OPENAI_BASE_URL', None))
            
            if not api_key:
                logger.warning("OPENAI_API_KEY not set. OpenAI client will not work.")
            
            self._client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=60.0,
                max_retries=2
            )
            
            logger.info(f"OpenAI client initialized with base_url: {base_url or 'default'}")
    
    @property
    def client(self):
        """Get the OpenAI client instance."""
        return self._client
    
    def get_model_pricing(self, model_name):
        """
        Get pricing information for a model.
        
        Args:
            model_name: Name of the OpenAI model
            
        Returns:
            Dict with input_price and output_price per 1M tokens
        """
        # Pricing as of 2024 (per 1M tokens in USD)
        pricing = {
            'gpt-4o': {'input': 5.00, 'output': 15.00},
            'gpt-4o-mini': {'input': 0.150, 'output': 0.600},
            'gpt-4-turbo': {'input': 10.00, 'output': 30.00},
            'gpt-4': {'input': 30.00, 'output': 60.00},
            'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},
        }
        
        return pricing.get(model_name, {'input': 0.0, 'output': 0.0})
    
    def calculate_cost(self, model_name, input_tokens, output_tokens):
        """
        Calculate the cost of an API call.
        
        Args:
            model_name: Name of the OpenAI model
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        pricing = self.get_model_pricing(model_name)
        
        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']
        
        return input_cost + output_cost


def get_openai_client():
    """Get or create OpenAI client instance."""
    return OpenAIClient().client


def calculate_cost(model_name, input_tokens, output_tokens):
    """Helper function to calculate cost."""
    return OpenAIClient().calculate_cost(model_name, input_tokens, output_tokens)
