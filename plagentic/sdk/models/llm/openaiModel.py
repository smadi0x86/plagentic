from plagentic.sdk.models.llm.baseModel import LLMModel
from plagentic.sdk.common.enums import ModelApiBase


class OpenAIModel(LLMModel):
    def __init__(self, model: str, api_key: str, api_base: str = None):
        api_base = api_base or ModelApiBase.OPENAI.value
        super().__init__(model, api_key=api_key, api_base=api_base)
