import asyncio
import json
import os
import numpy as np
import faiss
from dotenv import load_dotenv
from google import genai
from google.genai import types
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import mcp_client
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
# gemini-2.5-flash is deprecated for new API keys/projects (Google's Gemini 3.x
# migration). gemini-3.7-flash (released 2026-08-13) is currently returning
# intermittent 503s under high demand, so we default to gemini-3.6-flash, which
# is stable; swap the string below once 3.7 settles down.
MODEL = "gemini-3.6-flash"

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
    data_source: str = "ai_knowledge_only"  # "local_verified" | "live_mcp_lookup" | "ai_knowledge_only"


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


def search_local_databases(name):
    """Search both local databases (Kaggle + openFDA snapshot) for a medicine"""
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


# --- Agentic MCP tool-calling ---
# This is the NEW capability: instead of a hardcoded if/else deciding when to
# hit the live openFDA API, Gemini's function calling decides for itself
# whether the local match is good enough, based on a short summary of what
# was found locally. Only if Gemini asks for the tool do we actually spawn
# the MCP server (mcp_server/medicine_search_server.py) via mcp_client.

SEARCH_MEDICINE_TOOL = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="search_medicine",
        description=(
            "Look up a medicine LIVE on the openFDA drug label database via "
            "MCP. Use this ONLY if the local database match is missing or "
            "clearly insufficient (e.g. no indications/dosage/warnings info). "
            "If the local match already has good information, do NOT call this."
        ),
        parameters={
            "type": "object",
            "properties": {
                "drug_name": {
                    "type": "string",
                    "description": "The medicine name to look up on openFDA.",
                }
            },
            "required": ["drug_name"],
        },
    )
])

AGENTIC_SYSTEM_INSTRUCTION = (
    "You are deciding how to ground an answer about a medicine for MediSimply. "
    "You will be shown a summary of what MediSimply's local, pre-verified "
    "database already found for this medicine.\n\n"
    "Call search_medicine ONLY if the local summary says no match was found, "
    "or the matched entry is missing indications/dosage/warnings content "
    "(e.g. fields are empty or 'N/A').\n\n"
    "Do NOT call search_medicine if the local summary already contains real "
    "indications, dosage, and warnings text - that data is already verified "
    "and calling the tool again would be redundant. In that case, just "
    "acknowledge the local match is sufficient and stop, without calling any tool."
)


def summarize_local_match(medicine_name, kaggle_match, openfda_match):
    """Short text summary of what the local DB search found, for Gemini to judge."""
    if not kaggle_match and not openfda_match:
        return f"No local match found for '{medicine_name}' in either database."

    parts = []
    if kaggle_match:
        parts.append(
            f"Kaggle DB match: name={kaggle_match.get('name')}, "
            f"composition={kaggle_match.get('composition', 'N/A')}, "
            f"uses={kaggle_match.get('uses', 'N/A')}"
        )
    if openfda_match:
        parts.append(
            f"openFDA (local snapshot) match: name={openfda_match.get('name')}, "
            f"indications={openfda_match.get('indications', 'N/A')}, "
            f"dosage={openfda_match.get('dosage', 'N/A')}, "
            f"warnings={openfda_match.get('warnings', 'N/A')}"
        )
    return "\n".join(parts)


def _extract_function_call(response):
    """Pull the first function_call part out of a Gemini response, if any."""
    if not response.candidates:
        return None
    parts = response.candidates[0].content.parts or []
    for part in parts:
        if part.function_call:
            return part.function_call
    return None


