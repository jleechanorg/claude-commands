import sys
import unittest
from unittest.mock import MagicMock
import numpy as np

# Mock fastembed before importing mvp_site
mock_fastembed = MagicMock()
sys.modules["fastembed"] = mock_fastembed

# Now import modules
from mvp_site import constants, intent_classifier

class TestIntentClassifier(unittest.TestCase):
    def setUp(self):
        # Reset singleton
        intent_classifier.LocalIntentClassifier._instance = None

    def test_initialization(self):
        # Mock TextEmbedding inside the classifier module (it was imported from fastembed)
        # Since we mocked sys.modules['fastembed'], intent_classifier.TextEmbedding is already a Mock
        
        # We need to configure it
        mock_embedding_cls = intent_classifier.TextEmbedding
        mock_model = MagicMock()
        mock_embedding_cls.return_value = mock_model
        
        def mock_embed(texts):
            for _ in texts:
                yield np.array([0.1, 0.2, 0.3])
        
        mock_model.embed = mock_embed

        classifier = intent_classifier.LocalIntentClassifier.get_instance()
        classifier._initialize_model()

        self.assertTrue(classifier.ready)
        self.assertIsNotNone(classifier.model)
        self.assertGreater(len(classifier.anchor_embeddings), 0)

    def test_predict_think_mode(self):
        classifier = intent_classifier.LocalIntentClassifier.get_instance()
        classifier.ready = True
        
        classifier.anchor_embeddings = {
            constants.MODE_THINK: np.array([[1.0, 0.0]]),
            constants.MODE_INFO: np.array([[0.0, 1.0]]),
            constants.MODE_GOD: np.array([[0.0, 0.0]])
        }
        
        mock_model = MagicMock()
        classifier.model = mock_model

        def mock_embed(texts):
            for _ in texts:
                # Provide a unit vector to satisfy the exact score check after normalization
                yield np.array([0.9, 0.43588989435406735])  # 0.9^2 + x^2 = 1 -> x = sqrt(1-0.81) = sqrt(0.19)
        
        mock_model.embed.side_effect = mock_embed

        mode, score = classifier.predict("I need a plan")
        
        self.assertEqual(mode, constants.MODE_THINK)
        self.assertAlmostEqual(score, 0.9)

if __name__ == '__main__':
    unittest.main()