from transformers import AutoModelForCausalLM, AutoTokenizer


class LlamaModelOperation():
    def __init__(self, model_name="decapoda-research/llama-3-70b-instruct-titan-0.1", hc_token='********'):
        self.model_name = model_name
        self.hc_token = hc_token
        self.model = None 
        self.tokenizer = None

    def load_model(self):
        if self.model is None:
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, token=self.hc_token)

    def get_response(self):
        self.load_model()  # Load the model only when needed

        prompt = "Hello, how are you today?"
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids

        # Generate text
        generated_ids = self.model.generate(
            input_ids=input_ids,
            max_length=128,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.0
        )

        # Decode the generated IDs back to text
        generated_text = self.tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        print(generated_text)

    def unload_model(self):
        if self.model is not None:
            del self.model
            self.model = None
            self.tokenizer = None


if __name__ == '__main__':
    llama_obj = LlamaModelOperation()
    llama_obj.get_response()
    llama_obj.unload_model()

