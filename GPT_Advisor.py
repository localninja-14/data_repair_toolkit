import os
import json
import pandas as pd
import openai
from dotenv import load_dotenv
from utils import sanitize_column_name

class GPT_Advisor:
    def __init__(self, profile_path="output/data_profile.json", output_path="output/proposed_rules.json"):
        self.profile_path = profile_path
        self.output_path = output_path
        self.profile = {}
        self.proposals = {}
        self.column_name_map = {}  # maps original -> sanitized

        load_dotenv("tool.env")
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def load_profile(self):
        with open(self.profile_path, "r") as f:
            self.profile = json.load(f)
        # build sanitized name map
        self.column_name_map = {col: sanitize_column_name(col) for col in self.profile.keys()}

    def generate_rules(self):
        # create a sanitized profile for GPT with clean column names
        sanitized_profile = {
            self.column_name_map[col]: stats
            for col, stats in self.profile.items()
        }
        
        prompt = (
            "You are given a dataset profile in JSON format with sanitized column names. "
            "For each sanitized column name, write a Python function definition named "
            "clean_<column_name> that takes a pandas Series as input and returns a cleaned Series. "
            "Output a JSON object mapping each sanitized column name to the string of its function definition. "
            "Do not include any explanatory text, only the JSON.\n\n"
            f"Profile: {json.dumps(sanitized_profile)}"
        )

        try:
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Python assistant that outputs exactly the requested JSON mapping."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            text = completion.choices[0].message.content.strip()
            # proposals are indexed by sanitized column names
            sanitized_proposals = json.loads(text)
            # map back to original column names
            self.proposals = {
                orig: sanitized_proposals.get(sanitized, f"def clean_{sanitized}(s):\n    return s")
                for orig, sanitized in self.column_name_map.items()
            }
        except Exception:
            # fallback: identity functions for each original column
            self.proposals = {
                orig: f"def clean_{sanitized}(s):\n    return s"
                for orig, sanitized in self.column_name_map.items()
            }

    def save_proposals(self):
        output_data = {
            "column_name_map": self.column_name_map,
            "proposals": self.proposals,
        }
        with open(self.output_path, "w") as f:
            json.dump(output_data, f, indent=4)

if __name__ == "__main__":
    advisor = GPT_Advisor()
    advisor.load_profile()
    advisor.generate_rules()
    advisor.save_proposals()
    print(f"Proposals saved to {advisor.output_path}")