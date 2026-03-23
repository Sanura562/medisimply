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

app = FastAPI(title="MediSimply API", version="3.0.0")

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
    source: str
    image_url: str = ""
    composition: str = ""
    manufacturer: str = ""
    what_it_does: SectionOutput
    how_to_take: SectionOutput
    warnings_and_side_effects: SectionOutput
    who_should_not_take: SectionOutput
    key_points: list[str]


class SearchResult(BaseModel):
    name: str
    composition: str
    image_url: str
    manufacturer: str


# --- Load databases ---
def load_kaggle_db():
    """Load the 11K Kaggle medicines database"""
    try:
        with open("medicines_db.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def load_openfda_db():
    """Load our openFDA curated database"""
    try:
        with open("drug_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def search_medicine(name):
    """
    Search for a medicine across both databases.
    Priority: Kaggle (has images) > openFDA (has detailed medical data)
    """
    name_lower = name.lower().strip()
    kaggle_match = None
    openfda_match = None

    # Search Kaggle DB (11K medicines with images)
    kaggle_db = load_kaggle_db()
    for med in kaggle_db:
        med_name_lower = med["name"].lower()
        if name_lower == med_name_lower or name_lower in med_name_lower or med_name_lower in name_lower:
            kaggle_match = med
            break

    # Also try matching by composition (e.g., user types "Amoxicillin" but DB has "Augmentin 625 Duo Tablet")
    if not kaggle_match:
        for med in kaggle_db:
            if name_lower in med.get("composition", "").lower():
                kaggle_match = med
                break

    # Search openFDA DB
    openfda_db = load_openfda_db()
    for drug in openfda_db:
        if drug["name"].lower() == name_lower or name_lower in drug["name"].lower():
            openfda_match = drug
            break

    return kaggle_match, openfda_match


# --- LLM Call ---
def simplify_medicine(medicine_name, kaggle_data=None, openfda_data=None):
    """Ask LLM to simplify medicine information using available data"""

    context_parts = []

    if kaggle_data:
        context_parts.append(f"""
From Kaggle Medicine Database:
- Name: {kaggle_data['name']}
- Composition: {kaggle_data.get('composition', 'N/A')}
- Uses: {kaggle_data.get('uses', 'N/A')}
- Side Effects: {kaggle_data.get('side_effects', 'N/A')}
- Manufacturer: {kaggle_data.get('manufacturer', 'N/A')}
""")

    if openfda_data:
        context_parts.append(f"""
From openFDA Verified Database:
- Indications: {openfda_data.get('indications', 'N/A')}
- Dosage: {openfda_data.get('dosage', 'N/A')}
- Warnings: {openfda_data.get('warnings', 'N/A')}
- Adverse Reactions: {openfda_data.get('adverse_reactions', 'N/A')}
- Contraindications: {openfda_data.get('contraindications', 'N/A')}
""")

    if context_parts:
        context = "Here is verified medical data:\n" + "\n".join(context_parts)
        source_instruction = "Use the verified data provided above as your primary source. You may supplement with your medical knowledge only when the data says 'N/A' or 'Not available'."
    else:
        context = f"The user is asking about: {medicine_name}"
        source_instruction = """This medicine was NOT found in our verified databases.
Use your general medical knowledge but be conservative.
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
- Warm, caring, respectful tone (like a kind pharmacist)
- Active voice ("Take this medicine" not "This medicine should be taken")
- For Sinhala: use natural spoken Sinhala, not formal/literary style
- Never invent information

JSON format only, no other text:
{{
    "what_it_does": {{
        "english": "...",
        "sinhala": "..."
    }},
    "how_to_take": {{
        "english": "...",
        "sinhala": "..."
    }},
    "warnings_and_side_effects": {{
        "english": "...",
        "sinhala": "..."
    }},
    "who_should_not_take": {{
        "english": "...",
        "sinhala": "..."
    }},
    "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"]
}}
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
    return {
        "message": "MediSimply API v3.0",
        "status": "running",
        "databases": {
            "kaggle_medicines": kaggle_count,
            "openfda_drugs": openfda_count,
            "total": kaggle_count + openfda_count,
        }
    }


@app.get("/drugs")
def get_drugs():
    """Get list of all unique drug names from both databases"""
    names = set()
    for d in load_openfda_db():
        names.add(d["name"])
    for m in load_kaggle_db():
        names.add(m["name"])
    return sorted(list(names))


@app.get("/search/{query}")
def search_drugs(query: str):
    """Search medicines by name - returns top 10 matches with images"""
    query_lower = query.lower().strip()
    results = []

    # Search Kaggle DB first (has images)
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
    """Main endpoint: User types medicine name, gets simplified info"""
    medicine_name = query.medicine_name.strip()
    if not medicine_name:
        raise HTTPException(status_code=400, detail="Please enter a medicine name")

    # Search both databases
    kaggle_match, openfda_match = search_medicine(medicine_name)
    found = kaggle_match is not None or openfda_match is not None

    # Determine source info
    if kaggle_match and openfda_match:
        source = "openFDA + Kaggle Medicine Database"
    elif kaggle_match:
        source = "Kaggle Medicine Database (11K medicines)"
    elif openfda_match:
        source = "openFDA Verified Drug Labels"
    else:
        source = "AI Knowledge (not in verified database)"

    # Get image and metadata from Kaggle match
    image_url = kaggle_match.get("image_url", "") if kaggle_match else ""
    composition = kaggle_match.get("composition", "") if kaggle_match else ""
    manufacturer = kaggle_match.get("manufacturer", "") if kaggle_match else ""

    # Use display name from whichever database matched
    display_name = medicine_name
    if kaggle_match:
        display_name = kaggle_match["name"]
    elif openfda_match:
        display_name = openfda_match["name"]

    # Call LLM with all available data
    try:
        result = simplify_medicine(medicine_name, kaggle_match, openfda_match)

        return MedicineResponse(
            medicine_name=display_name,
            found_in_database=found,
            source=source,
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
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")