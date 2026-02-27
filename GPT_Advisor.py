import json

class GPTAdvisor:
    def __init__(self, profile_path="profiles.json"):
        with open(profile_path, "r") as f:
            self.profiles = json.load(f)
        self.proposed_rules = []

    def generate_rules(self):
        for col, meta in self.profiles.items():
            rule = {"column": col, "confidence": 0.9, "notes": ""}
            if meta["numeric_ratio"] > 0.7:
                rule["action"] = "coerce_to_float"
                rule["notes"] = "Column mostly numeric; remove symbols and commas."
            elif meta["date_ratio"] > 0.6:
                rule["action"] = "parse_date"
                rule["notes"] = "Column mostly date-like; parse to ISO format."
            else:
                rule["action"] = "normalize_text"
                rule["notes"] = "Text/categorical column; lowercase and strip."
            self.proposed_rules.append(rule)

    def save_rules(self, output_path="proposed_rules.json"):
        with open(output_path, "w") as f:
            json.dump(self.proposed_rules, f, indent=4)
        print(f"Proposed rules saved to {output_path}")

if __name__ == "__main__":
    advisor = GPTAdvisor("profiles.json")
    advisor.generate_rules()
    advisor.save_rules()