import os
from dotenv import load_dotenv

# LangChain Imports
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import (
    DirectoryLoader, 
    TextLoader, 
    PyPDFLoader, 
    Docx2txtLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

class MultiSourceBankingAgent:
    def __init__(self, data_path="data/"):
        self.llm = ChatOpenAI(model=os.getenv("MODEL_NAME", "gpt-4o"), temperature=0)
        self.data_path = data_path
        
        # 1. Setup Document Loaders for multiple file types
        # This mapping tells LangChain which loader to use for which extension
        loaders = {
            ".txt": TextLoader,
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
        }

        def create_loader(file_path):
            ext = os.path.splitext(file_path)[1]
            if ext in loaders:
                return loaders[ext](file_path)
            return None

        # Load all documents from the directory
        print(f"Loading documents from {data_path}...")
        docs = []
        for file in os.listdir(data_path):
            file_path = os.path.join(data_path, file)
            loader = create_loader(file_path)
            if loader:
                docs.extend(loader.load())

        # 2. Text Chunking (Mandatory Phase 4 Task)
        # Breaking long documents into smaller pieces for better retrieval
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        splits = text_splitter.split_documents(docs)

        # 3. Embeddings & Vector Store
        self.vectorstore = Chroma.from_documents(
            documents=splits, 
            embedding=OpenAIEmbeddings(),
            collection_name="banking_knowledge"
        )
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})

        # 4. RAG Prompt with Phase 3 Safety Rules
        template = """
        You are the Sentinel FinAI Advisory Agent. Use the context below to answer accurately.
        
        Context: {context}
        
        Safety Rules:
        1. Answer ONLY using the provided context. If unsure, say "I don't have that information in my current records."
        2. Strictly NON-TRANSACTIONAL. Refuse money movement.
        3. No legal/tax advice.
        
        Question: {question}
        """
        self.prompt = ChatPromptTemplate.from_template(template)

    def ask(self, query):
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        return rag_chain.invoke(query)

if __name__ == "__main__":
    # Ensure the 'data' directory exists and has files before running
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Created /data directory. Please add your .txt, .pdf, or .docx files there.")
    else:
        agent = MultiSourceBankingAgent()
        
        print("\n--- Phase 4: Multi-Format RAG Agent ---")
        # Test query that might span across your different documents
        query = "1. What are the requirements for a home loan and the interest rates? (query asked from txt file)"
        print(f"Q: {query}\nA: {agent.ask(query)}\n")

        # From txt file
        query = "2. What is the APY for the Elite Savings account? (query asked from txt file)"
        print(f"Q: {query}\nA: {agent.ask(query)}\n")

        # From docx file
        query = "3. What documents do I need for a 30-year mortgage? (query asked from docx file)"
        print(f"Q: {query}\nA: {agent.ask(query)}\n")

        # From PDF file
        query = "4. Can you increase my ATM limit to $5,000? (query asked from PDF file)"
        print(f"Q: {query}\nA: {agent.ask(query)}\n")