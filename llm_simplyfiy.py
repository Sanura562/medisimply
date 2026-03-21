import json
import os
from dotenv import load_dotenv
from google import genai

# Load API key from .env file
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-2.5-flash"


def simplify_medical_text(text):
    """Use Gemini to simplify medical text and translate to Sinhala"""

    prompt = f"""You are a medical text simplification assistant for elderly Sinhala speakers in Sri Lanka.

Your task: Take complex medical text and produce TWO outputs:
1. A simplified English version (6th grade reading level)
2. A Sinhala translation of the simplified version

Rules:
- Use short sentences (10-15 words max)
- Replace medical jargon with everyday words
- Keep drug names, dosages, and numbers EXACTLY as they are
- Use active voice
- Be warm and caring in tone
- Never invent information not in the original text
- If something is unclear, say "Ask your doctor about this"

Respond in this exact JSON format:
{{
    "simplified_english": "the simplified text here",
    "sinhala": "the Sinhala translation here",
    "key_points": ["point 1", "point 2", "point 3"]
}}

Medical text to simplify:
{text}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )

    # Parse the JSON from response
    response_text = response.text.strip()

    # Remove markdown code blocks if present
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0]

    return json.loads(response_text)


def main():
    # Load our drug dataset
    with open("drug_data.json", "r", encoding="utf-8") as f:
        drugs = json.load(f)

    print("=" * 60)
    print("  LLM Medical Text Simplifier (Gemini)")
    print("=" * 60)

    # Test with first drug that has indications
    for drug in drugs:
        if drug["indications"] != "Not available":
            test_drug = drug
            break

    print(f"\nDrug: {test_drug['name']}")
    print(f"\n--- ORIGINAL (Complex Medical Text) ---")
    print(test_drug["indications"][:500])

    print(f"\n\nSimplifying with Gemini...\n")

    try:
        result = simplify_medical_text(test_drug["indications"])

        print("--- SIMPLIFIED ENGLISH ---")
        print(result["simplified_english"])

        print(f"\n--- SINHALA TRANSLATION ---")
        print(result["sinhala"])

        print(f"\n--- KEY POINTS ---")
        for i, point in enumerate(result["key_points"], 1):
            print(f"  {i}. {point}")

        # Now simplify warnings too
        if test_drug["warnings"] != "Not available":
            print(f"\n\nSimplifying warnings...\n")
            warnings_result = simplify_medical_text(test_drug["warnings"])

            print("--- SIMPLIFIED WARNINGS ---")
            print(warnings_result["simplified_english"])

            print(f"\n--- WARNINGS IN SINHALA ---")
            print(warnings_result["sinhala"])

        # Save the result
        output = {
            "drug_name": test_drug["name"],
            "original": test_drug["indications"],
            "simplified": result,
        }

        with open("llm_output_sample.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n\nSaved output to llm_output_sample.json")

    except Exception as e:
        print(f"Error: {e}")
        print("Check that your GEMINI_API_KEY is correct in .env")


if __name__ == "__main__":
    main()
