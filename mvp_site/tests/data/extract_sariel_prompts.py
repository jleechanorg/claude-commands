#!/usr/bin/env python3
"""
Extract the first 10 LLM prompts from Sariel campaign for integration testing.
This includes the initial campaign setup prompt and player interactions.
"""

import json
import os
from datetime import datetime


class SarielPromptExtractor:
    """Extract prompts from Sariel campaign data"""

    def __init__(self):
        self.campaign_data = None
        self.prompts = []

    def load_campaign_data(self, json_path):
        """Load campaign data from JSON file"""
        if not os.path.exists(json_path):
            # Try alternative path
            alt_path = json_path.replace(
                "statesync3_184dde0e4868b73b", "statesync2_184d8886fb5997c5"
            )
            if os.path.exists(alt_path):
                json_path = alt_path
            else:
                raise FileNotFoundError(f"Campaign data not found: {json_path}")

        with open(json_path) as f:
            self.campaign_data = json.load(f)

    def extract_initial_prompt(self):
        """Extract the initial campaign setup prompt"""
        # Based on the campaign structure, create an initial prompt
        initial_prompt = {
            "type": "initial_setup",
            "mode": "god",
            "content": """Create a new D&D campaign with the following setup:
            
Player Character: Sariel, a member of House Arcanus
Setting: A medieval fantasy world with political intrigue
Starting Location: The throne room of a grand castle

Initialize the campaign with:
- Player character data for Sariel
- Initial NPCs including advisors and court members
- The immediate scenario where Sariel must make important decisions

Begin the narrative with Sariel arriving at court for an important meeting.""",
            "expected_state_updates": {
                "player_character_data": {"name": "Sariel"},
                "npc_data": {},
                "location": "Throne Room",
            },
        }
        return initial_prompt

    def extract_player_prompts(self):
        """Extract the first 10 player interaction prompts"""
        prompts = []

        if not self.campaign_data or "interactions" not in self.campaign_data:
            return prompts

        for i, interaction in enumerate(self.campaign_data["interactions"][:10]):
            # Determine the mode based on interaction context
            mode = "main character"  # Default to character mode

            # Build the prompt structure
            prompt = {
                "type": "player_interaction",
                "interaction_number": i + 1,
                "mode": mode,
                "content": interaction["player_input"]["content"],
                "context": {
                    "location": interaction["location"],
                    "timestamp": interaction["timestamp"],
                    "expected_entities": interaction.get("expected_entities", []),
                },
                "metadata": {
                    "is_cassian_problem": i == 1,  # The famous interaction #2
                    "original_player_input": interaction["player_input"]["content"],
                },
            }

            prompts.append(prompt)

        return prompts

    def format_prompts_for_testing(self):
        """Format prompts in a way suitable for integration testing"""
        formatted = []

        # Add initial prompt
        initial = self.extract_initial_prompt()
        formatted.append(
            {
                "prompt_id": "initial_setup",
                "mode": initial["mode"],
                "input": initial["content"],
                "expected_updates": initial["expected_state_updates"],
            }
        )

        # Add player prompts
        player_prompts = self.extract_player_prompts()
        for prompt in player_prompts:
            formatted.append(
                {
                    "prompt_id": f"interaction_{prompt['interaction_number']}",
                    "mode": prompt["mode"],
                    "input": prompt["content"],
                    "context": prompt["context"],
                    "metadata": prompt["metadata"],
                }
            )

        return formatted

    def save_prompts(self, output_path):
        """Save extracted prompts to a JSON file"""
        prompts = self.format_prompts_for_testing()

        output_data = {
            "campaign": "sariel_v2",
            "extraction_date": datetime.now().isoformat(),
            "total_prompts": len(prompts),
            "prompts": prompts,
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"Saved {len(prompts)} prompts to {output_path}")

    def display_prompts(self):
        """Display the extracted prompts in a readable format"""
        prompts = self.format_prompts_for_testing()

        print("=== Sariel Campaign Prompts ===")
        print(f"Total prompts: {len(prompts)}")
        print()

        for i, prompt in enumerate(prompts):
            print(f"[{i}] {prompt['prompt_id']} ({prompt['mode']} mode)")
            print(
                f"Input: {prompt['input'][:100]}..."
                if len(prompt["input"]) > 100
                else f"Input: {prompt['input']}"
            )
            if "context" in prompt:
                print(f"Location: {prompt['context'].get('location', 'N/A')}")
            print("-" * 50)


def main():
    """Main function to extract and display Sariel campaign prompts"""
    extractor = SarielPromptExtractor()

    # Load campaign data
    json_path = "/home/jleechan/.claude-squad/worktrees/statesync3_184dde0e4868b73b/prototype/tests/milestone_0.4/tmp/sariel_v2_first_10_log.json"

    try:
        extractor.load_campaign_data(json_path)
        print(f"Loaded campaign data from: {json_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # Display prompts
    extractor.display_prompts()

    # Save prompts for integration testing
    output_path = "/home/jleechan/.claude-squad/worktrees/statesync3_184dde0e4868b73b/mvp_site/sariel_campaign_prompts.json"
    extractor.save_prompts(output_path)


if __name__ == "__main__":
    main()
