#!/usr/bin/env python3
"""
Apply comprehensive timeline enhancements to the Alexiel book
"""

import re
import os

def apply_timeline_enhancements(input_file, output_file):
    """Apply all timeline enhancements to the book"""
    
    print("Reading original book...")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Applying timeline enhancements...")
    
    # 1. Add Arc Timeline Summaries
    arc_summaries = {
        "Arc 1\n": """Arc 1

### Timeline Summary: Pre-Arc 1
- Year 61: Alexiel is created by Lucifer
- Year 71: At age 10, begins advanced combat training
- Year 74: At age 13, masters combat against constructs
- Year 76: At age 15, receives "Promise of the Throne"
- Year 78: Current story begins, Alexiel age 17

""",
        "ch 6\n": """ch 6

### Timeline Summary: Arc 1 → Arc 2
- Year 78, Month of Scourge: Alexiel defects at age 17
- Year 78, Month of Scourge: Arrives at Fortress Vigil
- Year 78, Month of Mirtul: Travels to Aeterna
- Year 78, Month of Eleasis: Marries Artorius (age 17)
- Year 78, Month of Eleint: Takes command of Third Regiment
- Year 79: Birth of twins Cassian and Valerius (Alexiel age 18)
- Year 80: Birth of daughter Sariel (Alexiel age 19)

""",
        "ch 18\n": """ch 18

### Timeline Summary: Arc 2 → Arc 3
- Year 78: Alexiel defects and marries at age 17
- Year 79-81: Consolidates power in the Imperium
- Year 82: Assassination attempt at age 21
- Year 82: Alexiel appointed as Magister of the Watch
- Year 83: Battle of Mourning Fields at age 22

"""
    }
    
    for marker, summary in arc_summaries.items():
        content = content.replace(marker, summary, 1)
    
    # 2. Add age references at key timestamps
    age_insertions = [
        # Year 78 - Age 17
        (r"(Timestamp: Year of the Unchained Host, 78\. Month of Scourge.*?\n.*?Location:.*?\n)(?!\[Alexiel)", r"\1\n[Alexiel: Age 17]\n"),
        (r"(Timestamp: Year of the Unchained Host, 78\. Month of Mirtul.*?\n.*?Location:.*?\n)(?!\[Alexiel)", r"\1\n[Alexiel: Age 17]\n"),
        (r"(Timestamp: Year of the Unchained Host, 78\. Month of Eleasis.*?\n.*?Location:.*?\n)(?!\[Alexiel)", r"\1\n[Alexiel: Age 17]\n"),
        (r"(Timestamp: Year of the Unchained Host, 78\. Month of Eleint.*?\n.*?Location:.*?\n)(?!\[Alexiel)", r"\1\n[Alexiel: Age 17]\n"),
        
        # Year 79 - Age 18
        (r"(Timestamp: Year of the Unchained Host, 79.*?\n.*?Location:.*?\n)(?!\[Alexiel)", r"\1\n[Alexiel: Age 18]\n"),
        
        # Year 80 - Age 19
        (r"(Timestamp: Year of the Unchained Host, 80.*?\n.*?Location:.*?\n)(?!\[Alexiel)", r"\1\n[Alexiel: Age 19]\n"),
        
        # Year 82 - Age 21
        (r"(Timestamp: Year of the Unchained Host, 82.*?\n.*?Location:.*?\n)(?!\[Alexiel)", r"\1\n[Alexiel: Age 21]\n"),
        
        # Year 83 - Age 22
        (r"(Timestamp: Year of the Unchained Host, 83.*?\n.*?Location:.*?\n)(?!\[Alexiel)", r"\1\n[Alexiel: Age 22]\n"),
    ]
    
    for pattern, replacement in age_insertions:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 3. Add "years since" references for major time jumps
    years_since_insertions = [
        # Year 82
        (r"(\[Alexiel: Age 21\]\n)(?!\[4 years)", r"\1[4 years since defection / 3 years since marriage]\n"),
        
        # Year 83
        (r"(\[Alexiel: Age 22\]\n)(?!\[5 years)", r"\1[5 years since defection / 4 years since marriage]\n"),
    ]
    
    for pattern, replacement in years_since_insertions:
        content = re.sub(pattern, replacement, content)
    
    # 4. Add relative time markers
    relative_time_markers = [
        # Training scene after wedding
        ("Timestamp: Year of the Unchained Host, 78. Month of Eleint, Day 3.", 
         "[Three weeks after the wedding...]\n\nTimestamp: Year of the Unchained Host, 78. Month of Eleint, Day 3."),
        
        # Jump to Year 82
        ("Timestamp: Year of the Unchained Host, 82. Month of Kythorn",
         "[Four years later...]\n\nTimestamp: Year of the Unchained Host, 82. Month of Kythorn"),
        
        # Jump to Year 83
        ("Timestamp: Year of the Unchained Host, 83. Month of Flamerule",
         "[One year later...]\n\nTimestamp: Year of the Unchained Host, 83. Month of Flamerule"),
    ]
    
    for old_text, new_text in relative_time_markers:
        content = content.replace(old_text, new_text, 1)
    
    # 5. Remove game stats and replace with narrative descriptions
    game_stat_replacements = [
        # Remove entire game stat blocks
        (r"\[Key Game Stats:.*?\]\n*", ""),
        (r"\[CHARACTER_RESOURCES\]\n*", ""),
        
        # Replace fatigue with narrative
        (r"Fatigue: \d+ \(-\d+ to all d20 rolls\)\n*", "[Physical exhaustion weighing on her movements]\n"),
        
        # Replace level references
        (r"Level \d+", "veteran warrior"),
        (r"Extra Attack \(x\d+\)", "[Years of training evident in her fluid strikes]"),
        
        # Remove XP/HP references
        (r"XP: \d+/\d+\+?", ""),
        (r"HP: \d+/\d+", ""),
    ]
    
    for pattern, replacement in game_stat_replacements:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # 6. Add seasonal/cultural references
    seasonal_additions = [
        ("The Third Imperial Regiment was a study in disgrace.",
         "As the autumn leaves began to turn, marking the approach of the Harvest Festival, the Third Imperial Regiment was a study in disgrace."),
        
        ("Year 79",
         "the Spring Equinox celebrations of Year 79"),
         
        ("The afternoon sunlight streamed through",
         "The Winter Solstice celebrations of the previous year had marked another milestone—Sariel's third birthday had been celebrated with the pageantry befitting an Imperial princess.\n\nThe afternoon sunlight streamed through"),
    ]
    
    for old_text, new_text in seasonal_additions:
        if old_text in content:
            content = content.replace(old_text, new_text, 1)
    
    # 7. Add age references for children
    child_age_patterns = [
        # Sariel
        (r"Sariel(?!, now \d+ years? old)", "Sariel, now four years old"),
        (r"her daughter(?!, now \d+ years? old)", "her daughter, now four years old"),
        
        # Twins
        (r"(?<!The )twins(?!, now \d+ years? old)", "twins, now three years old"),
        (r"Cassian and Valerius(?!, now \d+ years? old)", "Cassian and Valerius, now three years old"),
    ]
    
    # Apply child age patterns only in Year 82 sections
    year_82_start = content.find("Year of the Unchained Host, 82")
    if year_82_start != -1:
        year_83_start = content.find("Year of the Unchained Host, 83", year_82_start)
        if year_83_start == -1:
            year_83_start = len(content)
        
        year_82_section = content[year_82_start:year_83_start]
        
        for pattern, replacement in child_age_patterns:
            year_82_section = re.sub(pattern, replacement, year_82_section)
        
        content = content[:year_82_start] + year_82_section + content[year_83_start:]
    
    # Clean up any double newlines
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    print("Writing enhanced book...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Timeline enhancements complete! Output written to {output_file}")

if __name__ == "__main__":
    input_file = "/home/jleechan/projects/worldarchitect.ai/world/celestial_wars_alexiel_book_cleaned.md"
    output_file = "/home/jleechan/projects/worldarchitect.ai/world/celestial_wars_alexiel_book_timeline_enhanced.md"
    
    if os.path.exists(input_file):
        apply_timeline_enhancements(input_file, output_file)
    else:
        print(f"Error: Input file {input_file} not found!")