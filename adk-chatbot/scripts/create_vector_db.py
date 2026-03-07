"""
Create Vector Database from SDAIA PDF Chunks
Uses OpenAI embeddings and ChromaDB for storage
"""
import json
import chromadb
import openai
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def load_chunks(chunks_path: str) -> list[dict]:
    """Load chunks from JSON file"""
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    print(f"✅ Loaded {len(chunks)} chunks from {chunks_path}")
    return chunks


def create_embeddings(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    """
    Create embeddings using OpenAI API
    
    Args:
        texts: List of text strings to embed
        model: OpenAI embedding model to use
        
    Returns:
        List of embedding vectors
    """
    print(f"🔄 Creating embeddings for {len(texts)} texts...")
    
    response = openai.embeddings.create(
        input=texts,
        model=model
    )
    
    embeddings = [item.embedding for item in response.data]
    print(f"✅ Created {len(embeddings)} embeddings")
    return embeddings


def create_vector_db(chunks: list[dict], db_path: str = "data/chroma_db"):
    """
    Create ChromaDB vector database from chunks
    
    Args:
        chunks: List of chunk dicts with id, page, text
        db_path: Path to store the database
    """
    print(f"\n📦 Creating ChromaDB at {db_path}...")
    
    # Initialize ChromaDB persistent client at the given path.
    # We rely on Chroma's recommended PersistentClient API, and we always
    # recreate the database from scratch for this script.
    client = chromadb.PersistentClient(path=db_path)
    
    # Create or get collection
    collection_name = "sdaia_ai_principles"
    
    # Delete existing collection if it exists
    try:
        client.delete_collection(name=collection_name)
        print(f"🗑️ Deleted existing collection: {collection_name}")
    except:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "SDAIA AI Ethics Principles in Arabic"}
    )
    
    print(f"✅ Created collection: {collection_name}")
    
    # Prepare data for ChromaDB
    ids = [chunk["id"] for chunk in chunks]
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [{"page": chunk["page"], "word_count": chunk["word_count"]} for chunk in chunks]
    
    # Create embeddings
    embeddings = create_embeddings(texts)
    
    # Add to collection
    print(f"\n💾 Adding {len(chunks)} chunks to vector database...")
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )
    
    print(f"✅ Successfully added all chunks to database!")
    
    # Verify
    count = collection.count()
    print(f"📊 Total documents in collection: {count}")
    
    return collection


def test_search(collection, query: str, n_results: int = 3):
    """Test the vector database with a sample query"""
    print(f"\n🔍 Testing search with query: '{query}'")
    
    # Create query embedding
    query_embedding = create_embeddings([query])[0]
    
    # Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    print(f"\n📋 Top {n_results} results:")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
        print(f"\n{i}. Page {metadata['page']}:")
        print(f"   {doc[:200]}...")


if __name__ == "__main__":
    # Paths
    chunks_path = "data/sdaia_chunks.json"
    db_path = "data/chroma_db"
    
    # Load chunks
    chunks = load_chunks(chunks_path)
    
    # Create vector database
    collection = create_vector_db(chunks, db_path)
    
    # Test with a sample query
    test_search(collection, "ما هي مبادئ حماية البيانات الشخصية؟", n_results=3)
    
    print("\n✅ Vector database created successfully!")
    print(f"📁 Database location: {db_path}")