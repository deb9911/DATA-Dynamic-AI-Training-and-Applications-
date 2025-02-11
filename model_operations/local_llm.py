from llama_cpp import Llama
import gc


class LocalLlmOperation():
    def load_llm(self):
        model_path = r'C:\Users\DebashisBiswas\Documents\small llm\llama-2-7b-chat.Q2_K.gguf'

        try:
            llm = Llama(
                model_path=model_path,
                n_ctx=2048,  # Context size
                n_threads=4,  # Number of CPU assigned to this task
            )
            return llm
        except Exception as e:
            print(f"Error loading LLaMA model: {e}")
            return None

    def generate_text(self):
        llm = self.load_llm()
        prompt = 'Hello, how are you today?'
        # output_data = output["text"]
        try:
            output = llm(prompt, max_tokens=2048, temperature=0.7)
            generated_text = output["choices"][0]["text"]
            print(f'Output:\t{generated_text}')
            # print(f'Output:\t{output["choices"][0]["text"]}')
            return generated_text
        except Exception as KeyError:
            print(f'Whole output\t:{output}')
            return None
        except Exception as KeyboardInterrupt:
            print(f'Keyboard interruption')
            return None
        finally:
            del llm  # Explicitly delete the LLaMA object
            gc.collect()
            print('Process completed')

        # return output_data


if __name__ == '__main__':
    local_llm_obj = LocalLlmOperation()
    local_llm_obj.generate_text()

