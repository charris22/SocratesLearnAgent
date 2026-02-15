"""Azure OpenAI client factory with DefaultAzureCredential support."""

from openai import AsyncAzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from app.config import get_settings


_client: AsyncAzureOpenAI | None = None


def get_openai_client() -> AsyncAzureOpenAI:
    """Return a singleton AsyncAzureOpenAI client.

    Uses API key auth if AZURE_OPENAI_API_KEY is set,
    otherwise uses DefaultAzureCredential (recommended for production).
    """
    global _client
    if _client is not None:
        return _client

    settings = get_settings()

    if settings.use_key_auth:
        _client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )
    else:
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )
        _client = AsyncAzureOpenAI(
            azure_ad_token_provider=token_provider,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
        )

    return _client
