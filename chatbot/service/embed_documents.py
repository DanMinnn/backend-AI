import os
import re
import sys
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from langchain_text_splitters import CharacterTextSplitter

pdf_data_path = "../data"
vector_db_path = "../vectorstores/db_faiss"
load_dotenv()

def clean_line_breaks(text: str) -> str:
    """
    Ghép các dòng bị ngắt dòng không cần thiết trong cùng đoạn.
    """
    return re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    
def create_db_from_files():
    #
    loader = DirectoryLoader(pdf_data_path, glob="*.pdf", loader_cls = PyPDFLoader)
    documents = loader.load()

    for doc in documents:
        doc.page_content = clean_line_breaks(doc.page_content)

    # Split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=50
    )
    chunks = text_splitter.split_documents(documents)
    print(f"🔹 Total chunks created: {len(chunks)}")
    # Embedding
    embedding_model = HuggingFaceEmbeddings(
        model_name="keepitreal/vietnamese-sbert",
        model_kwargs={"device": "cpu"},  
        encode_kwargs={"normalize_embeddings": True} 
    )

    # Save to Faiss vector DB
    db = FAISS.from_documents(documents=chunks, embedding=embedding_model)
    db.save_local(vector_db_path)
    

    # Test a query to verify
    test_query = "Dịch vụ nấu ăn"
    docs = db.similarity_search(test_query, k=5)
    for i, doc in enumerate(docs):
        print(f"\n>> Kết quả {i+1}:")
        print(doc.page_content[:300])

    return db

create_db_from_files()