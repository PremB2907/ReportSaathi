from abc import ABC, abstractmethod

class BaseAIProvider(ABC):
    """
    Abstract Base Class defining the standard interface for all AI model providers.
    """
    @abstractmethod
    def analyze_report(self, images, language="english", symptoms=None, patient_context=None) -> dict:
        """
        Extracts structured parameters, status classifications, and explanations from report images.
        """
        pass

    @abstractmethod
    def ask_report(self, report_data, question, history=None, language="english") -> str:
        """
        Answers conversational Q&A queries based on the extracted report data.
        """
        pass

    @abstractmethod
    def check_health(self) -> dict:
        """
        Performs diagnostic checks to see if the provider is configured, authenticated, and online.
        """
        pass

    @abstractmethod
    def test_connection(self) -> str:
        """
        Executes a tiny, harmless test request to verify connection without transmitting patient data.
        """
        pass
