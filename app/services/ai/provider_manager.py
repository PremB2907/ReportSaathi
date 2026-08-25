import os
import logging
import time
import requests
from app.services.ai.groq_provider import GroqProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_compatible_provider import OpenAICompatibleProvider
from app.services.ai.demo_provider import DemoProvider

logger = logging.getLogger(__name__)

class ProviderManager:
    """
    Orchestrates AI request dispatching and handles automatic fallback routing
    down the prioritized chain of active providers.
    """
    def __init__(self):
        self.providers = {
            "groq": GroqProvider(),
            "gemini": GeminiProvider(),
            "nvidia": OpenAICompatibleProvider(),
            "demo": DemoProvider()
        }
        
        # Read prioritize order
        order_str = os.environ.get("AI_PROVIDER_ORDER", "groq,gemini,nvidia,demo")
        self.order = [p.strip().lower() for p in order_str.split(",") if p.strip().lower() in self.providers]

    def get_provider(self, name):
        return self.providers.get(name)

    def get_status_info(self) -> dict:
        """
        Gathers configured status states for diagnostic utilities.
        Safe to render in both user-facing APIs and admin diagnostic boards.
        """
        details = {}
        healthy = False

        for name, provider in self.providers.items():
            health = provider.check_health()
            details[name] = {
                "configured": bool(getattr(provider, 'api_key', True) or name == "demo"),
                "available": health["available"],
                "reason": health.get("reason", "unknown")
            }
            if health["available"] and name != "demo":
                healthy = True
        
        # If demo is the only available option, healthy is True if demo is active
        if details.get("demo", {}).get("available"):
            healthy = True

        # Find active provider (first available in priority order)
        active_provider = "demo"
        for p_name in self.order:
            if details.get(p_name, {}).get("available"):
                active_provider = p_name
                break

        return {
            "healthy": healthy,
            "active_provider": active_provider,
            "providers": details
        }

    def _categorize_error(self, e) -> tuple:
        """
        Categorizes error types to prevent sensitive info disclosure.
        Returns: (category_str, http_status_int)
        """
        if isinstance(e, requests.exceptions.Timeout):
            return "TIMEOUT", 504
        if isinstance(e, requests.exceptions.ConnectionError):
            return "PROVIDER_UNAVAILABLE", 503
        if isinstance(e, requests.exceptions.HTTPError):
            status = e.response.status_code if e.response is not None else 500
            if status in [401, 403]:
                return "AUTHENTICATION_ERROR", status
            if status == 429:
                return "RATE_LIMIT", status
            if status == 404:
                return "MODEL_NOT_FOUND", status
            if status == 400:
                return "INVALID_REQUEST", status
            return "PROVIDER_UNAVAILABLE", status
        if isinstance(e, (json.JSONDecodeError, ValueError)):
            return "PARSING_ERROR", 200
        return "UNKNOWN_ERROR", 500

    def analyze_report(self, images, language="english", symptoms=None, patient_context=None) -> dict:
        """
        Tries report extraction in priority order, falling back on errors.
        """
        last_exception = None
        
        for name in self.order:
            provider = self.providers[name]
            
            # Check availability first (skip if not active)
            health = provider.check_health()
            if not health["available"]:
                continue

            logger.info(f"Dispatching analyze_report to provider: {name}")
            try:
                # Execution
                data = provider.analyze_report(images, language, symptoms, patient_context)
                if data and isinstance(data, dict) and "tests" in data:
                    return data
                raise ValueError("Returned data does not contain expected 'tests' block.")
            except Exception as ex:
                category, status = self._categorize_error(ex)
                last_exception = ex
                
                # Secure developer log
                logger.error(
                    f"AI Provider Failure Details | "
                    f"provider: {name} | "
                    f"error_category: {category} | "
                    f"HTTP_status: {status} | "
                    f"timestamp: {time.time()} | "
                    f"exception: {str(ex)}"
                )
                
                # Continue with the next provider in line
                continue

        # If we exhausted all options
        raise RuntimeError(
            "AI service is temporarily unavailable. All configured providers failed."
        ) from last_exception

    def ask_report(self, report_data, question, history=None, language="english") -> str:
        """
        Tries conversational chat completion in priority order.
        """
        last_exception = None
        
        for name in self.order:
            provider = self.providers[name]
            
            health = provider.check_health()
            if not health["available"]:
                continue

            logger.info(f"Dispatching ask_report to provider: {name}")
            try:
                answer = provider.ask_report(report_data, question, history, language)
                if answer:
                    return answer
                raise ValueError("Empty response returned.")
            except Exception as ex:
                category, status = self._categorize_error(ex)
                last_exception = ex
                
                logger.error(
                    f"AI Provider Chat Failure Details | "
                    f"provider: {name} | "
                    f"error_category: {category} | "
                    f"HTTP_status: {status} | "
                    f"timestamp: {time.time()} | "
                    f"exception: {str(ex)}"
                )
                continue

        raise RuntimeError(
            "Conversational assistant is temporarily unavailable."
        ) from last_exception
