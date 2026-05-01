# End-TO-End chat app using Groq LPU and Ollama's embeddings with Streamlit

import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader, TextLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import time
import requests

import agent_control
from agent_control import control
from agent_control import ControlViolationError

load_dotenv()

groq_api_key = os.environ["GROQ_API_KEY"]
os.environ["USER_AGENT"] = "my-langchain-app"

agent_control.init(
    agent_name="moderated_rag_chatbot_v2",
    agent_description="RAG chatbot with moderation"
)

## Stramlit session_state
if "vectors" not in st.session_state:
    st.session_state.embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    st.session_state.loader = WebBaseLoader("https://docs.langchain.com/langsmith/home") #initializes the loader with the URL
    st.session_state.docs = st.session_state.loader.load() #get's converted into document object - not pdf, csv or .txt
    # We load (pdf, csv or .txt) files or pasre HTML content from web to convert it into document object.
    # If the document loaded has more than one page then that many document objects are created [list of documents].
    # load() return type is list of documents - So even if we have 1 doc. obj. it will return a "list with 1 doc. obj. inside".
    
    st.session_state.txt_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    st.session_state.final_doc = st.session_state.txt_splitter.split_documents(st.session_state.docs[:50])
    # print("-----------------------------")
    # print(st.session_state.final_doc[0])
    # print("-----------------------------")
    st.session_state.vectors = FAISS.from_documents(st.session_state.final_doc, st.session_state.embeddings)
    st.session_state.vectors.save_local("my_FAISS_vdb")

# st.title("ChatGroq Bot with Moderation and n8n Webhook Alerts")
# print("-----------------------------")
# print(st.session_state.final_doc[0])
# print("-----------------------------")

st.title("RAG ChatBot with Moderation")
llm = ChatGroq(groq_api_key = groq_api_key, model_name="meta-llama/llama-4-scout-17b-16e-instruct")

prompt = ChatPromptTemplate.from_template("""
Answer the questions based on the provided context.
Please provide the most accurate response based on the question.
If not found, respond by inferring from the model's knowledge (no more than 50 words).
Do not hallucinate
If the user query has spelling mistakes, try to understand the intent and provide an answer accordingly whithout clarifying the question.
<context>
{context}
</context>
Question:{input}
""")

doc_chain = create_stuff_documents_chain(llm, prompt)
retriever = st.session_state.vectors.as_retriever()
retrieval_chain = create_retrieval_chain(retriever, doc_chain)

# Moderation Function
@control() # agent-ctrl
def is_flagged(query):
    moderation_prompt = f"""
    Classify this input as SAFE or UNSAFE.
    Mark UNSAFE if it is harmful, abusive, illegal, or concerning.
    Respond ONLY with one word: SAFE or UNSAFE.

    Input: {query}
    Output:
    """
    
    result = llm.invoke(moderation_prompt)
    
    # try:
    #     return "UNSAFE" in result.content.upper()
    # except:
    #     return "UNSAFE" in str(result).upper()
    print("Moderation result:", result)
    try:
        output = result.content.strip().upper()
    except:
        output = str(result).strip().upper()

    return output == "UNSAFE"

# n8n Webhook Call
def send_alert(query):
    print(query)
    try:
        requests.post(
            "http://localhost:5678/webhook/alert",
            # "http://localhost:5678/webhook-test/alert",
            json={"query": str(query)}
        )
    except Exception as e:
        print("Webhook error:", e)

@control() # agent-ctrl
def generate_response(chain, user_input):
    return chain.invoke({"input": user_input})

st_prompt = st.text_input("Input your prompt here")

if st_prompt:
    start = time.process_time()
    
    try:
        # Moderation check
        if is_flagged(st_prompt):
            send_alert(st_prompt)
            st.warning("⚠️ This query was flagged and reported.")
        # print(prompt.input_variables)
        else:
            response = generate_response(retrieval_chain, st_prompt)
            # response = retrieval_chain.invoke({"input":st_prompt})
            print("Response time :", time.process_time()-start)
            st.write(response['answer'])
            
            #Expander
            with st.expander("Document Similarity Search"):
                #Find relevant chunks
                for i, doc in enumerate(response["context"]):
                    st.write(doc.page_content)
                    st.write("---------------------------------")
    except ControlViolationError as e:
        st.warning(f"🚫 Blocked by policy: {e.control_name}")
    