def decide_and_maybe_fetch_live(medicine_name, kaggle_match, openfda_match):
    """
    THE AGENTIC STEP.

    Gives Gemini the local search summary + the search_medicine tool
    declaration and lets IT decide whether to call the tool - there is no
    hardcoded if/else here. If Gemini emits a function call, we execute it
    via mcp_client (a real MCP round trip to mcp_server/medicine_search_server.py),
    feed the tool result back to Gemini as a function response so it can
    continue, and return the live data for grounding.

    Returns the live MCP result dict (with "found": True) if Gemini called
    the tool and openFDA had data, otherwise None.
    """
    local_summary = summarize_local_match(medicine_name, kaggle_match, openfda_match)

    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=(
                f"User is asking about the medicine: '{medicine_name}'.\n\n"
                f"Local database search result:\n{local_summary}\n\n"
                "Decide whether to call search_medicine."
            ))],
        )
    ]
    config = types.GenerateContentConfig(
        system_instruction=AGENTIC_SYSTEM_INSTRUCTION,
        tools=[SEARCH_MEDICINE_TOOL],
    )

    response = client.models.generate_content(model=MODEL, contents=contents, config=config)
    function_call = _extract_function_call(response)

    if not function_call:
        print(f"[Agentic] Gemini judged local data sufficient for '{medicine_name}' - no MCP call.")
        return None

    drug_name_arg = function_call.args.get("drug_name", medicine_name)
    print(f"[Agentic] Gemini requested a live MCP lookup for '{drug_name_arg}'.")
    live_result = asyncio.run(mcp_client.call_search_medicine(drug_name_arg))

    # Feed the tool result back to Gemini and let it continue, per the
    # function-calling contract. Its follow-up text isn't used further here -
    # simplify_medicine() below still produces the actual structured output -
    # but completing the round trip keeps this a genuine agentic tool call.
    try:
        contents.append(response.candidates[0].content)
        # Gemini 3.x assigns each function_call an id and expects the matching
        # function_response to echo it back (needed to correlate responses when
        # the model makes parallel tool calls); Part.from_function_response()
        # doesn't accept/propagate id, so build the FunctionResponse directly.
        function_response = types.FunctionResponse(
            id=function_call.id,
            name="search_medicine",
            response=live_result,
        )
        contents.append(types.Content(
            role="user",
            parts=[types.Part(function_response=function_response)],
        ))
        client.models.generate_content(model=MODEL, contents=contents, config=config)
    except Exception as e:
        print(f"[Agentic] Follow-up call after tool response failed (non-fatal): {e}")

    if live_result.get("found"):
        return live_result

    print(f"[Agentic] MCP live lookup found nothing for '{drug_name_arg}': {live_result}")
    return None


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


# FAISS always returns its top_k NEAREST neighbours, even for a query that
# isn't really about anything in the index (there's no "no match" option).
# This threshold filters OUT chunks that aren't actually relevant - applied
# once, right after retrieval, so irrelevant chunks never reach the prompt,
# the data_source label, or the sources shown to the user. Real matches in
# this dataset score ~0.5-0.7; unrelated nearest-neighbours score ~0.77+.
#
# The threshold alone is NOT sufficient, though: generic OTC pain-reliever
# phrasing ("temporarily relieves minor aches and pains...") scores as low
# as ~0.66 - comfortably under this threshold - for a completely unrelated
# drug (e.g. an Ibuprofen chunk for a "Saridon" query), because embedding
# distance measures phrasing similarity, not drug identity. The RAG corpus
# is built from a small fixed list of specific reference drugs, so a chunk
# is only trustworthy grounding if its own drug_name actually matches the
# query - that check (_rag_chunk_matches_query) is the real guard here; the
# distance threshold just additionally trims noisy same-drug chunks.
RAG_RELEVANCE_THRESHOLD = 0.72


def _rag_chunk_matches_query(medicine_name, chunk_drug_name):
    query = medicine_name.strip().lower()
    drug = chunk_drug_name.strip().lower()
    return bool(query) and bool(drug) and (query in drug or drug in query)


def filter_relevant_chunks(rag_results, medicine_name):
    return [
        r for r in rag_results
        if r.get("relevance_score", float("inf")) < RAG_RELEVANCE_THRESHOLD
        and _rag_chunk_matches_query(medicine_name, r.get("drug_name", ""))
    ]


