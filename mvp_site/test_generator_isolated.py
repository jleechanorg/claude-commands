import unittest
import os
from flask import Flask, request, send_file, jsonify

# We ONLY import the document_generator, which has no cloud dependencies.
import document_generator

# --- A self-contained Flask App for testing ONLY ---
app = Flask(__name__)

# Mock data to simulate what would come from Firestore
MOCK_STORY_CONTEXT = [{'actor': 'gemini', 'text': 'The test begins.'}]
MOCK_CAMPAIGN_DATA = {'title': 'PDF Test Campaign'}

# A fake endpoint that mimics the real one, but without any database calls.
@app.route('/test_export', methods=['GET'])
def test_export():
    file_format = request.args.get('format', 'pdf').lower()
    
    campaign_title = MOCK_CAMPAIGN_DATA.get('title')
    story_text = document_generator.get_story_text_from_context(MOCK_STORY_CONTEXT)
    
    file_path = None
    try:
        if file_format == 'pdf':
            # This is the line we are truly testing
            import tempfile
            file_path = tempfile.mktemp(suffix='.pdf')
            document_generator.generate_pdf(story_text, file_path, campaign_title)
            return send_file(file_path, as_attachment=True, mimetype='application/pdf', download_name='test_campaign.pdf')
        else:
            return jsonify({'error': 'This test only supports PDF format.'}), 400
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

# --- Test Class ---
class TestPdfGeneration(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_pdf_generation_and_export(self):
        """
        Tests if a PDF can be generated and returned from the test Flask route.
        This test WILL FAIL if 'assets/DejaVuSans.ttf' is missing.
        """
        print("\\n--- Running PDF Generation Test ---")
        
        # Prerequisite check - look for font relative to this test file
        test_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(test_dir, 'assets', 'DejaVuSans.ttf')
        self.assertTrue(os.path.exists(font_path), f"Font file not found at {font_path}. Please run the curl command to download it.")

        # Call our simple test endpoint
        response = self.client.get('/test_export?format=pdf')

        # Assert that the response is successful and is a PDF
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertTrue(len(response.data) > 100)
        self.assertTrue(response.data.startswith(b'%PDF-'))

        print("--- PDF Generation Test Finished Successfully ---")

if __name__ == '__main__':
    unittest.main()
