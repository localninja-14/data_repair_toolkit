import json

class RuleReview:
    def __init__(self, proposed_path="proposed_rules.json"):
        with open(proposed_path, "r") as f:
            self.rules = json.load(f)
        self.approved_rules = []

    def review_rules(self):
        print("=== Human-in-the-loop Rule Review ===")
        for idx, rule in enumerate(self.rules):
            print(f"\nRule {idx+1}:")
            print(f"Column: {rule['column']}")
            print(f"Suggested action: {rule['action']}")
            print(f"Confidence: {rule['confidence']}")
            print(f"Notes: {rule['notes']}")
            
            while True:
                choice = input("Approve (a), Reject (r), Modify (m): ").strip().lower()
                if choice == "a":
                    self.approved_rules.append(rule)
                    break
                elif choice == "r":
                    print("Rule rejected.")
                    break
                elif choice == "m":
                    new_action = input("New action: ").strip()
                    new_notes = input("New notes: ").strip()
                    rule["action"] = new_action or rule["action"]
                    rule["notes"] = new_notes or rule["notes"]
                    self.approved_rules.append(rule)
                    break
                else:
                    print("Invalid input. Choose 'a', 'r', or 'm'.")

    def save_approved(self, output_path="approved_rules.json"):
        with open(output_path, "w") as f:
            json.dump(self.approved_rules, f, indent=4)
        print(f"Approved rules saved to {output_path}")

if __name__ == "__main__":
    reviewer = RuleReview("proposed_rules.json")
    reviewer.review_rules()
    reviewer.save_approved()