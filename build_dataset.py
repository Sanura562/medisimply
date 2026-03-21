import requests
import json
import time

BASE_URL = "https://api.fda.gov/drug/label.json"

# Drugs from Sri Lanka's Essential Medicines List (common ones elderly patients use)
SRI_LANKA_DRUGS = [
    "Paracetamol", "Amoxicillin", "Metformin", "Atenolol", "Enalapril",
    "Omeprazole", "Ibuprofen", "Aspirin", "Amlodipine", "Losartan",
    "Atorvastatin", "Metoprolol", "Furosemide", "Glibenclamide", "Insulin",
    "Diclofenac", "Clopidogrel", "Warfarin", "Salbutamol", "Prednisolone",
    "Ciprofloxacin", "Domperidone", "Ranitidine", "Chlorpheniramine", "Erythromycin"
]


def fetch_drug(drug_name):
    """Fetch drug info from openFDA"""
    params = {
        "search": f'openfda.generic_name:"{drug_name}"',
        "limit": 1
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        if "results" not in data or len(data["results"]) == 0:
            return None

        result = data["results"][0]

        # Extract and clean the fields we need
        drug_info = {
            "name": drug_name,
            "purpose": clean_text(result.get("purpose", ["Not available"])[0]),
            "indications": clean_text(result.get("indications_and_usage", ["Not available"])[0]),
            "warnings": clean_text(result.get("warnings", ["Not available"])[0]),
            "dosage": clean_text(result.get("dosage_and_administration", ["Not available"])[0]),
            "active_ingredient": clean_text(result.get("active_ingredient", ["Not available"])[0]),
            "adverse_reactions": clean_text(result.get("adverse_reactions", ["Not available"])[0]),
        }

        return drug_info

    except Exception as e:
        print(f"  Error: {e}")
        return None


def clean_text(text):
    """Remove extra whitespace and limit length"""
    if text == "Not available":
        return text
    # Remove extra spaces and newlines
    cleaned = " ".join(text.split())
    # Limit to first 1000 chars (full text can be very long)
    if len(cleaned) > 1000:
        cleaned = cleaned[:1000] + "..."
    return cleaned


def main():
    print("=" * 60)
    print("  FYP Dataset Builder - Sri Lanka Essential Medicines")
    print("=" * 60)
    print(f"\nFetching data for {len(SRI_LANKA_DRUGS)} drugs...\n")

    all_drugs = []
    failed = []

    for i, drug in enumerate(SRI_LANKA_DRUGS, 1):
        print(f"[{i}/{len(SRI_LANKA_DRUGS)}] {drug}...", end=" ")
        info = fetch_drug(drug)

        if info:
            all_drugs.append(info)
            print("OK")
        else:
            failed.append(drug)
            print("FAILED")

        # Small delay to be respectful to the API
        time.sleep(0.5)

    # Save the dataset
    with open("drug_data.json", "w", encoding="utf-8") as f:
        json.dump(all_drugs, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"  Done! {len(all_drugs)} drugs saved to drug_data.json")
    if failed:
        print(f"  Failed: {', '.join(failed)}")
    print(f"{'=' * 60}")

    # Show a preview of one drug
    if all_drugs:
        print(f"\nPreview of {all_drugs[0]['name']}:")
        for key, value in all_drugs[0].items():
            preview = value[:100] + "..." if len(value) > 100 else value
            print(f"  {key}: {preview}")


# This is like public static void main in Java
if __name__ == "__main__":
    main()