# --- LLM with RAG ---
def simplify_medicine(medicine_name, kaggle_data=None, openfda_data=None, rag_results=None, mcp_live_data=None):
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

    # NEW: live openFDA data fetched on-demand via the MCP tool call, when
    # Gemini decided the local/RAG data above wasn't enough on its own.
    if mcp_live_data and mcp_live_data.get("found"):
        context_parts.append(f"""
From Live openFDA Lookup (fetched live via MCP tool call):
- Indications: {mcp_live_data.get('indications_and_usage', 'N/A')}
- Dosage: {mcp_live_data.get('dosage_and_administration', 'N/A')}
- Warnings: {mcp_live_data.get('warnings', 'N/A')}
- Adverse Reactions: {mcp_live_data.get('adverse_reactions', 'N/A')}
- Contraindications: {mcp_live_data.get('contraindications', 'N/A')}
- Active Ingredient: {mcp_live_data.get('active_ingredient', 'N/A')}
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
    if not response.text:
        raise ValueError("Gemini returned no text content (possibly blocked by safety filters or an unusual finish_reason)")
    response_text = response.text.strip()

    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0]

    return json.loads(response_text)


def check_drug_name_consistency(medicine_name, result):
    """
    Safety-net, not a gate: confirms the generated content actually mentions
    the drug that was searched, to catch wrong-drug hallucinations (grounding
    the answer in an unrelated drug's data) via logs/tests rather than a user
    noticing in a demo. Logs only - a legitimate answer may reasonably use a
    different form of the name (generic vs. brand), so this doesn't block.
    """
    combined_text = " ".join([
        result["what_it_does"]["english"],
        result["how_to_take"]["english"],
        result["warnings_and_side_effects"]["english"],
        result["who_should_not_take"]["english"],
        " ".join(result.get("key_points", [])),
    ]).lower()

    name_token = medicine_name.strip().lower().split()[0] if medicine_name.strip() else ""
    if name_token and name_token not in combined_text:
        print(
            f"[Consistency Check] WARNING: generated content for '{medicine_name}' "
            f"never mentions '{name_token}' - possible wrong-drug hallucination."
        )


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

    # Step 1: Search local databases
    kaggle_match, openfda_match = search_local_databases(medicine_name)
    found = kaggle_match is not None or openfda_match is not None

    # Step 2: RAG retrieval - find relevant passages, then drop any chunk
    # that isn't actually about this drug (see filter_relevant_chunks) before
    # it can reach the prompt, the label, or the sources shown to the user.
    rag_results = filter_relevant_chunks(retrieve_relevant_chunks(
        f"{medicine_name} medicine uses dosage warnings side effects",
        top_k=5
    ), medicine_name)

    # Step 2.5 (NEW, agentic): let Gemini decide - based on what step 1/2 found -
    # whether to call the live search_medicine MCP tool. No hardcoded if/else;
    # Gemini's function calling makes the call. Never let a hiccup here (e.g.
    # a transient Gemini/MCP error) crash the whole /lookup request.
    try:
        live_data = decide_and_maybe_fetch_live(medicine_name, kaggle_match, openfda_match)
    except Exception as e:
        print(f"[Agentic] tool-decision step failed, falling back to local/AI-only: {e}")
        live_data = None

    if live_data:
        data_source = "live_mcp_lookup"
    elif found or rag_results:
        data_source = "local_verified"
    else:
        data_source = "ai_knowledge_only"

    # Step 3: Determine source info
    sources = []
    if rag_results:
        sources.append("RAG Retrieved Passages")
    if kaggle_match:
        sources.append("Kaggle Medicine Database")
    if openfda_match:
        sources.append("openFDA Verified Labels")
    if live_data:
        sources.append("Live openFDA Lookup (via MCP)")
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

    # Step 4: Call LLM with RAG context (+ live MCP data, if any)
    try:
        result = simplify_medicine(medicine_name, kaggle_match, openfda_match, rag_results, live_data)
        check_drug_name_consistency(medicine_name, result)

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
            data_source=data_source,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Load RAG index when server starts
load_rag()