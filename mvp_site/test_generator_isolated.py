import unittest
import os
from unittest.mock import patch
from flask import Flask, request, send_file, jsonify
import document_generator  # We only import the generator, which has no cloud dependencies

# --- A self-contained Flask App for testing ONLY ---
app = Flask(__name__)

# This is a fake story context for our test endpoint
MOCK_STORY_CONTEXT = [
    {'actor': 'gemini', 'text': 'The test begins.'},
    {'actor': 'user', 'text': 'I test the PDF.', 'mode': 'character'}
]
MOCK_CAMPAIGN_DATA = {'title': 'PDF Test Campaign'}

# This is a fake endpoint that mimics the real one in main.py
@app.route('/api/campaigns/<campaign_id>/export', methods=['GET'])
def export_campaign(campaign_id):
    file_format = request.args.get('format', 'txt').lower()
    
    # We use our fake data instead of calling firestore
    campaign_title = MOCK_CAMPAIGN_DATA.get('title')
    story_text = document_generator.get_story_text_from_context(MOCK_STORY_CONTEXT)
    
    file_path = None
    mimetype = 'text/plain'
    
    try:
        if file_format == 'pdf':
            # This is the line we are truly testing
            file_path = document_generator.generate_pdf(story_text, campaign_title)
            mimetype = 'application/pdf'
        else:
            return jsonify({'error': 'This test only supports PDF format.'}), 400

        return send_file(file_path, as_attachment=True, mimetype=mimetype)
    
    except Exception as e:
        print(f"ERROR IN FAKE ENDPOINT: {e}")
        return jsonify({'error': 'Failed to generate file'}), 500
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

# --- Test Class ---

class TestIsolatedPdfGeneration(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.campaign_id = "isolated-test-id"

    # We patch the font loading to avoid needing the assets folder for this test
    @patch('fpdf.FPDF.add_font')
    def test_pdf_export_from_flask_route(self, mock_add_font):
        """
        Tests if a PDF can be generated and returned from a Flask route context.
        This bypasses all firebase/gemini import issues.
        """
        print("\\n--- Running Isolated PDF Export Test ---")
        
        response = self.client.get(
            f'/api/campaigns/{self.campaign_id}/export?format=pdf'
        )

        # 1. Check for success status code
        self.assertEqual(response.status_code, 200, "Response status code should be 200 (OK)")
        
        # 2. Check that the content type is for a PDF
        self.assertEqual(response.mimetype, 'application/pdf', "Mimetype should be application/pdf")
        
        # 3. Check that the file content is not empty
        self.assertTrue(len(response.data) > 0, "PDF file should not be empty")

        print("--- Isolated PDF Test Finished Successfully ---")

if __name__ == '__main__':
    unittest.main()
