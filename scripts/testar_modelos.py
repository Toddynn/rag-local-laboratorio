"""Exercicio diagnostico: usa geracao e embeddings sem implementar um RAG."""
from ollama import chat, embed

resp = chat(
    model='qwen3:1.7b',
    messages=[{'role': 'user', 'content': 'Responda em uma frase: o que e um RAG?'}],
    options={'num_ctx': 2048, 'num_predict': 120},
)
print('\nRESPOSTA DO MODELO:\n', resp.message.content)

vectors = embed(model='embeddinggemma', input=['Instituto Federal', 'Universidade'])
print('\nVETORES GERADOS: ', len(vectors.embeddings))
print('DIMENSAO DO PRIMEIRO VETOR: ', len(vectors.embeddings[0]))
