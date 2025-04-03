from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="deepseek-r1:32b")

result = llm.invoke("hello")
print(result)
