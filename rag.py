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
import numpy as np
import faiss
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- STEP 1: CHUNKING ---
# Why chunk? Because LLMs work better with small, focused pieces of text
# Instead of sending a 2000-word drug label, we send the 3 most relevant paragraphs

def chunk_text(text, chunk_size=300):
    """
    Split text into smaller pieces.
    
    Think of it like this:
    - A full drug label = an entire textbook chapter
    - A chunk = one paragraph from that chapter
    - We only want to send the relevant paragraphs to the LLM
    
    chunk_size=300 means roughly 300 characters per chunk
    """
    if not text or text == "Not available":
        return []
    
    # Split by sentences (roughly)
    sentences = text.replace(". ", ".\n").split("\n")
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If adding this sentence would make the chunk too big, save current and start new
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence
    
    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def build_chunks_from_databases():
    """
    Read both databases and create chunks with metadata.
    
    Each chunk looks like:
    {
        "text": "Amoxicillin is used for bacterial infections...",
        "drug_name": "Amoxicillin",
        "section": "indications",
        "source": "openFDA"
    }
    
    The metadata tells us WHERE this chunk came from,
    so we can show source attribution in the frontend.
    """
    all_chunks = []
    
    # Process openFDA database
    try:
        with open("drug_data.json", "r", encoding="utf-8") as f:
            openfda_drugs = json.load(f)
        
        for drug in openfda_drugs:
            name = drug["name"]
            
            # Each section becomes its own set of chunks
            sections = {
                "indications": drug.get("indications", ""),
                "dosage": drug.get("dosage", ""),
                "warnings": drug.get("warnings", ""),
                "adverse_reactions": drug.get("adverse_reactions", ""),
                "contraindications": drug.get("contraindications", ""),
                "drug_interactions": drug.get("drug_interactions", ""),
            }
            
            for section_name, section_text in sections.items():
                if section_text and section_text != "Not available":
                    chunks = chunk_text(section_text)
                    for chunk in chunks:
                        all_chunks.append({
                            "text": chunk,
                            "drug_name": name,
                            "section": section_name,
                            "source": "openFDA Drug Labels"
                        })
        
        print(f"  openFDA: {len([c for c in all_chunks if c['source'] == 'openFDA Drug Labels'])} chunks from {len(openfda_drugs)} drugs")
    
    except FileNotFoundError:
        print("  drug_data.json not found, skipping openFDA")
    
    # Process Kaggle database
    try:
        with open("medicines_db.json", "r", encoding="utf-8") as f:
            kaggle_medicines = json.load(f)
        
        kaggle_count = 0
        for med in kaggle_medicines:
            name = med["name"]
            
            # Kaggle data has different fields
            sections = {
                "uses": med.get("uses", ""),
                "side_effects": med.get("side_effects", ""),
                "composition": med.get("composition", ""),
            }
            
            for section_name, section_text in sections.items():
                if section_text and section_text.strip():
                    chunks = chunk_text(section_text)
                    for chunk in chunks:
                        all_chunks.append({
                            "text": chunk,
                            "drug_name": name,
                            "section": section_name,
                            "source": "Kaggle Medicine Database"
                        })
                        kaggle_count += 1
        
        print(f"  Kaggle: {kaggle_count} chunks from {len(kaggle_medicines)} medicines")
    
    except FileNotFoundError:
        print("  medicines_db.json not found, skipping Kaggle")
    
    print(f"  Total: {len(all_chunks)} chunks")
    return all_chunks


# --- STEP 2: EMBEDDINGS ---
# An embedding converts text into a list of numbers (a vector)
# Similar texts get similar numbers
# "headache medicine" and "pain relief tablet" would have similar vectors
# "headache medicine" and "car engine oil" would have very different vectors

def get_embedding(text):
    """
    Convert a piece of text into a vector using Gemini's embedding model.
    
    Input:  "Amoxicillin treats bacterial infections"
    Output: [0.023, -0.156, 0.892, ...] (768 numbers)
    
    These numbers capture the MEANING of the text.
    """
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return response.embeddings[0].values


