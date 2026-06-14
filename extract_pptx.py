import zipfile
import xml.etree.ElementTree as ET
import re

def extract_pptx_text(pptx_path):
    # PPTX is a zip file. We open it and read the slide XMLs.
    try:
        archive = zipfile.ZipFile(pptx_path, 'r')
    except Exception as e:
        print(f"Error opening file: {e}")
        return

    # Find and sort slide files
    slide_files = [f for f in archive.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
    slide_files.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

    # Namespaces
    namespaces = {
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'
    }

    print(f"Found {len(slide_files)} slides in the presentation.\n")

    for slide_file in slide_files:
        slide_num = re.search(r'slide(\d+)\.xml', slide_file).group(1)
        print(f"=== SLIDE {slide_num} ===")
        xml_content = archive.read(slide_file)
        root = ET.fromstring(xml_content)
        
        # Find all text elements
        texts = []
        for elem in root.iter():
            if elem.tag.endswith('}t'): # matches {http://schemas.openxmlformats.org/drawingml/2006/main}t
                if elem.text:
                    texts.append(elem.text.strip())
        
        # Group adjacent texts or print them
        # Let's join and print
        print("\n".join([t for t in texts if t]))
        print("\n" + "="*40 + "\n")

if __name__ == '__main__':
    extract_pptx_text('/Users/aryanmahajan/Downloads/MedCare_AI_Hackathon.pptx')
