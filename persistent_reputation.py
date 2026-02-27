import json
from pathlib import Path

REPUTATION_FILE = Path("rule_reputation.json")

class RuleReputation:
    def __init__(self, file_path=REPUTATION_FILE):
        self.file_path = file_path
        self.reputation = self.load_reputation()

    def load_reputation(self):
        if self.file_path.exists():
            with open(self.file_path, "r") as f:
                return json.load(f)
        return {}

    def update(self, logs):
        for log in logs:
            key = f"{log['column']}:{log['action']}"
            scores = self.reputation.get(key, [])
            scores.append(log['confidence'])
        
            self.reputation[key] = scores[-10:]

        self.save()

    def get_score(self, column, action):
        key = f"{column}:{action}"
        scores = self.reputation.get(key, [])
        if not scores:
            return None
        return round(sum(scores) / len(scores), 2)

    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.reputation, f, indent=4)