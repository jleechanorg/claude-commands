import unittest
import os
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

import firestore_service

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    print("--- Firebase Admin Initialized Successfully for Live Test ---")
except Exception as e:
    print(f"--- FATAL ERROR: Could not initialize Firebase Admin. ---")
    print(f"Please ensure 'serviceAccountKey.json' is in your root directory.")
    print(f"Error details: {e}")
    exit()

class TestLiveFirestoreFetching(unittest.TestCase):
    
    def setUp(self):
        """
        This method runs before our test. It connects to the real Firestore
        and creates temporary test data.
        """
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

    def test_sequence_id_generation_and_sorting(self):
        """
        Calls the REAL firestore_service function and verifies that sequence IDs
        are generated correctly after sorting.
        """
        print("\\n--- Running Test: test_sequence_id_generation_and_sorting ---")
        
        _campaign, story = firestore_service.get_campaign_by_id(self.user_id, self.campaign_id)

        self.assertIsNotNone(story)
        
        # 1. Check if the sequence starts at 1
        self.assertEqual(story[0].get('sequence_id'), 1, "Sequence should start at 1.")
        
        # 2. Check if the last sequence ID matches the length
        self.assertEqual(story[-1].get('sequence_id'), len(story), "Last sequence ID should match total count.")

        # 3. Check if all sequence IDs are present and correctly ordered
        expected_sequence_id = 1
        for entry in story:
            self.assertIsInstance(entry.get('sequence_id'), int, "sequence_id should be an integer.")
            self.assertEqual(entry.get('sequence_id'), expected_sequence_id, "Sequence IDs should be consecutive.")
            expected_sequence_id += 1
            
        print("--- Test Finished Successfully ---")

if __name__ == '__main__':
    unittest.main()
