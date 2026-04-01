import json
import os
import numpy as np
import faiss
from dotenv import load_dotenv
from google import genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
"""
Sinhala Medical Glossary for MediSimply
========================================
This glossary ensures consistent, accurate Sinhala translations
of medical terms. Terms are mapped to colloquial (spoken) Sinhala
that elderly patients would understand.

This is a key contribution of the FYP - no such glossary exists
for Sinhala medical text simplification.
"""

# Format: "English term": "Sinhala translation (spoken/colloquial)"
MEDICAL_GLOSSARY = {
    # --- Body Parts ---
    "heart": "හදවත",
    "liver": "අක්මාව",
    "kidney": "වකුගඩුව",
    "lungs": "පෙනහළු",
    "stomach": "බඩ / ආමාශය",
    "brain": "මොළය",
    "blood": "ලේ / රුධිරය",
    "blood vessels": "ලේ නාල",
    "skin": "සම",
    "bones": "ඇට",
    "joints": "සන්ධි",
    "muscles": "මාංශ පේශි",
    "eyes": "ඇස්",
    "ears": "කන්",
    "throat": "උගුර",
    "chest": "छාතිය",
    "intestines": "බඩවැල්",
    "bladder": "මුත්‍රාශය",
    "uterus": "ගර්භාෂය",
    "nerves": "ස්නායු",

    # --- Common Conditions ---
    "high blood pressure": "අධි රුධිර පීඩනය (බ්ලඩ් ප්‍රෙෂර් එක වැඩි වීම)",
    "low blood pressure": "අඩු රුධිර පීඩනය (බ්ලඩ් ප්‍රෙෂර් එක අඩු වීම)",
    "diabetes": "දියවැඩියාව (සීනි රෝගය)",
    "type 2 diabetes": "ටයිප් 2 දියවැඩියාව",
    "cholesterol": "කොලෙස්ටරෝල්",
    "high cholesterol": "කොලෙස්ටරෝල් වැඩි වීම",
    "infection": "ආසාදනය (ඉන්ෆෙක්ෂන් එකක්)",
    "bacterial infection": "බැක්ටීරියා ආසාදනය",
    "viral infection": "වයිරස් ආසාදනය",
    "inflammation": "ඉදිමීම / දැවිල්ල",
    "fever": "උණ",
    "pain": "වේදනාව / අමාරුව",
    "headache": "හිසරදය",
    "stomach ache": "බඩේ අමාරුව",
    "chest pain": "छාතියේ අමාරුව",
    "joint pain": "සන්ධි වේදනාව",
    "back pain": "පිට අමාරුව",
    "swelling": "ඉදිමීම",
    "allergy": "අසාත්මිකතාවය (ඇලර්ජි)",
    "allergic reaction": "ඇලර්ජි ප්‍රතික්‍රියාව",
    "asthma": "ඇදුම",
    "stroke": "ආඝාතය (ස්ට්‍රෝක්)",
    "heart attack": "හෘදයාබාධය (හාට් ඇටෑක්)",
    "cancer": "පිළිකාව",
    "ulcer": "තුවාලය / ඇල්සරය",
    "diarrhea": "පාචනය (බඩ පිරීම)",
    "constipation": "මලබද්ධය",
    "nausea": "ඔක්කාරය (වමනය එන ගතිය)",
    "vomiting": "වමනය",
    "dizziness": "කරකැවිල්ල / හිස කැරකීම",
    "fatigue": "තෙහෙට්ටුව / මහන්සිය",
    "cough": "කැස්ස",
    "cold": "සෙම්ප්‍රතිශ්‍යාව (සීතල)",
    "rash": "සම් කුෂ්ඨ / කැසීම",
    "itching": "කැසීම",
    "bleeding": "ලේ ගැලීම",
    "anxiety": "කාංසාව / බය",
    "depression": "මානසික අවපීඩනය",
    "insomnia": "නින්ද නොයාම",
    "gout": "වාතරක්තය (ගවුට්)",
    "arthritis": "ආතරයිටිස් (සන්ධි දැවිල්ල)",
    "thyroid": "තයිරොයිඩ්",
    "anemia": "රක්තහීනතාවය (ලේ මදිකම)",

    # --- Medicine Types ---
    "antibiotic": "ප්‍රතිජීවක බෙහෙත (ඇන්ටිබයොටික්)",
    "painkiller": "වේදනා නාශක බෙහෙත",
    "pain reliever": "වේදනා නාශක බෙහෙත",
    "blood thinner": "ලේ තුනී කරන බෙහෙත",
    "antacid": "ආම්ලිකතා නාශක (ගෑස් බෙහෙත)",
    "anti-inflammatory": "දැවිල්ල අඩු කරන බෙහෙත",
    "steroid": "ස්ටෙරොයිඩ් බෙහෙත",
    "supplement": "අතිරේක පෝෂක (සප්ලිමන්ට්)",
    "vitamin": "විටමින්",
    "tablet": "පෙත්ත",
    "capsule": "කැප්සියුලය",
    "syrup": "සිරප්",
    "injection": "එන්නත",
    "cream": "ක්‍රීම්",
    "drops": "බිංදු",
    "inhaler": "ඉන්හේලර්",

    # --- Dosage Instructions ---
    "once a day": "දිනකට එක් වරක්",
    "twice a day": "දිනකට දෙවරක්",
    "three times a day": "දිනකට තුන් වරක්",
    "before meals": "ආහාරයට පෙර",
    "after meals": "ආහාරයෙන් පසුව",
    "with food": "ආහාර සමඟ",
    "on an empty stomach": "හිස් බඩට",
    "at bedtime": "නිදාගැනීමට පෙර",
    "in the morning": "උදේ",
    "in the evening": "සවස",
    "as needed": "අවශ්‍ය විටදී",
    "every 4 hours": "පැය 4 කට වරක්",
    "every 6 hours": "පැය 6 කට වරක්",
    "every 8 hours": "පැය 8 කට වරක්",
    "every 12 hours": "පැය 12 කට වරක්",

    # --- Warnings ---
    "do not take": "ගන්න එපා",
    "stop taking": "ගැනීම නවත්වන්න",
    "consult your doctor": "ඔබේ වෛද්‍යවරයාගෙන් අහන්න",
    "talk to your doctor": "ඔබේ වෛද්‍යවරයාට කියන්න",
    "call your doctor": "ඔබේ වෛද්‍යවරයාට කතා කරන්න",
    "go to hospital": "රෝහලට යන්න",
    "side effects": "අතුරු ආබාධ",
    "overdose": "අධික මාත්‍රාව (වැඩිපුර ගැනීම)",
    "do not crush": "කඩන්න / කුඩු කරන්න එපා",
    "do not chew": "සපන්න එපා",
    "swallow whole": "හපමින් ගිලින්න",
    "keep out of reach of children": "ළමුන්ට අත නොනිල තැනක තබන්න",
    "store in cool place": "සිසිල් තැනක තබන්න",
    "do not drive": "රිය පදවන්න එපා",
    "avoid alcohol": "මත්පැන් වලින් වළකින්න",
    "pregnant": "ගර්භණී (ලේඩුව)",
    "breastfeeding": "කිරි දෙන (මව)",
    "elderly": "වැඩිහිටි / මහලු",
    "children": "ළමුන් / ළමයි",

    # --- Common Actions ---
    "take": "ගන්න",
    "swallow": "ගිලින්න",
    "apply": "ආලේප කරන්න",
    "inject": "එන්නත් කරන්න",
    "inhale": "ආශ්වාස කරන්න",
    "dissolve": "දිය කරන්න",
    "mix": "මිශ්‍ර කරන්න",
}


