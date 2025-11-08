from vllm import LLM, SamplingParams
from vllm.sampling_params import GuidedDecodingParams
from pydantic import BaseModel, ValidationError
import logging
from tenacity import retry, stop_after_attempt, wait_fixed
from openai import OpenAI
import time

logger = logging.getLogger(__name__)


class LanguageModel:
    """
    A wrapper class for LLMs to use either online or offline inference
    """
    def __init__(
        self,
        model: str,
        max_num_seqs: int=2,
        max_model_length: int=8192,
        tensor_parallel_size: int=1,
        max_num_batched_tokens: int=16384,
        online: bool=False,
        api_key: bool=None
    ) -> None:
        self.online = online
        if not self.online:
            self.max_num_seqs = max_num_seqs
            self.max_model_length = max_model_length
            self.tensor_parallel_size = tensor_parallel_size
            self.model = LLM(
                model=model, 
                max_num_seqs=max_num_seqs, 
                max_model_len=max_model_length, 
                tensor_parallel_size=tensor_parallel_size, 
                max_num_batched_tokens=max_num_batched_tokens, 
                enforce_eager=True)
        else:
            self.model=OpenAI(api_key=api_key)
        self.model_name = model

    
    def _generate_output(self, prompts: list, sampling_params: SamplingParams):
        outputs = self.model.generate(prompts=prompts, sampling_params=sampling_params)
        return outputs
    
    # @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def structured_response(self, message: list, schema: BaseModel, max_tokens: int=4096):
        rsps = []
        logger.info(f'MESSAGES: {message}')
        if not self.online:
            json_schema = schema.model_json_schema()
            guided_decoding_params_json = GuidedDecodingParams(json=json_schema)
            sampling_params_json = SamplingParams(guided_decoding=guided_decoding_params_json, max_tokens=max_tokens)
            generation = self._generate_output(message, sampling_params=sampling_params_json)
            for output in generation:
                output_text = output.outputs[0].text
                try:
                    rsp = schema.model_validate_json(output_text)  
                except ValidationError as e:
                    logger.error(e)
                    logger.error(generation)
                    rsps.append(None)
                rsps.append(rsp)
        else:
            time.sleep(1)
            effort = 'low' if self.model_name == 'o3' else 'minimal'
            for m in message:
                msg = [{"role": "user", "content": m}]
                response = self.model.responses.parse(
                    model=self.model_name,
                    reasoning={
                        "effort": effort
                    },
                    input = msg,
                    text_format=schema)
                rsp = response
                # if (response.refusal):
                #     print(response.refusal)
                #     logger.error(response.refusal)
                #     return None
                # else:
                rsps.append(rsp.output_parsed)
                logger.info(rsp)
        logger.info(f'RESPONSES: {rsps}')
        return rsps
