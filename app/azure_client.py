"""Azure AI Foundry / Azure OpenAI client factory.

Supports two endpoint styles:
  - Azure AI Foundry inference  (*.services.ai.azure.com)  → /models/chat/completions
  - Standard Azure OpenAI       (*.openai.azure.com)       → /openai/deployments/…
"""

from openai import AsyncAzureOpenAI, AsyncOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from app.config import get_settings


_client: AsyncOpenAI | AsyncAzureOpenAI | None = None


def _is_foundry_endpoint(endpoint: str) -> bool:
    """Return True if the endpoint is an Azure AI Foundry / AI Services URL."""
    return "services.ai.azure.com" in endpoint or "models.ai.azure.com" in endpoint


def get_openai_client() -> AsyncOpenAI | AsyncAzureOpenAI:
    """Return a singleton chat-completions client.

    Automatically detects whether the endpoint is Azure AI Foundry (inference API)
    or standard Azure OpenAI and configures the right SDK client.
    """
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    endpoint = settings.azure_openai_endpoint.rstrip("/")

    if _is_foundry_endpoint(endpoint):
        # Azure AI Foundry / AI Services – uses /models/chat/completions
        base_url = f"{endpoint}/models"

        if settings.use_key_auth:
            _client = AsyncOpenAI(
                base_url=base_url,
                api_key=settings.azure_openai_api_key,
            )
        else:
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            _client = AsyncOpenAI(
                base_url=base_url,
                api_key="placeholder",  # required by SDK but not sent when using token
            )
            # Inject bearer-token auth via default headers
            _client._custom_headers = {  # type: ignore[attr-defined]
                "Authorization": f"Bearer {token_provider()}"
            }
    else:
        # Standard Azure OpenAI endpoint (*.openai.azure.com)
        if settings.use_key_auth:
            _client = AsyncAzureOpenAI(
                api_key=settings.azure_openai_api_key,
                azure_endpoint=endpoint,
                api_version=settings.azure_openai_api_version,
            )
        else:
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential, "https://cognitiveservices.azure.com/.default"
            )
            _client = AsyncAzureOpenAI(
                azure_ad_token_provider=token_provider,
                azure_endpoint=endpoint,
                api_version=settings.azure_openai_api_version,
            )

    return _client