def get_glossary_prompt():
    """
    Generate a glossary section for the LLM prompt.
    This ensures consistent Sinhala translations across all outputs.
    """
    glossary_text = "SINHALA MEDICAL GLOSSARY - You MUST use these exact translations:\n\n"

    for english, sinhala in MEDICAL_GLOSSARY.items():
        glossary_text += f'  "{english}" → "{sinhala}"\n'

    glossary_text += """
IMPORTANT GLOSSARY RULES:
1. ALWAYS use the Sinhala terms from this glossary when translating
2. NEVER translate drug names - keep them in English (e.g., Amoxicillin stays as Amoxicillin)
3. NEVER translate dosage numbers - keep them as-is (e.g., 500mg stays as 500mg)
4. Use colloquial/spoken Sinhala, not formal literary Sinhala
5. When a term has both formal and colloquial forms shown (e.g., "වේදනාව / අමාරුව"), prefer the colloquial form (අමාරුව)
6. Add English terms in brackets for medical concepts elderly patients might know by English name (e.g., "ඇලර්ජි" for allergy)
"""
    return glossary_text


# Quick stats
if __name__ == "__main__":
    print(f"MediSimply Sinhala Medical Glossary")
    print(f"Total terms: {len(MEDICAL_GLOSSARY)}")

    categories = {
        "Body Parts": [k for k in MEDICAL_GLOSSARY if k in ["heart", "liver", "kidney", "lungs", "stomach", "brain", "blood", "skin", "bones", "joints", "muscles", "eyes", "ears", "throat", "chest"]],
        "Conditions": [k for k in MEDICAL_GLOSSARY if "pain" in k or "infection" in k or k in ["diabetes", "fever", "allergy", "asthma", "stroke", "cancer", "diarrhea", "nausea", "cough"]],
        "Medicine Types": [k for k in MEDICAL_GLOSSARY if k in ["antibiotic", "painkiller", "tablet", "capsule", "syrup", "injection", "cream", "drops", "inhaler"]],
    }

    for cat, terms in categories.items():
        print(f"\n  {cat}: {len(terms)} terms")
        for t in terms[:5]:
            print(f"    {t} → {MEDICAL_GLOSSARY[t]}")

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"

