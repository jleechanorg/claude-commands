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
    # Create story text manually (since get_story_text_from_context doesn't exist)
    story_text = "Story:\nThe test begins."
    
    file_path = None
    try:
        if file_format == 'pdf':
            # Create output file path
            import tempfile
            import uuid
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.pdf")
            
            # This is the line we are truly testing
            document_generator.generate_pdf(story_text, file_path, campaign_title)
            return send_file(file_path, as_attachment=True, mimetype='application/pdf')
        else:
            return jsonify({'error': 'This test only supports PDF format.'}), 400
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            # Also clean up temp directory
            import tempfile
            temp_dir = os.path.dirname(file_path)
            if temp_dir and os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except OSError:
                    pass  # Directory may not be empty

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
        
        # Prerequisite check
        font_path = 'assets/DejaVuSans.ttf'
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
