#!/usr/bin/env python3
"""
Apply comprehensive prose improvements with more thorough pattern matching
"""

import os
import re


def apply_comprehensive_improvements(input_file, output_file):
    """Apply all prose improvements more thoroughly"""

    print("Reading timeline-enhanced book...")
    with open(input_file, encoding="utf-8") as f:
        content = f.read()

    print("Applying comprehensive prose improvements...")

    # 1. REPETITIVE DESCRIPTORS - More comprehensive cold replacements
    cold_patterns = [
        (r"\bcold calculations\b", "dispassionate assessment"),
        (r"\bcold strategist\b", "calculating mind"),
        (r"\bcold engine of analysis\b", "relentless processor"),
        (r"\bcold, quiet finality\b", "stark certainty"),
        (r"\bcold analysis\b", "methodical evaluation"),
        (r"\bcold precision\b", "clinical accuracy"),
        (r"\bcold assessment\b", "detached appraisal"),
        (r"\bcold logic\b", "inexorable reasoning"),
        (r"\bcold mind\b", "analytical intellect"),
        (r"\bcold fury\b", "glacial rage"),
        (r"\bcold clarity\b", "crystalline focus"),
        (r"\bcold certainty\b", "absolute conviction"),
        (r"\bcold satisfaction\b", "quiet satisfaction"),
        (r"\bcold contempt\b", "withering disdain"),
    ]

    for pattern, replacement in cold_patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    # 2. RPG MECHANICS - More thorough removal
    rpg_patterns = [
        (r"\bher secret magic, her Power Layer 1—", "her secret magic—"),
        (r"\bPower Layer 1\b", "telekinetic force"),
        (r'\bLayer 2 \("?The Reluctant Champion"?\)', "her carefully crafted facade"),
        (r"\bLayer 3.*?(?:Joyful Predator|mind)", "true predatory nature"),
        (r"\bher Layer 2.*?persona", "her facade"),
        (r"\bLayer 1.*?(?:Prodigal Sword)", "original identity"),
        (r"\bSecond Wind technique", "breathing technique"),
        (r"\bAction Surge\b", "burst of speed"),
        (r"\bhidden Layer 3 mind", "hidden true nature"),
        (r"\bLayer 3 \(.*?\)", "true self"),
        (r"\bthe Layer 2", "the facade"),
        (r"\bLayer \d+", "persona"),
    ]

    for pattern, replacement in rpg_patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    # 3. TELLING EMOTIONS - More comprehensive showing
    emotion_patterns = [
        (
            r"She was, to her immense surprise, somewhat touched",
            "She found herself hesitating, her prepared response dying on her lips",
        ),
        (
            r"\bfelt a surge of pride\b",
            "straightened slightly, satisfaction flickering across her features",
        ),
        (
            r"\bwas deeply moved\b",
            "felt something shift in her chest, unexpected and unwelcome",
        ),
        (r"\bfelt genuine affection\b", "caught herself almost smiling"),
        (r"\bwas terrified\b", "felt her hands begin to tremble"),
        (r"\bfelt relief\b", "released a breath she didn't realize she'd been holding"),
        (r"\bwas surprised\b", "blinked, caught off guard"),
        (r"\bfelt anger\b", "her jaw tightened"),
        (r"\bwas confused\b", "frowned, pieces refusing to fit together"),
        (r"\bfelt fear\b", "her pulse quickened"),
    ]

    for pattern, replacement in emotion_patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    # 4. CHARACTER VOICES - More comprehensive speech pattern changes
    # Make Cato more direct and practical
    content = re.sub(r'"([^"]*?)," Cato said', r'"\1," Cato grunted', content)
    content = re.sub(
        r'"Your orders, my Lady\?"', '"What\'s the plan, Commander?"', content
    )
    content = re.sub(r'"As you command, my Lady"', '"Understood, Commander"', content)
    content = re.sub(r'"Very well, my Lady"', '"Copy that, Commander"', content)

    # Make Raziel more grandiose and formal
    content = re.sub(
        r'"The situation requires"',
        '"The permutations of circumstance demand"',
        content,
    )
    content = re.sub(
        r'"It is logical"', '"The calculus of probability suggests"', content
    )
    content = re.sub(
        r'"We must consider"', '"The variables before us dictate"', content
    )

    # Make young guards more nervous
    content = re.sub(
        r'"Yes, my Lady\. As you command\."',
        '"I— yes, my lady. As you command."',
        content,
    )
    content = re.sub(r'"My Lady, the"', '"My lady, the— the"', content)

    # 5. OVEREXPLAINING MAGIC - Make more mysterious
    magic_patterns = [
        (
            r"She would overload it\. She would pour every last drop of her life force, her will, her very soul into it",
            "She would break the careful limits she had always maintained. She would become the void itself",
        ),
        (r"\btelekinetic power\b", "invisible force"),
        (r"\bpsychic energy\b", "will made manifest"),
        (r"\bmagical resonance\b", "otherworldly harmony"),
        (r"\barcane formulae\b", "forbidden mathematics"),
        (r"\bmagical abilities\b", "hidden talents"),
        (r"\bmystic arts\b", "secret disciplines"),
    ]

    for pattern, replacement in magic_patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    # 6. SENTENCE STRUCTURE VARIATION - More thorough pattern breaking
    # Fix repetitive "She [verb]. She [verb]. She [verb]." patterns
    def vary_sentence_structure(text):
        # Pattern 1: Three consecutive "She verb" sentences
        pattern1 = r"(She \w+[^.]*\.) (She \w+[^.]*\.) (She \w+[^.]*\.)"

        def restructure_three(match):
            sent1, sent2, sent3 = match.groups()
            # Vary the middle sentence structure
            sent2_new = re.sub(r"She (\w+)", r"Her action \1ed", sent2)
            if sent2_new == sent2:
                sent2_new = re.sub(r"She (\w+)", r"The movement \1ed her", sent2)
            return f"{sent1} {sent2_new}. {sent3}"

        text = re.sub(pattern1, restructure_three, text)

        # Pattern 2: Break up "The [noun] was [adj]" repetition
        pattern2 = r"(The \w+ was \w+\.) (The \w+ was \w+\.)"

        def vary_the_was(match):
            sent1, sent2 = match.groups()
            sent2_new = re.sub(r"The (\w+) was (\w+)", r"\1 \2", sent2)
            return f"{sent1} {sent2_new}."

        text = re.sub(pattern2, vary_the_was, text)

        return text

    content = vary_sentence_structure(content)

    # 7. DENSE EXPOSITION - Convert to sensory details
    exposition_patterns = [
        (
            r"The northern shipyards at Varrick have fallen",
            "The smoke from Varrick's shipyards was visible even from here—black pillars marking another Imperial loss",
        ),
        (
            r"The political situation was deteriorating",
            "The tension in the court was thick enough to taste, whispered conversations dying when she passed",
        ),
        (
            r"The war was escalating",
            "The sound of forges never stopped now, day and night, feeding the endless hunger for steel",
        ),
        (r"The military situation", "The reports that arrived with each dawn"),
        (r"The strategic implications", "The weight of what this meant"),
    ]

    for pattern, replacement in exposition_patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    # 8. ABSTRACT THREATS - Make concrete
    threat_patterns = [
        (
            r"weapons that have not been seen since the Age of Dominion",
            "the Void Bells—weapons that drove three entire legions mad the last time they were rung",
        ),
        (r"\bancient powers\b", "powers that turned the last wielder's bones to glass"),
        (
            r"\bforbidden knowledge\b",
            "knowledge that carved the Whispering Scars into the earth itself",
        ),
        (
            r"\bterrible consequences\b",
            "consequences that still echo in the Blighted Reaches",
        ),
        (r"\bawesome power\b", "power that left the Sundered Peaks as glass"),
        (r"\bdark magic\b", "magic that still screams in the wind at Ashfall"),
    ]

    for pattern, replacement in threat_patterns:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    # 9. POWER PROGRESSION CLARITY - Add context
    combat_context = [
        (
            r"\btwelve hunters\b",
            "twelve hunters—odds that would have been trivial at full strength",
        ),
        (
            r"The hunters cornered",
            "The hunters, emboldened by her obvious exhaustion, cornered",
        ),
        (
            r"She moved with deadly",
            "Despite the fire in her wounded side, she moved with deadly",
        ),
        (
            r"faced the Apostate",
            "faced the Apostate, her strength finally restored after days of recovery,",
        ),
    ]

    for pattern, replacement in combat_context:
        content = re.sub(
            pattern, replacement, content, count=1
        )  # Only first occurrence

    # 10. VARIED INTERNAL STATES - Break monotonous thought patterns
    thought_variations = [
        (
            r"Her mind analyzed",
            "Instinct screamed danger before her mind could analyze",
        ),
        (r"She calculated the", "Dread settled in her stomach as she calculated the"),
        (
            r"The strategic implications",
            "A chill of recognition preceded her analysis of the strategic implications",
        ),
        (
            r"Her tactical assessment",
            "Fury clouded her judgment for a moment before her tactical assessment",
        ),
    ]

    for pattern, replacement in thought_variations:
        content = re.sub(
            pattern, replacement, content, count=1
        )  # Add variety, not replace all

    # Clean up formatting
    content = re.sub(r"\n\n\n+", "\n\n", content)
    content = re.sub(r"  +", " ", content)

    print("Writing comprehensively improved book...")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Comprehensive improvements complete! Output written to {output_file}")


if __name__ == "__main__":
    input_file = "/home/jleechan/projects/worldarchitect.ai/world/celestial_wars_alexiel_book_timeline_enhanced.md"
    output_file = "/home/jleechan/projects/worldarchitect.ai/world/celestial_wars_alexiel_book_final_comprehensive.md"

    if os.path.exists(input_file):
        apply_comprehensive_improvements(input_file, output_file)
    else:
        print(f"Error: Input file {input_file} not found!")
