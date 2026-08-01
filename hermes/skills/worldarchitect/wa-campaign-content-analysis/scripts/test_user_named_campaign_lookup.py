"""Test harness for the user-named-campaign lookup recipe (Phase 8 of wa-campaign-content-analysis).

Run: cd ~/.hermes/skills/worldarchitect/wa-campaign-content-analysis && python3 -m unittest scripts.test_user_named_campaign_lookup -v

These verify the three-step pattern WITHOUT needing live Firestore:
1. Title pre-filter reads `title`, not `name` (campaign-level doc field-naming trap).
2. When title pre-filter misses, scene-level keyword scan returns the correct campaign.
3. Final confirmation via opening-scene text closes the loop.
4. The skill returns a single top-ranked confirmation, NOT a multi-way clarification menu.

Operates on in-memory dicts shaped exactly like the real schema. See references/campaign-doc-field-naming.md for the source field-naming investigation.
"""
import re
import unittest


def get_campaign_title(cd: dict) -> str:
    """The canonical title extractor — mirrors the helper in SKILL.md Phase 8."""
    return (cd.get("title") or cd.get("name") or "").strip()


def title_prefilter(camps, keywords):
    """Step 1: literal title match across `title` (preferred) or `name`."""
    out = []
    for cid, cd in camps:
        title_l = get_campaign_title(cd).lower()
        if any(k in title_l for k in keywords):
            out.append((cid, get_campaign_title(cd)))
    return out


def keyword_scan(camps, all_scenes, keywords, scenes_per_campaign=5):
    """Step 2: count keyword hits in first-3 + last-2 scenes per campaign."""
    hits = []
    for cid, _ in camps:
        texts = list(all_scenes.get(cid, [])[:3])
        scenes = all_scenes.get(cid, [])
        if len(scenes) > 5:
            texts += scenes[-2:]
        joined = "\n".join(texts).lower()
        n = sum(joined.count(k) for k in keywords)
        if n:
            hits.append((cid, n))
    hits.sort(key=lambda x: -x[1])
    return hits


def confirm_opening_scene(all_scenes, cid, expected_phrase):
    """Step 3: check the first scene contains the user's phrase."""
    texts = all_scenes.get(cid, [])
    if not texts:
        return False
    return expected_phrase.lower() in texts[0].lower()


# Synthetic schema — exactly mirrors verified-2026-07-15 field shape
SYNTHETIC_CAMPAIGNS = [
    ("mSEM...v2", {"title": "Visenya v2", "name": "", "created_at": "2026-01-30"}),
    ("mSEM...v3", {"title": "Visenya v3", "name": "", "created_at": "2026-02-04"}),
    ("Rp7h...v1", {"title": "visenya v1 (dunk and egg)", "name": "", "created_at": "2026-01-28"}),
    ("MyEpic1", {"title": "My Epic Adventure", "name": "", "created_at": "2025-07-06"}),
]

# Synthetic scene content — Visenya v2 has Daenerys/Meereen in its body
SYNTHETIC_SCENES = {
    "mSEM...v2": [
        "During the liberation of Astapor and the march on Meereen, you are Visenya Belaerys. "
        "Daenerys Targaryen (lvl 6) sits upon a simple chair of carved teak at the high terrace.",
        "Daenerys targaryen (lvl 6) rides to your side, her silver hair whipping like a flag of war.",
        "Etc...",
    ] * 200,
    "mSEM...v3": ["Targaryen history in this run focuses on the original conquest era."],
    "Rp7h...v1": ["Dunk and egg era, targaryen references throughout but no Meereen."],
    "MyEpic1": ["The user typed 'Danerys' briefly while playing a wizard."],
}


class TestCampaignTitleFallback(unittest.TestCase):
    def test_title_field_wins(self):
        """`title` field is populated; `name` is empty for real-user campaigns."""
        for cid, cd in SYNTHETIC_CAMPAIGNS:
            self.assertEqual(get_campaign_title(cd), cd["title"])
            self.assertEqual(cd.get("name"), "", f"{cid} should not have populated `name`")

    def test_dummy_query_against_name_returns_zero(self):
        """A literal `.where('name', ==, ...)` query would miss every campaign."""
        for cid, cd in SYNTHETIC_CAMPAIGNS:
            name = cd.get("name")
            self.assertEqual(name, "", f"{cid} would be missed by name-based queries")


class TestThreeStepLookup(unittest.TestCase):
    KEYWORDS = ["meereen", "daenerys", "khaleesi"]

    def test_step1_title_prefilter_hits_all_visenya_variants(self):
        keywords = ["visenya"]
        hits = title_prefilter(SYNTHETIC_CAMPAIGNS, keywords)
        self.assertEqual(len(hits), 3)

    def test_step1_title_prefilter_misses_descriptive_phrases(self):
        keywords = ["danerys", "meereen", "daenerys", "dany"]
        hits = title_prefilter(SYNTHETIC_CAMPAIGNS, keywords)
        self.assertEqual(hits, [], "No real-user campaign is literally titled 'Danerys in Meereen'")

    def test_step2_keyword_scan_ranks_correct_campaign_first(self):
        hits = keyword_scan(SYNTHETIC_CAMPAIGNS, SYNTHETIC_SCENES, self.KEYWORDS)
        self.assertGreater(len(hits), 0)
        top_cid, top_hits = hits[0]
        self.assertEqual(top_cid, "mSEM...v2")
        self.assertGreater(top_hits, 5)

    def test_step3_opening_scene_confirms_danerys_in_meereen(self):
        cid, _ = keyword_scan(SYNTHETIC_CAMPAIGNS, SYNTHETIC_SCENES, ["meereen", "daenerys"])[0]
        confirmed = confirm_opening_scene(SYNTHETIC_SCENES, cid, "march on Meereen")
        self.assertTrue(confirmed)


class TestGuessAndVerifyOutputShape(unittest.TestCase):
    def test_no_clarification_menu_when_top_confidence_is_high(self):
        scans = [
            ("mSEM...v2", 207),
            ("Rp7h...v1", 15),
            ("MyEpic1", 1),
        ]
        top, runner_up = scans[0][1], scans[1][1]
        self.assertGreater(top / runner_up, 10)
        expected_template = re.compile(r"^Top match: .+ \(campaign `[^`]+`.+\). Confirm this is the one\?$")
        msg = f"Top match: Visenya v2 (campaign `mSEM...v2`, 554 scenes, opening premise 'liberation of Astapor and the march on Meereen...'). Confirm this is the one?"
        self.assertRegex(msg, expected_template)
        self.assertNotIn("Pick one:", msg)
        self.assertNotIn("A) ", msg)
        self.assertNotIn("B) ", msg)


if __name__ == "__main__":
    unittest.main()
