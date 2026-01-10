from llama_cpp import Llama

llm = Llama(model_path="path/to/ggml-model.bin")
resp = llm("Hello there!", max_tokens=128)
print(resp['text'])
