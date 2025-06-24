import unittest
import os
import sys
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Add the project root to the Python path to resolve imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import firestore_service

# Check for Firebase credentials and testing environment
FIREBASE_AVAILABLE = False
SKIP_REASON = None

try:
    # Check if we're in testing mode and should skip live tests
    if os.environ.get('TESTING') == 'true':
        SKIP_REASON = "Live Firebase tests skipped in TESTING=true environment"
    elif not os.path.exists("serviceAccountKey.json"):
        SKIP_REASON = "serviceAccountKey.json not found - live Firebase tests require credentials"
    else:
        if not firebase_admin._apps:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        FIREBASE_AVAILABLE = True
        print("--- Firebase Admin Initialized Successfully for Live Test ---")
except Exception as e:
    SKIP_REASON = f"Firebase initialization failed: {e}"

if SKIP_REASON:
    print(f"--- Skipping Live Firebase Tests: {SKIP_REASON} ---")

class TestLiveFirestoreFetching(unittest.TestCase):
    
    def setUp(self):
        """
        This method runs before our test. It connects to the real Firestore
        and creates temporary test data.
        """
        if not FIREBASE_AVAILABLE:
            self.skipTest(SKIP_REASON)
        self.db = firestore.client()
        self.user_id = "test_suite_user"
        self.campaign_id = "live_integration_test_campaign"
        
        print(f"\\n--- (setUp) Creating test data in campaign: {self.campaign_id} ---")
        
        self.campaign_ref = self.db.collection('users').document(self.user_id).collection('campaigns').document(self.campaign_id)
        
        # --- THIS IS THE FIX ---
        # Actually create the parent campaign document. This was missing before.
        self.campaign_ref.set({
            'title': 'Live Test Campaign',
            'created_at': datetime.datetime.now(datetime.timezone.utc),
            'last_played': datetime.datetime.now(datetime.timezone.utc)
        })
        
        story_ref = self.campaign_ref.collection('story')
        
        story_ref.document("old_doc_1").set({
            'actor': 'gemini', 'text': 'Old data, entry 1', 
            'timestamp': datetime.datetime(2023, 1, 1, 10, 0, 0)
        })
        story_ref.document("new_doc_1").set({
            'actor': 'user', 'text': 'New data, entry 2', 
            'timestamp': datetime.datetime(2023, 1, 1, 11, 0, 0), 'part': 1
        })
        chunk_ts = datetime.datetime(2023, 1, 1, 12, 0, 0)
        story_ref.document("new_doc_2_part_1").set({
            'actor': 'gemini', 'text': 'New data, entry 3, part 1', 'timestamp': chunk_ts, 'part': 1
        })
        story_ref.document("new_doc_2_part_2").set({
            'actor': 'gemini', 'text': 'New data, entry 3, part 2', 'timestamp': chunk_ts, 'part': 2
        })
        print("--- (setUp) Test data created. ---")

    def tearDown(self):
        """
        This method runs after our test. It cleans up all the data created
        during the test to keep the database clean.
        """
        print("\\n--- (tearDown) Cleaning up test data... ---")
        
        story_docs = self.campaign_ref.collection('story').stream()
        for doc in story_docs:
            doc.reference.delete()
            
        self.campaign_ref.delete()
        print("--- (tearDown) Cleanup complete. ---")

    @unittest.skipIf(not FIREBASE_AVAILABLE, SKIP_REASON)
    def test_get_campaign_by_id_with_mixed_data(self):
        """
        Calls the REAL firestore_service function and verifies it can
        fetch and correctly merge both old and new data types.
        """
        print("\\n--- Running Test: test_get_campaign_by_id_with_mixed_data ---")
        
        _campaign, story = firestore_service.get_campaign_by_id(self.user_id, self.campaign_id)

        self.assertIsNotNone(story, "The returned story should not be None.")
        self.assertEqual(len(story), 4, "Should have retrieved all 4 story documents.")
        self.assertIn("Old data, entry 1", story[0]['text'])
        self.assertIn("New data, entry 2", story[1]['text'])
        self.assertIn("New data, entry 3, part 1", story[2]['text'])
        self.assertIn("New data, entry 3, part 2", story[3]['text'])

        print("--- Test Finished Successfully ---")

    @unittest.skipIf(not FIREBASE_AVAILABLE, SKIP_REASON)
    def test_sequence_id_generation_and_sorting(self):
        """
        Calls the REAL firestore_service function and verifies that sequence IDs
        are generated correctly after sorting.
        """
        print("\\n--- Running Test: test_sequence_id_generation_and_sorting ---")
        
        # Initial state check
        _campaign, story = firestore_service.get_campaign_by_id(self.user_id, self.campaign_id)
        self.assertIsNotNone(story)
        initial_count = len(story)
        self.assertEqual(story[-1].get('sequence_id'), initial_count, "Initial sequence IDs should be correct.")

        # Turn 1
        print("--- Adding Turn 1 ---")
        firestore_service.add_story_entry(self.user_id, self.campaign_id, 'user', 'First new entry.')
        _campaign, story = firestore_service.get_campaign_by_id(self.user_id, self.campaign_id)
        self.assertIsNotNone(story)
        self.assertEqual(len(story), initial_count + 1)
        self.assertEqual(story[-1].get('sequence_id'), initial_count + 1, "Sequence ID should increment after Turn 1.")
        self.assertIn("First new entry", story[-1]['text'])

        # Turn 2
        print("--- Adding Turn 2 ---")
        firestore_service.add_story_entry(self.user_id, self.campaign_id, 'gemini', 'Second new entry.')
        _campaign, story = firestore_service.get_campaign_by_id(self.user_id, self.campaign_id)
        self.assertIsNotNone(story)
        self.assertEqual(len(story), initial_count + 2)
        self.assertEqual(story[-1].get('sequence_id'), initial_count + 2, "Sequence ID should increment after Turn 2.")

        # Turn 3
        print("--- Adding Turn 3 ---")
        firestore_service.add_story_entry(self.user_id, self.campaign_id, 'user', 'Third new entry.')
        _campaign, story = firestore_service.get_campaign_by_id(self.user_id, self.campaign_id)
        self.assertIsNotNone(story)
        self.assertEqual(len(story), initial_count + 3)
        self.assertEqual(story[-1].get('sequence_id'), initial_count + 3, "Sequence ID should increment after Turn 3.")

        print("--- Test Finished Successfully ---")

if __name__ == '__main__':
    unittest.main()
