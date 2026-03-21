import requests
import json

BASE_URL = "https://api.fda.gov/drug/label.json"

def fetch_drug(drug_name):
    params = {
        "search": f'openfda.brand_name:"{drug_name}"',
        "limit": 1
    }
    
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching {drug_name}: {response.status_code}")
        return None
    
    data = response.json()
    
    if "results" not in data or len(data["results"]) == 0:
        print(f"No results found for {drug_name}")
        return None
    
    result = data["results"][0]
    
    drug_info = {
        "name": drug_name,
        "purpose": result.get("purpose", ["Not available"])[0],
        "warnings": result.get("warnings", ["Not available"])[0],
        "dosage": result.get("dosage_and_administration", ["Not available"])[0],
        "active_ingredient": result.get("active_ingredient", ["Not available"])[0],
    }
    
    return drug_info


drugs_to_fetch = ["Paracetamol", "Amoxicillin", "Ibuprofen", "Omeprazole", "Metformin"]

print("Fetching drug data from openFDA...\n")

all_drugs = []

for drug in drugs_to_fetch:
    print(f"Fetching: {drug}...")
    info = fetch_drug(drug)
    if info:
        all_drugs.append(info)
        print(f"  Got it! Purpose: {info['purpose'][:80]}...")
    print()

with open("drug_data.json", "w", encoding="utf-8") as f:
    json.dump(all_drugs, f, indent=2, ensure_ascii=False)

print(f"Saved {len(all_drugs)} drugs to drug_data.json")
