import csv
import json

def import_kaggle_dataset():
    """Import the 11K medicine dataset from Kaggle CSV into our project format"""

    medicines = []

    with open("Medicine_Details.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            medicine = {
                "name": row["Medicine Name"].strip(),
                "composition": row["Composition"].strip(),
                "uses": row["Uses"].strip(),
                "side_effects": row["Side_effects"].strip(),
                "image_url": row["Image URL"].strip().strip('"'),
                "manufacturer": row["Manufacturer"].strip(),
                "reviews": {
                    "excellent": row.get("Excellent Review %", "0"),
                    "average": row.get("Average Review %", "0"),
                    "poor": row.get("Poor Review %", "0"),
                },
            }
            medicines.append(medicine)

    # Save as JSON
    with open("medicines_db.json", "w", encoding="utf-8") as f:
        json.dump(medicines, f, indent=2, ensure_ascii=False)

    print(f"Imported {len(medicines)} medicines to medicines_db.json")

    # Print some stats
    with_images = sum(1 for m in medicines if m["image_url"] and m["image_url"] != "")
    with_uses = sum(1 for m in medicines if m["uses"] and m["uses"] != "")
    with_side_effects = sum(1 for m in medicines if m["side_effects"] and m["side_effects"] != "")

    print(f"\nStats:")
    print(f"  With images: {with_images}")
    print(f"  With uses: {with_uses}")
    print(f"  With side effects: {with_side_effects}")

    # Show first 5 as preview
    print(f"\nFirst 5 medicines:")
    for m in medicines[:5]:
        print(f"  - {m['name']} ({m['composition'][:50]}...)")


if __name__ == "__main__":
    import_kaggle_dataset()
