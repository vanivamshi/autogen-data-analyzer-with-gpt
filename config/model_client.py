from autogen_ext.models.openai import OpenAIChatCompletionClient

from config.settings import MODEL_NAME, OPENAI_API_KEY


def get_model_client() -> OpenAIChatCompletionClient:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env or your environment.")
    return OpenAIChatCompletionClient(model=MODEL_NAME, api_key=OPENAI_API_KEY)
