import json

def load_drugs():
    """Load our drug dataset"""
    with open("drug_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


def simplify_text(text):
    """Basic rule-based simplification - we'll replace this with LLM later"""
    if text == "Not available":
        return text

    # Step 1: Replace complex medical terms with simple ones
    replacements = {
        "administered orally": "taken by mouth",
        "oral administration": "taken by mouth",
        "contraindicated": "should not be used",
        "adverse reactions": "side effects",
        "adverse events": "side effects",
        "hypersensitivity": "allergic reaction",
        "hepatic impairment": "liver problems",
        "renal impairment": "kidney problems",
        "cardiovascular": "heart and blood vessel",
        "hypertension": "high blood pressure",
        "hypotension": "low blood pressure",
        "tachycardia": "fast heartbeat",
        "bradycardia": "slow heartbeat",
        "dyspnea": "difficulty breathing",
        "edema": "swelling",
        "nausea": "feeling sick",
        "emesis": "vomiting",
        "pyrexia": "fever",
        "analgesic": "pain reliever",
        "antipyretic": "fever reducer",
        "prophylaxis": "prevention",
        "concomitant": "at the same time",
        "discontinue": "stop taking",
        "pediatric": "children",
        "geriatric": "elderly",
        "milligrams": "mg",
        "immediately seek medical attention": "go to the doctor right away",
        "consult your healthcare provider": "talk to your doctor",
    }

    simplified = text.lower()
    for complex_term, simple_term in replacements.items():
        simplified = simplified.replace(complex_term.lower(), simple_term)

    # Step 2: Take only the first 3 sentences (elderly users need shorter text)
    sentences = simplified.split(". ")
    if len(sentences) > 3:
        simplified = ". ".join(sentences[:3]) + "."

    return simplified


def create_simplified_entry(drug):
    """Create a simplified version of a drug entry"""
    return {
        "name": drug["name"],
        "what_it_does": simplify_text(drug["indications"]),
        "how_to_take": simplify_text(drug["dosage"]),
        "warnings": simplify_text(drug["warnings"]),
        "side_effects": simplify_text(drug["adverse_reactions"]),
    }


def main():
    drugs = load_drugs()
    print(f"Loaded {len(drugs)} drugs\n")

    simplified_drugs = []

    for drug in drugs:
        simplified = create_simplified_entry(drug)
        simplified_drugs.append(simplified)

    # Save simplified dataset
    with open("simplified_drugs.json", "w", encoding="utf-8") as f:
        json.dump(simplified_drugs, f, indent=2, ensure_ascii=False)

    # Show before/after for first drug that has data
    for drug, simple in zip(drugs, simplified_drugs):
        if drug["indications"] != "Not available":
            print(f"Drug: {drug['name']}")
            print(f"\n--- ORIGINAL ---")
            print(f"{drug['indications'][:300]}...")
            print(f"\n--- SIMPLIFIED ---")
            print(f"{simple['what_it_does'][:300]}...")
            print(f"\n--- ORIGINAL WARNINGS ---")
            print(f"{drug['warnings'][:300]}...")
            print(f"\n--- SIMPLIFIED WARNINGS ---")
            print(f"{simple['warnings'][:300]}...")
            break

    print(f"\nSaved {len(simplified_drugs)} simplified drugs to simplified_drugs.json")


if __name__ == "__main__":
    main()