app = FastAPI(title="MediSimply API", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---
class MedicineQuery(BaseModel):
    medicine_name: str


class SectionOutput(BaseModel):
    english: str
    sinhala: str


class SourceInfo(BaseModel):
    text: str
    drug_name: str
    section: str
    source: str


class MedicineResponse(BaseModel):
    medicine_name: str
    found_in_database: bool
    source: str
    image_url: str = ""
    composition: str = ""
    manufacturer: str = ""
    what_it_does: SectionOutput
    how_to_take: SectionOutput
    warnings_and_side_effects: SectionOutput
    who_should_not_take: SectionOutput
    key_points: list[str]
    rag_sources: list[SourceInfo] = []  # NEW: show where info came from


class SearchResult(BaseModel):
    name: str
    composition: str
    image_url: str
    manufacturer: str


# --- Load databases ---
def load_kaggle_db():
    try:
        with open("medicines_db.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def load_openfda_db():
    try:
        with open("drug_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def search_medicine(name):
    """Search both databases for a medicine"""
    name_lower = name.lower().strip()
    kaggle_match = None
    openfda_match = None

    for med in load_kaggle_db():
        if name_lower in med["name"].lower() or med["name"].lower() in name_lower:
            kaggle_match = med
            break
    if not kaggle_match:
        for med in load_kaggle_db():
            if name_lower in med.get("composition", "").lower():
                kaggle_match = med
                break

    for drug in load_openfda_db():
        if drug["name"].lower() == name_lower or name_lower in drug["name"].lower():
            openfda_match = drug
            break

    return kaggle_match, openfda_match


# --- RAG: Retrieval ---
# Load FAISS index once when server starts (not on every request)
rag_index = None
rag_chunks = None

def load_rag():
    """Load the FAISS index and chunks into memory"""
    global rag_index, rag_chunks
    try:
        rag_index = faiss.read_index("faiss_index.bin")
        with open("chunks_metadata.json", "r", encoding="utf-8") as f:
            rag_chunks = json.load(f)
        print(f"RAG loaded: {rag_index.ntotal} vectors")
    except FileNotFoundError:
        print("WARNING: RAG index not found. Run rag.py first to build it.")
        rag_index = None
        rag_chunks = None


def get_embedding(text):
    """Convert text to vector using Gemini embedding model"""
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return response.embeddings[0].values


def retrieve_relevant_chunks(query, top_k=5):
    """
    THE KEY RAG FUNCTION
    
    This is what makes RAG different from just sending everything to the LLM:
    1. Convert the user's query into a vector
    2. Find the most similar chunks in our FAISS index
    3. Return only the relevant passages
    
    Without RAG: "Here's ALL the data about ALL drugs, please simplify"
    With RAG:    "Here are the 5 most relevant passages about THIS drug, please simplify"
    """
    if rag_index is None or rag_chunks is None:
        return []
    
    try:
        query_vector = np.array([get_embedding(query)]).astype("float32")
        distances, indices = rag_index.search(query_vector, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(rag_chunks):
                chunk = rag_chunks[idx].copy()
                chunk["relevance_score"] = float(distances[0][i])
                results.append(chunk)
        
        return results
    except Exception as e:
        print(f"RAG retrieval error: {e}")
        return []


# --- LLM with RAG ---
def simplify_medicine(medicine_name, kaggle_data=None, openfda_data=None, rag_results=None):
    """
    THE KEY DIFFERENCE WITH RAG:
    
    Before RAG:
        Prompt = "Simplify this medicine info" + database dump
        Problem: LLM might hallucinate, no source attribution
    
    After RAG:
        Prompt = "Using ONLY these retrieved passages" + relevant chunks
        Result: Grounded in real sources, traceable, less hallucination
    """
    
    context_parts = []

    # RAG context - the most important part
    if rag_results:
        rag_context = "\n\n".join([
            f"[Source: {r['source']} | Drug: {r['drug_name']} | Section: {r['section']}]\n{r['text']}"
            for r in rag_results
        ])
        context_parts.append(f"""
RETRIEVED PASSAGES FROM VERIFIED MEDICAL DATABASE:
{rag_context}
""")

    # Kaggle data for additional context
    if kaggle_data:
        context_parts.append(f"""
Additional info from Medicine Database:
- Name: {kaggle_data['name']}
- Composition: {kaggle_data.get('composition', 'N/A')}
- Uses: {kaggle_data.get('uses', 'N/A')}
- Side Effects: {kaggle_data.get('side_effects', 'N/A')}
""")

    # openFDA data if available
    if openfda_data:
        context_parts.append(f"""
From openFDA Verified Labels:
- Indications: {openfda_data.get('indications', 'N/A')}
- Dosage: {openfda_data.get('dosage', 'N/A')}
- Warnings: {openfda_data.get('warnings', 'N/A')}
- Contraindications: {openfda_data.get('contraindications', 'N/A')}
""")

    if context_parts:
        context = "\n".join(context_parts)
        source_instruction = """CRITICAL INSTRUCTION: You MUST use ONLY the retrieved passages and provided data above.
Do NOT add any information that is not in the sources.
If a section has no relevant data, say "Ask your doctor or pharmacist about this."
For each fact you state, it must come from the provided passages."""
    else:
        context = f"The user is asking about: {medicine_name}"
        source_instruction = """This medicine was NOT found in our verified databases.
Use your general medical knowledge but be very conservative.
If unsure about anything, say 'Ask your doctor or pharmacist about this.'"""

    prompt = f"""You are MediSimply, a medical text simplification assistant for elderly Sinhala speakers in Sri Lanka.

{context}

{source_instruction}

Produce a JSON response with FOUR sections, each in simplified English AND Sinhala.

Rules:
- Write for a 60+ year old person with basic education
- Short sentences (10-15 words max)
- Replace ALL medical jargon with everyday words
- Keep drug names and dosage numbers EXACTLY as they are
- Warm, caring, respectful tone
- Active voice
- For Sinhala: natural spoken Sinhala, not formal/literary
- NEVER invent information not in the provided sources

JSON format only:
{{"what_it_does": {{"english": "...", "sinhala": "..."}}, "how_to_take": {{"english": "...", "sinhala": "..."}}, "warnings_and_side_effects": {{"english": "...", "sinhala": "..."}}, "who_should_not_take": {{"english": "...", "sinhala": "..."}}, "key_points": ["...", "...", "...", "...", "..."]}}
"""

    response = client.models.generate_content(model=MODEL, contents=prompt)
    response_text = response.text.strip()

    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0]

    return json.loads(response_text)


# --- Endpoints ---
@app.get("/")
def home():
    kaggle_count = len(load_kaggle_db())
    openfda_count = len(load_openfda_db())
    rag_status = "active" if rag_index is not None else "not loaded"
    return {
        "message": "MediSimply API v4.0 (with RAG)",
        "status": "running",
        "rag": rag_status,
        "rag_vectors": rag_index.ntotal if rag_index else 0,
        "databases": {
            "kaggle_medicines": kaggle_count,
            "openfda_drugs": openfda_count,
            "total": kaggle_count + openfda_count,
        }
    }


@app.get("/drugs")
def get_drugs():
    names = set()
    for d in load_openfda_db():
        names.add(d["name"])
    for m in load_kaggle_db():
        names.add(m["name"])
    return sorted(list(names))


@app.get("/search/{query}")
def search_drugs(query: str):
    query_lower = query.lower().strip()
    results = []
    for med in load_kaggle_db():
        if query_lower in med["name"].lower() or query_lower in med.get("composition", "").lower():
            results.append(SearchResult(
                name=med["name"],
                composition=med.get("composition", ""),
                image_url=med.get("image_url", ""),
                manufacturer=med.get("manufacturer", ""),
            ))
            if len(results) >= 10:
                break
    return results


@app.post("/lookup", response_model=MedicineResponse)
def lookup_medicine(query: MedicineQuery):
    """
    Main endpoint with RAG:
    1. Search databases for the medicine
    2. Use RAG to retrieve relevant medical passages
    3. Send ONLY relevant passages + data to LLM
    4. Return grounded, simplified result with source attribution
    """
    medicine_name = query.medicine_name.strip()
    if not medicine_name:
        raise HTTPException(status_code=400, detail="Please enter a medicine name")

    # Step 1: Search databases
    kaggle_match, openfda_match = search_medicine(medicine_name)
    found = kaggle_match is not None or openfda_match is not None

    # Step 2: RAG retrieval - find relevant passages
    rag_results = retrieve_relevant_chunks(
        f"{medicine_name} medicine uses dosage warnings side effects",
        top_k=5
    )

    # Step 3: Determine source info
    sources = []
    if rag_results:
        sources.append("RAG Retrieved Passages")
    if kaggle_match:
        sources.append("Kaggle Medicine Database")
    if openfda_match:
        sources.append("openFDA Verified Labels")
    if not sources:
        sources.append("AI Knowledge (not in verified database)")
    source_str = " + ".join(sources)

    # Get metadata from Kaggle
    image_url = kaggle_match.get("image_url", "") if kaggle_match else ""
    composition = kaggle_match.get("composition", "") if kaggle_match else ""
    manufacturer = kaggle_match.get("manufacturer", "") if kaggle_match else ""
    display_name = medicine_name
    if kaggle_match:
        display_name = kaggle_match["name"]
    elif openfda_match:
        display_name = openfda_match["name"]

    # Step 4: Call LLM with RAG context
    try:
        result = simplify_medicine(medicine_name, kaggle_match, openfda_match, rag_results)

        # Build source attribution for frontend
        rag_source_info = [
            SourceInfo(
                text=r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                drug_name=r["drug_name"],
                section=r["section"],
                source=r["source"],
            )
            for r in rag_results
        ]

        return MedicineResponse(
            medicine_name=display_name,
            found_in_database=found,
            source=source_str,
            image_url=image_url,
            composition=composition,
            manufacturer=manufacturer,
            what_it_does=SectionOutput(
                english=result["what_it_does"]["english"],
                sinhala=result["what_it_does"]["sinhala"],
            ),
            how_to_take=SectionOutput(
                english=result["how_to_take"]["english"],
                sinhala=result["how_to_take"]["sinhala"],
            ),
            warnings_and_side_effects=SectionOutput(
                english=result["warnings_and_side_effects"]["english"],
                sinhala=result["warnings_and_side_effects"]["sinhala"],
            ),
            who_should_not_take=SectionOutput(
                english=result["who_should_not_take"]["english"],
                sinhala=result["who_should_not_take"]["sinhala"],
            ),
            key_points=result["key_points"],
            rag_sources=rag_source_info,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Load RAG index when server starts
load_rag()