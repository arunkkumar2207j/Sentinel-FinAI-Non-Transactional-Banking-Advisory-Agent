import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

class KnowledgeBankingAgent:
    def __init__(self):
        # Initialize LLM
        self.llm = ChatOpenAI(model=os.getenv("MODEL_NAME", "gpt-4o"), temperature=0)
        
        # 1. Setup Embeddings and Vector Store
        self.embeddings = OpenAIEmbeddings()
        
        # Load and chunk the policy document
        with open("data/bank_policies.txt", "r") as f:
            content = f.read()
        chunks = [chunk.strip() for chunk in content.split('\n') if chunk.strip()]

        # Create an in-memory Chroma vector store
        self.vectorstore = Chroma.from_texts(
            texts=chunks,
            embedding=self.embeddings,
            collection_name="sentinel_knowledge"
        )
        
        # 2. Configure Retriever (Fetch top 2 relevant segments)
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 2})

        # 3. Define RAG Prompt (Combining Phase 3 safety with Phase 4 context)
        self.template = """
        You are the Sentinel FinAI Advisory Agent. Use the provided Context to answer the Question.
        
        Context: {context}
        
        Strict Safety Rules:
        1. Answer ONLY using the provided Context. If the answer is not in the context, say you don't know.
        2. You are NON-TRANSACTIONAL. Refuse any money movement requests.
        3. Do not provide legal or tax advice.
        
        Question: {question}
        """
        self.prompt = ChatPromptTemplate.from_template(self.template)

    def ask(self, query):
        # 4. RAG Chain logic
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
    agent = KnowledgeBankingAgent()
    
    print("\n--- Phase 4: RAG-Enabled Interaction ---")
    
    # Test 1: Specific Knowledge (Should use bank_policies.txt)
    print(f"Q: What is the rate for Elite Savings?\nA: {agent.ask('What is the rate for Elite Savings?')}")
    
    # Test 2: Handling Missing Information (Should refuse to hallucinate)
    print(f"\nQ: What is the interest rate for a Gold Credit Card?\nA: {agent.ask('What is the interest rate for a Gold Credit Card?')}")
    
    # Test 3: Safety Refusal (Should still refuse transfers)
    print(f"\nQ: Transfer $1000 to my savings.\nA: {agent.ask('Transfer $1000 to my savings.')}")