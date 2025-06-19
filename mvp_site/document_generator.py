import os
from fpdf import FPDF, XPos, YPos
from docx import Document

def get_story_text_from_context(story_context):
    """Formats a list of story context entries into a single string for document generation.

    Each story entry is prefixed with a label indicating the actor (e.g., "Story:",
    "God:", "Main Character:") based on the 'actor' and 'mode' fields in each entry.
    Entries are separated by double escaped newlines ("\\n\\n") and internal newlines
    within an entry's text are preserved with a single escaped newline ("\\n").

    Args:
        story_context (list): A list of dictionaries, where each dictionary represents
                              a turn in the story. Expected keys per dictionary:
                              'actor' (str): The source of the text (e.g., 'gemini', 'user').
                              'text' (str): The actual text content of the story turn.
                              'mode' (str, optional): The mode of interaction if the actor
                                                      is 'user' (e.g., 'god', 'character').

    Returns:
        str: A single string representing the entire story, formatted with labels
             and appropriate newline separators for use in document generation.
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
        
        story_parts.append(f"{label}:\\n{text}") # Escaped \n for potential multi-line text within an entry
    
    return "\\n\\n".join(story_parts) # Double escaped \n\n to separate distinct story entries/paragraphs

def generate_pdf(story_text, campaign_title):
    """Generates a PDF document from the provided story text and campaign title.

    The function creates a PDF with the campaign title underlined at the top,
    followed by the story content. It attempts to use the 'DejaVuSans' font
    if available in an 'assets' subdirectory, otherwise falls back to 'Helvetica'.
    The generated PDF is saved with a filename derived from the campaign title.

    Args:
        story_text (str): The full story text, where paragraphs are expected to be
                          separated by double escaped newlines ("\\n\\n") and lines
                          within paragraphs by single escaped newlines ("\\n").
        campaign_title (str): The title for the campaign, used in the PDF header
                              and for generating the output filename.

    Returns:
        str: The file path of the generated PDF document.
    """
    pdf = FPDF()
    pdf.add_page()
    
    font_family = 'Helvetica' # Default fallback font
    try:
        # Assumes 'assets/DejaVuSans.ttf' exists.
        # For robustness, ensure this path is correct relative to where the script runs,
        # or use an absolute path / path relative to this file's directory.
        pdf.add_font('DejaVu', '', 'assets/DejaVuSans.ttf') # uni=True is default for TTF in FPDF2
        font_family = 'DejaVu'
    except RuntimeError:
        # This message will be printed to the console where the Python script (e.g., Flask app) is running.
        print("WARNING: DejaVuSans.ttf not found. Falling back to core font.")

    # --- CORRECTED TITLE HANDLING --- (Comment from original code)
    # Set the font family, then style, then size
    pdf.set_font(font_family, style='U', size=16) # 'U' for underline instead of 'B' for bold
    # Encode for latin-1 if using core fonts, as they have limited character support.
    # DejaVu (TTF) should handle Unicode directly.
    encoded_title = campaign_title.encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 10, text=encoded_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(5) # Add some space after the title

    # --- CORRECTED BODY HANDLING --- (Comment from original code)
    # Set the font for the body (regular style)
    pdf.set_font(font_family, style='', size=12)
    # The input story_text uses "\\n\\n" for paragraph breaks.
    # FPDF's multi_cell interprets "\n" as a line break.
    for paragraph in story_text.split('\\n\\n'):
        # Replace escaped newlines "\\n" with actual newlines "\n" for FPDF multi_cell
        paragraph_for_pdf = paragraph.replace("\\n", "\n")
        encoded_paragraph = paragraph_for_pdf.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, text=encoded_paragraph, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3) # Add a small space after each paragraph block in the PDF

    # Generate a safe filename from the campaign title
    safe_filename_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in campaign_title).rstrip()
    safe_filename_title = safe_filename_title.replace(' ', '_')
    if not safe_filename_title: # Handle empty or purely special character titles
        safe_filename_title = "campaign_story" # Default filename
        
    file_path = f"{safe_filename_title}.pdf"
    pdf.output(file_path)
    return file_path

def generate_docx(story_text, campaign_title):
    """Generates a DOCX document from the provided story text and campaign title.

    The function creates a DOCX file with the campaign title as a level 1 heading,
    followed by the story content, where each segment separated by double
    escaped newlines ("\\n\\n") in the input text becomes a new paragraph.

    Args:
        story_text (str): The full story text, where paragraphs are expected to be
                          separated by double escaped newlines ("\\n\\n").
        campaign_title (str): The title for the campaign, used as the main heading
                              in the DOCX and for generating the output filename.

    Returns:
        str: The file path of the generated DOCX document.
    """
    document = Document()
    document.add_heading(campaign_title, level=1)
    # The input story_text uses "\\n\\n" for paragraph breaks.
    # Each part becomes a new paragraph in DOCX.
    # Replace escaped newlines "\\n" with actual newlines "\n" for proper line breaks within paragraphs.
    for paragraph_block in story_text.split('\\n\\n'):
        paragraph_for_docx = paragraph_block.replace("\\n", "\n")
        document.add_paragraph(paragraph_for_docx)
        
    # Generate a safe filename from the campaign title
    safe_filename_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in campaign_title).rstrip()
    safe_filename_title = safe_filename_title.replace(' ', '_')
    if not safe_filename_title: # Handle empty or purely special character titles
        safe_filename_title = "campaign_story" # Default filename

    file_path = f"{safe_filename_title}.docx"
    document.save(file_path)
    return file_path
