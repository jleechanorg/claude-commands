import os
from fpdf import FPDF, XPos, YPos
from docx import Document

def get_story_text_from_context(story_context):
    """[Summary of what get_story_text_from_context does]

    [More detailed explanation if needed]

    Args:
        story_context (list): Description of story_context. 
                              Example: [{'actor': str, 'text': str, 'mode': Optional[str]}]

    Returns:
        str: Description of the return value.
    """
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
    """[Summary of what generate_pdf does]

    [More detailed explanation if needed]

    Args:
        story_text (str): Description of story_text.
        campaign_title (str): Description of campaign_title.

    Returns:
        str: Description of the return value (e.g., file path of the generated PDF).
    """
    pdf = FPDF()
    pdf.add_page()
    
    font_family = 'Helvetica' # Default fallback font
    try:
        # Assumes 'assets/DejaVuSans.ttf' exists.
        pdf.add_font('DejaVu', '', 'assets/DejaVuSans.ttf')
        font_family = 'DejaVu'
    except RuntimeError:
        print("WARNING: DejaVuSans.ttf not found. Falling back to core font.")

    # --- CORRECTED TITLE HANDLING ---
    # Set the font family, then style, then size
    pdf.set_font(font_family, style='U', size=16) # 'U' for underline instead of 'B' for bold
    encoded_title = campaign_title.encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 10, text=encoded_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(5)

    # --- CORRECTED BODY HANDLING ---
    # Set the font for the body (regular style)
    pdf.set_font(font_family, style='', size=12)
    for paragraph in story_text.split('\\n\\n'):
        encoded_paragraph = paragraph.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, text=encoded_paragraph, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

    file_path = f"{campaign_title.replace(' ', '_')}.pdf"
    pdf.output(file_path)
    return file_path

def generate_docx(story_text, campaign_title):
    """[Summary of what generate_docx does]

    [More detailed explanation if needed]

    Args:
        story_text (str): Description of story_text.
        campaign_title (str): Description of campaign_title.

    Returns:
        str: Description of the return value (e.g., file path of the generated DOCX).
    """
    document = Document()
    document.add_heading(campaign_title, level=1)
    for paragraph in story_text.split('\\n\\n'):
        document.add_paragraph(paragraph)
    file_path = f"{campaign_title.replace(' ', '_')}.docx"
    document.save(file_path)
    return file_path
