class PromptBuilder:
    """Simplified PromptBuilder used for unit tests."""
    def __init__(self, game_state):
        self.game_state = game_state

    def build_core_system_instructions(self):
        return ""

    def add_character_instructions(self, character_name, campaign_instructions):
        return ""

    def add_selected_prompt_instructions(self, selected_prompt):
        return ""

    def add_system_reference_instructions(self, system_reference):
        return ""

    def build_companion_instruction(self):
        companions = None
        if hasattr(self.game_state, 'data'):
            companions = self.game_state.data.get('game_state', {}).get('companions')
        if not companions:
            return ""
        if not isinstance(companions, dict) or len(companions) == 0:
            return ""
        lines = ["**ACTIVE COMPANIONS**"]
        for name, info in companions.items():
            if not isinstance(info, dict):
                continue
            cls = info.get('class', 'Unknown')
            lines.append(f"- {name} ({cls})")
        return "\n".join(lines)

    def build_background_summary_instruction(self):
        story = None
        if hasattr(self.game_state, 'data'):
            story = self.game_state.data.get('game_state', {}).get('story')
        summary = None
        if isinstance(story, dict):
            summary = story.get('summary')
        if not summary:
            return ""
        return f"**STORY SUMMARY**\n{summary}"

    def finalize_instructions(self, character_name, campaign_instructions, selected_prompt, system_reference):
        parts = []
        for part in [
            self.build_core_system_instructions(),
            self.add_character_instructions(character_name, campaign_instructions),
            self.add_selected_prompt_instructions(selected_prompt),
            self.add_system_reference_instructions(system_reference),
            self.build_companion_instruction(),
            self.build_background_summary_instruction(),
        ]:
            cleaned = part.strip()
            if cleaned:
                parts.append(cleaned)
        return "\n\n".join(parts)
