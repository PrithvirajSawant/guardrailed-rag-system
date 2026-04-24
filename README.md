# Guardrailed RAG System  

> Multi-layer AI safety system combining RAG, LLM-based moderation, policy enforcement, and real-time alerting to ensure safe and controlled AI responses.


## System Layers

User input moderation → #Layer 1  
Agent Control (input guardrails) → #Layer 2  
Agent Control (output guardrails) → #Layer 3  
n8n alerting system → #Layer 4  


## Features

- Multi-layer AI safety (moderation + enforcement)  
- Prompt injection protection  
- Harmful output filtering  
- Sensitive data leakage prevention  
- Semantic search using FAISS + Nomic embeddings  
- Context-aware responses using RAG  
- Real-time alerting via n8n webhook  


## Architecture

User query  

LLM Moderation checks input  

Agent Control (PRE):  
- Blocks unsafe or injected prompts  

RAG Pipeline:  
- Query → embedding (Nomic)  
- Semantic search (FAISS)  
- Retrieve relevant documents  

LLM generates response using context  

Agent Control (POST):  
- Filters harmful / sensitive output  

Final response returned  

If unsafe:  
- Alert sent via n8n  


## Tech Stack

- Python
- LangChain
- FAISS (Vector Store)  
- Groq (Llama 4)  
- Ollama (Embeddings - nomic-embed-text)  
- Agent Control (Policy Enforcement)  
- n8n (Automation & Alerts)  
- Streamlit (UI)
- Docker