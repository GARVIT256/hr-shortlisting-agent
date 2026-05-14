import json
from pathlib import Path

def extract_text_from_pdf(file_path: str) -> str:
    try:
        import fitz
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except ImportError:
        return "PyMuPDF not installed. Cannot parse PDF."
    except Exception as e:
        return f"Error parsing PDF: {e}"

def extract_text_from_docx(file_path: str) -> str:
    try:
        import docx
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except ImportError:
        return "python-docx not installed. Cannot parse DOCX."
    except Exception as e:
        return f"Error parsing DOCX: {e}"

def extract_text_from_json(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return json.dumps(data, indent=2)

def ingest_file(file_path: str) -> str:
    try:
        path = Path(file_path)
        if path.suffix.lower() == '.pdf':
            return extract_text_from_pdf(file_path)
        elif path.suffix.lower() == '.docx':
            return extract_text_from_docx(file_path)
        elif path.suffix.lower() == '.json':
            return extract_text_from_json(file_path)
        elif path.suffix.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return f"STATUS: UNPARSEABLE - Unsupported format {path.suffix}"
    except Exception as e:
        return f"STATUS: UNPARSEABLE - {str(e)}"
