import json
import os
from dotenv import load_dotenv
from google import genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"

app = FastAPI(title="MediSimply API", version="2.0.0")

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


class MedicineResponse(BaseModel):
    medicine_name: str
    found_in_database: bool
    what_it_does: SectionOutput
    how_to_take: SectionOutput
    warnings_and_side_effects: SectionOutput
    who_should_not_take: SectionOutput
    key_points: list[str]


# --- Load drug database ---
def load_drugs():
    with open("drug_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


def find_drug(name):
    """Search for a drug in our database (case-insensitive)"""
    drugs = load_drugs()
    name_lower = name.lower().strip()
    for drug in drugs:
        if drug["name"].lower() == name_lower:
            return drug
    # Also try partial match
    for drug in drugs:
        if name_lower in drug["name"].lower() or drug["name"].lower() in name_lower:
            return drug
    return None


# --- LLM Call ---
def simplify_medicine(medicine_name, database_info=None):
    """Ask LLM to simplify medicine information"""

    if database_info:
        # We have data from our database - ground the LLM with it
        context = f"""
Here is verified medical data from openFDA for {medicine_name}:

Indications: {database_info.get('indications', 'Not available')}
Dosage: {database_info.get('dosage', 'Not available')}
Warnings: {database_info.get('warnings', 'Not available')}
Adverse Reactions: {database_info.get('adverse_reactions', 'Not available')}
Active Ingredient: {database_info.get('active_ingredient', 'Not available')}
"""
        source_instruction = "Use ONLY the verified data provided above. Do not add information that is not in the data."
    else:
        # No database match - use LLM knowledge but warn
        context = f"The user is asking about: {medicine_name}"
        source_instruction = """You are using your general medical knowledge since this medicine was not found in our verified database.
Be conservative - only state things you are confident about. If unsure about anything, say "Ask your doctor about this."
"""

    prompt = f"""You are MediSimply, a medical text simplification assistant for elderly Sinhala speakers in Sri Lanka.

{context}

{source_instruction}

Produce a JSON response with FOUR sections, each in simplified English AND Sinhala.

Rules for simplification:
- Write for a 60+ year old person with basic education
- Use short sentences (10-15 words maximum)
- Replace ALL medical jargon with everyday words
- Keep drug names and dosage numbers EXACTLY as they are
- Use warm, caring, respectful tone (like a kind pharmacist explaining)
- Use active voice ("Take this medicine" not "This medicine should be taken")
- For Sinhala: use natural spoken Sinhala, not formal/literary style

Respond in this EXACT JSON format only, no other text:
{{
    "what_it_does": {{
        "english": "Simple explanation of what this medicine does...",
        "sinhala": "මෙම බෙහෙත කරන දේ..."
    }},
    "how_to_take": {{
        "english": "Simple dosage instructions...",
        "sinhala": "බෙහෙත ගන්නේ කෙසේද..."
    }},
    "warnings_and_side_effects": {{
        "english": "Simple warnings and possible side effects...",
        "sinhala": "අනතුරු ඇඟවීම් සහ අතුරු ආබාධ..."
    }},
    "who_should_not_take": {{
        "english": "Who should avoid this medicine...",
        "sinhala": "මෙම බෙහෙත නොගත යුත්තේ කාටද..."
    }},
    "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"]
}}
"""

    response = client.models.generate_content(model=MODEL, contents=prompt)
    response_text = response.text.strip()

    # Remove markdown code blocks if present
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0]

    return json.loads(response_text)


# --- Endpoints ---
@app.get("/")
def home():
    return {"message": "MediSimply API v2.0", "status": "running"}


@app.get("/drugs")
def get_drugs():
    """Get list of all drugs in our database"""
    drugs = load_drugs()
    return [d["name"] for d in drugs]


@app.post("/lookup", response_model=MedicineResponse)
def lookup_medicine(query: MedicineQuery):
    """
    Main endpoint: User types a medicine name.
    1. Search our database
    2. If found, use verified data + LLM to simplify
    3. If not found, use LLM knowledge but flag it
    """
    medicine_name = query.medicine_name.strip()
    if not medicine_name:
        raise HTTPException(status_code=400, detail="Please enter a medicine name")

    # Step 1: Search database
    drug_data = find_drug(medicine_name)
    found = drug_data is not None

    # Step 2: Call LLM with or without database context
    try:
        result = simplify_medicine(medicine_name, drug_data)

        return MedicineResponse(
            medicine_name=medicine_name,
            found_in_database=found,
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
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simplifying: {str(e)}")