"""
RAG chatbot using Ollama and ChromaDB for FDA device Q&A
"""
import sys
import os
import requests
from typing import List, Dict

import streamlit as st
import chromadb
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

class RAGChatbot:
    def __init__(self, chroma_path: str, ollama_url: str, model: str, embedding_model: str):
        self.ollama_url = ollama_url
        self.model = model
        self.embedding_model = embedding_model

        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        try:
            self.collection = self.chroma_client.get_collection("fda_devices")
        except:
            self.collection = None

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama"""
        url = f"{self.ollama_url}/api/embed"
        payload = {
            "model": self.embedding_model,
            "input": text
        }

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        if 'embeddings' in result:
            return result['embeddings'][0]
        elif 'embedding' in result:
            return result['embedding']
        else:
            raise ValueError(f"Unexpected response: {result.keys()}")

    def retrieve_context(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant context from vector DB"""
        if self.collection is None:
            return []

        # Get query embedding
        query_embedding = self.get_embedding(query)

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Format results
        contexts = []
        if results['documents'] and len(results['documents']) > 0:
            for i in range(len(results['documents'][0])):
                contexts.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })

        return contexts

    def generate_response(self, query: str, contexts: List[Dict]) -> str:
        """Generate response using Ollama LLM"""
        # Build context string
        context_str = "\n\n".join([
            f"[Device: {ctx['metadata'].get('device_name', 'N/A')} | Company: {ctx['metadata'].get('company', 'N/A')}]\n{ctx['text']}"
            for ctx in contexts
        ])

        # Build prompt
        prompt = f"""You are an expert assistant for FDA AI/ML medical device information.

Context from FDA device approval documents:
{context_str}

User question: {query}

Please provide a detailed answer based on the context above. If the context doesn't contain relevant information, say so clearly.

Answer:"""

        # Call Ollama API
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        return result.get('response', 'No response generated')

    def chat(self, query: str, top_k: int = 5) -> tuple[str, List[Dict]]:
        """Main chat function"""
        contexts = self.retrieve_context(query, top_k)
        response = self.generate_response(query, contexts)
        return response, contexts

def main():
    st.set_page_config(
        page_title="FDA AI/ML Device Chatbot",
        page_icon="🤖",
        layout="wide"
    )

    st.title("FDA AI/ML Device Chatbot")
    st.markdown("Ask questions about FDA-approved AI/ML medical devices")

    # Initialize chatbot
    chroma_path = os.getenv('CHROMA_PERSIST_DIR', './data/chroma')
    ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    model = os.getenv('OLLAMA_MODEL', 'gpt-oss:latest')
    embedding_model = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text:latest')

    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = RAGChatbot(chroma_path, ollama_url, model, embedding_model)

    if 'messages' not in st.session_state:
        st.session_state.messages = []

    chatbot = st.session_state.chatbot

    # Check if vector DB exists
    if chatbot.collection is None:
        st.error("Vector database not found. Please run embedding first: `python src/embed.py`")
        return

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about FDA AI/ML medical devices..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching and generating response..."):
                try:
                    response, contexts = chatbot.chat(prompt, top_k=5)

                    st.markdown(response)

                    # Show sources
                    with st.expander("View Sources"):
                        for i, ctx in enumerate(contexts):
                            st.markdown(f"**Source {i+1}:** {ctx['metadata'].get('device_name', 'N/A')} - {ctx['metadata'].get('company', 'N/A')}")
                            st.text(ctx['text'][:300] + "...")
                            st.markdown("---")

                    st.session_state.messages.append({"role": "assistant", "content": response})

                except Exception as e:
                    st.error(f"Error: {e}")

    # Sidebar
    st.sidebar.header("Settings")
    st.sidebar.info(f"Model: {model}")
    st.sidebar.info(f"Embedding: {embedding_model}")

    if st.sidebar.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()