def get_embeddings_batch(texts, batch_size=50):
    """
    Convert many texts to vectors in batches.
    We batch them because sending 10,000 one at a time would be very slow.
    """
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"    Embedding batch {i // batch_size + 1}/{(len(texts) // batch_size) + 1}...")
        
        for text in batch:
            try:
                emb = get_embedding(text)
                all_embeddings.append(emb)
            except Exception as e:
                # If one fails, use zeros (won't match anything, but won't crash)
                print(f"    Warning: embedding failed for text: {text[:50]}... Error: {e}")
                all_embeddings.append([0.0] * 768)
        
        # Small delay to respect rate limits
        import time
        time.sleep(1)
    
    return all_embeddings


# --- STEP 3: FAISS INDEX ---
# FAISS is like a super-fast phonebook for vectors
# Instead of looking up by name, it looks up by similarity
# "Find me the 5 vectors most similar to this query vector"

def build_faiss_index(chunks):
    """
    Build a FAISS index from our chunks.
    
    This is a one-time operation. We:
    1. Get embeddings for all chunks
    2. Store them in FAISS
    3. Save to disk so we don't have to rebuild every time
    """
    print("\nStep 1: Getting embeddings for all chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = get_embeddings_batch(texts)
    
    # Convert to numpy array (FAISS needs this format)
    # numpy is like Java's array but for math/science
    embeddings_array = np.array(embeddings).astype("float32")
    
    print(f"\nStep 2: Building FAISS index...")
    print(f"  Vector dimension: {embeddings_array.shape[1]}")
    print(f"  Number of vectors: {embeddings_array.shape[0]}")
    
    # Create the FAISS index
    # IndexFlatL2 = simplest index, uses L2 (Euclidean) distance
    # Good enough for our dataset size
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)
    
    print(f"  Index built with {index.ntotal} vectors")
    
    # Save everything to disk
    print(f"\nStep 3: Saving to disk...")
    faiss.write_index(index, "faiss_index.bin")
    
    with open("chunks_metadata.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    
    print(f"  Saved faiss_index.bin and chunks_metadata.json")
    
    return index, chunks


# --- STEP 4: RETRIEVAL ---
# This is the R in RAG - finding the most relevant chunks for a query

def load_index():
    """Load the pre-built FAISS index and chunk metadata"""
    index = faiss.read_index("faiss_index.bin")
    with open("chunks_metadata.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return index, chunks


def retrieve(query, index, chunks, top_k=5):
    """
    Find the top_k most relevant chunks for a query.
    
    Example:
        query = "What is amoxicillin used for?"
        Returns the 5 chunks most related to amoxicillin's uses
    
    This is like Google search but for your medical database:
    - Google converts your search to a vector
    - Finds web pages with similar vectors
    - Returns the most relevant ones
    
    We do the same but with medical text chunks.
    """
    # Convert query to vector
    query_embedding = get_embedding(query)
    query_vector = np.array([query_embedding]).astype("float32")
    
    # Search FAISS for similar vectors
    # distances = how far away each result is (lower = more similar)
    # indices = which chunks matched
    distances, indices = index.search(query_vector, top_k)
    
    # Collect results with metadata
    results = []
    for i, idx in enumerate(indices[0]):
        if idx < len(chunks):  # Safety check
            result = chunks[idx].copy()
            result["relevance_score"] = float(distances[0][i])
            results.append(result)
    
    return results


# --- MAIN: Build the index ---
if __name__ == "__main__":
    print("=" * 60)
    print("  MediSimply RAG - Building Vector Store")
    print("=" * 60)
    
    print("\nStep 0: Creating chunks from databases...")
    chunks = build_chunks_from_databases()
    
    if not chunks:
        print("No chunks found! Make sure drug_data.json and medicines_db.json exist.")
        exit(1)
    
    # Build the index (this takes a few minutes due to embedding API calls)
    index, chunks = build_faiss_index(chunks)
    
    # Test it with a sample query
    print("\n" + "=" * 60)
    print("  Testing retrieval...")
    print("=" * 60)
    
    test_queries = [
        "What is amoxicillin used for?",
        "side effects of metformin",
        "blood pressure medicine warnings",
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = retrieve(query, index, chunks, top_k=3)
        for j, r in enumerate(results, 1):
            print(f"  {j}. [{r['source']}] {r['drug_name']} ({r['section']})")
            print(f"     {r['text'][:100]}...")
    
    print(f"\nRAG system ready! Index has {index.ntotal} vectors.")
# ```

# I've commented every section heavily so you understand what each part does. Before running it, install numpy too:
# ```
# pip install numpy
# ```

# Then run it:
# ```
# python3 rag.py