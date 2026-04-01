"""
RAG (Retrieval-Augmented Generation) for MediSimply
====================================================
This module does 3 things:
1. Chunks medical texts into small pieces
2. Converts them to vectors (embeddings) using Gemini
3. Stores them in FAISS for fast similarity search
"""

import json
import os
import time
import numpy as np
import faiss
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# --- STEP 1: CHUNKING ---
def chunk_text(text, chunk_size=300):
    """
    Split text into smaller pieces.
    
    Why? LLMs work better with small, focused text.
    A full drug label = a textbook chapter
    A chunk = one paragraph
    We only send the RELEVANT paragraphs to the LLM
    """
    if not text or text == "Not available":
        return []
    
    sentences = text.replace(". ", ".\n").split("\n")
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def build_chunks():
    """
    Create chunks from openFDA database only.
    
    Why not Kaggle? openFDA has detailed medical text (dosage, warnings, 
    contraindications). Kaggle data is short and already searchable by name.
    RAG is for finding RELEVANT PASSAGES, not name matching.
    """
    all_chunks = []
    
    with open("drug_data.json", "r", encoding="utf-8") as f:
        drugs = json.load(f)
    
    for drug in drugs:
        name = drug["name"]
        sections = {
            "indications": drug.get("indications", ""),
            "dosage": drug.get("dosage", ""),
            "warnings": drug.get("warnings", ""),
            "adverse_reactions": drug.get("adverse_reactions", ""),
            "contraindications": drug.get("contraindications", ""),
            "drug_interactions": drug.get("drug_interactions", ""),
        }
        
        for section_name, text in sections.items():
            if text and text != "Not available":
                for chunk in chunk_text(text):
                    all_chunks.append({
                        "text": chunk,
                        "drug_name": name,
                        "section": section_name,
                        "source": "openFDA Drug Labels"
                    })
    
    print(f"Created {len(all_chunks)} chunks from {len(drugs)} drugs")
    return all_chunks


# --- STEP 2: EMBEDDINGS ---
def get_embedding(text):
    """
    Convert text into a vector (list of numbers).
    
    "Amoxicillin treats infections" → [0.023, -0.156, 0.892, ...]
    
    Similar meanings get similar numbers.
    "headache medicine" and "pain relief" → similar vectors
    "headache medicine" and "car engine" → very different vectors
    """
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return response.embeddings[0].values


# --- STEP 3: BUILD FAISS INDEX ---
def build_index(chunks):
    """
    Build the FAISS index. This is a one-time operation.
    
    FAISS = a super-fast phonebook for vectors
    Instead of looking up by name, it finds by SIMILARITY
    """
    print(f"\nEmbedding {len(chunks)} chunks (this takes a few minutes)...\n")
    
    embeddings = []
    for i, chunk in enumerate(chunks):
        print(f"  [{i+1}/{len(chunks)}] {chunk['drug_name']} - {chunk['section'][:20]}...", end=" ")
        try:
            emb = get_embedding(chunk["text"])
            embeddings.append(emb)
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")
            embeddings.append([0.0] * 768)
            time.sleep(10)  # Wait longer after errors
        
        # Rate limit: ~1 request per second
        time.sleep(1)
    
    # Convert to numpy array
    embeddings_array = np.array(embeddings).astype("float32")
    
    # Create FAISS index
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)
    
    # Save to disk
    faiss.write_index(index, "faiss_index.bin")
    with open("chunks_metadata.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    
    print(f"\nDone! Saved {index.ntotal} vectors to faiss_index.bin")
    return index


# --- STEP 4: RETRIEVAL (the R in RAG) ---
def load_index():
    """Load pre-built index from disk"""
    index = faiss.read_index("faiss_index.bin")
    with open("chunks_metadata.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return index, chunks


def retrieve(query, top_k=5):
    """
    Find the most relevant chunks for a query.
    
    Like Google search but for YOUR medical database:
    1. Convert query to vector
    2. FAISS finds the closest vectors
    3. Return those chunks with metadata
    
    Example:
        query = "amoxicillin side effects"
        Returns → 5 most relevant passages about amoxicillin side effects
    """
    index, chunks = load_index()
    
    # Convert query to vector
    query_vector = np.array([get_embedding(query)]).astype("float32")
    
    # Search FAISS
    distances, indices = index.search(query_vector, top_k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(chunks):
            result = chunks[idx].copy()
            result["relevance_score"] = float(distances[0][i])
            results.append(result)
    
    return results


# --- RUN: Build the index ---
if __name__ == "__main__":
    print("=" * 60)
    print("  MediSimply RAG - Building Vector Store")
    print("=" * 60)
    
    chunks = build_chunks()
    
    if not chunks:
        print("No chunks found! Make sure drug_data.json exists.")
        exit(1)
    
    build_index(chunks)
    
    # Test retrieval
    print("\n" + "=" * 60)
    print("  Testing retrieval...")
    print("=" * 60)
    
    test_queries = [
        "What is amoxicillin used for?",
        "side effects of metformin",
        "blood pressure medicine dosage",
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = retrieve(query, top_k=3)
        for j, r in enumerate(results, 1):
            print(f"  {j}. [{r['drug_name']}] ({r['section']})")
            print(f"     {r['text'][:100]}...")
    
    print(f"\nRAG system ready!")
