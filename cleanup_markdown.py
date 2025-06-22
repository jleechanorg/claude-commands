import os
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_core_content(text, filename):
    """Extracts the main article text, discarding website chrome."""
    
    # Define start markers for portrait and growth pages
    start_marker_portrait = "Detailed description of"
    start_marker_growth = "What does Success mean to"
    
    # Define a common end marker
    end_marker = r"(\\n\*Read about the|\\nTen rules to live by|\\nMore resources)"

    text_after_start = ""
    
    if "_portrait" in filename:
        start_pos = text.find(start_marker_portrait)
        if start_pos != -1:
            text_after_start = text[start_pos + len(start_marker_portrait):]
    elif "_growth" in filename:
        start_pos = text.find(start_marker_growth)
        if start_pos != -1:
            text_after_start = text[start_pos:] # Keep the start marker for growth pages
            
    if not text_after_start:
        logging.warning(f"Could not find start marker in {filename}. Using full file.")
        text_after_start = text

    # Find the end position using regex
    end_match = re.search(end_marker, text_after_start, re.IGNORECASE)
    if end_match:
        core_text = text_after_start[:end_match.start()]
    else:
        logging.warning(f"Could not find end marker in {filename}. Using text after start marker.")
        core_text = text_after_start
        
    return core_text.strip()

def format_text(text):
    """Formats the extracted text into clean markdown."""
    
    # Replace the literal '\\n' with actual newlines
    text = text.replace('\\n', '\\n')
    
    # Add a space after headings that run into the first sentence.
    text = re.sub(r'(#+.*?)(\\w)', r'\\1 \\2', text)
    
    # Consolidate multiple newlines into a max of two (for a blank line)
    text = re.sub(r'\\n{3,}', '\\n\\n', text)
    
    # Remove leading/trailing whitespace from the whole text
    return text.strip()

def cleanup_file(filepath):
    """Reads, cleans, and overwrites a single markdown file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_content = f.read()

        filename = os.path.basename(filepath)
        core_content = get_core_content(raw_content, filename)
        formatted_content = format_text(core_content)

        # Add a title based on the filename
        type_name = filename.split('_')[0]
        page_type = filename.split('_')[1].replace('.md', '').title()
        title = f"### {page_type} for an {type_name}\\n\\n"

        final_content = title + formatted_content

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_content)
        logging.info(f"Cleaned up: {filepath}")

    except Exception as e:
        logging.error(f"Could not process file {filepath}: {e}", exc_info=True)


def main():
    """Main function to clean up all markdown files in the directory."""
    target_dir = os.path.join('mvp_site', 'prompts', 'personalities')
    if not os.path.exists(target_dir):
        logging.error(f"Target directory not found: {target_dir}")
        return

    for filename in sorted(os.listdir(target_dir)):
        if filename.endswith('.md'):
            filepath = os.path.join(target_dir, filename)
            cleanup_file(filepath)
    
    logging.info("All markdown files have been cleaned.")

if __name__ == "__main__":
    main() 