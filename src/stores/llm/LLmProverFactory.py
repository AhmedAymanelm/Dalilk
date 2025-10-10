from .llmEnum import LLMType
from .providers import CohereProvider, OpenAIProvider



class LLmProverFactory:
    def __init__(self, config:dict):
        self.config = config

    def create(self, Provider: str = None, provider: str = None):
        # accept either 'Provider' or 'provider' for backward compatibility
        name = (Provider or provider or "").lower()
        if name == LLMType.OPENAI.value:
            return OpenAIProvider(
                api_key= self.config.OPENAI_API_KEY,
                api_url= self.config.OPENAI_API_URL,
                defult_generation_temperature= self.config.OPENAI_DEFAULT_TEMPERATURE,
                defult_input_max_character= self.config.OPENAI_DEFAULT_INPUT_MAX_CHARACTER,
                defult_output_max_character= self.config.OPENAI_DEFAULT_OUTPUT_MAX_CHARACTER
            )

        if name == LLMType.COhere.value:
            return CohereProvider(
                api_key= self.config.COHERE_API_KEY,
                defult_generation_temperature= self.config.COHERE_DEFAULT_TEMPERATURE,
                defult_input_max_character= self.config.COHERE_DEFAULT_INPUT_MAX_CHARACTER,
                defult_output_max_character= self.config.COHERE_DEFAULT_OUTPUT_MAX_CHARACTER
            )

        # if name == LLMType.Groq.value:
        #     return GroqProvider(
        #         api_key= self.config.GROQ_API_KEY,
        #         api_url= self.config.GROQ_API_URL,
        #         defult_generation_temperature= self.config.GROQ_DEFAULT_TEMPERATURE,
        #         defult_input_max_character= self.config.GROQ_DEFAULT_INPUT_MAX_CHARACTER,
        #         defult_output_max_character= self.config.GROQ_DEFAULT_OUTPUT_MAX_CHARACTER
        #     )

        return None
