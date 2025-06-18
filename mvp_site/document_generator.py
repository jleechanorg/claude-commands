import os
from fpdf import FPDF
from docx import Document

def get_story_text_from_context(story_context):
    """Extracts and formats story text from the context array."""
    story_parts = []
    for entry in story_context:
        actor = entry.get('actor', 'Unknown')
        text = entry.get('text', '')
        mode = entry.get('mode')

        if actor == 'gemini':
            label = 'Story'
        else: # user
            label = 'God' if mode == 'god' else 'Main Character'
        
        story_parts.append(f"{label}:\\n{text}")
    
    return "\\n\\n".join(story_parts)

def generate_pdf(story_text, campaign_title):
    """Generates a PDF file from story text and returns its path."""
    pdf = FPDF()
    pdf.add_page()
    
    # Set title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt=campaign_title, ln=True, align='C')
    pdf.ln(10) # Add a little space after the title

    # Set font for the body and add content
    pdf.set_font("Arial", size=12)
    # The 'multi_cell' handles word wrapping automatically.
    # We split by our double newline to preserve paragraph breaks.
    for paragraph in story_text.split('\\n\\n'):
        pdf.multi_cell(0, 5, txt=paragraph)
        pdf.ln(5) # Add a space between paragraphs

    # In a real cloud environment, you'd use a temporary directory like /tmp
    # For now, we'll create it in the local directory.
    file_path = f"{campaign_title.replace(' ', '_')}.pdf"
    pdf.output(file_path)
    return file_path

def generate_docx(story_text, campaign_title):
    """Generates a DOCX file from story text and returns its path."""
    document = Document()
    
    # Add title
    document.add_heading(campaign_title, level=1)

    # Add story content paragraph by paragraph
    for paragraph in story_text.split('\\n\\n'):
        document.add_paragraph(paragraph)
        
    # Define a temporary file path
    file_path = f"{campaign_title.replace(' ', '_')}.docx"
    document.save(file_path)
    return file_path
