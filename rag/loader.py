import os
import logging
from pathlib import Path
from typing import List
from llama_index.core import SimpleDirectoryReader, Document


def load_documents(path: str = "data/docs") -> List[Document]:
    """
    Load documents from directory. Creates directory if missing and provides guidance.
    
    Args:
        path: Directory path containing documents (PDF, TXT, DOCX, MD supported)
    
    Returns:
        List of loaded Document objects
    """
    doc_path = Path(path)
    
    # Create directory if it doesn't exist
    if not doc_path.exists():
        print(f"📁 Creating directory: {path}")
        doc_path.mkdir(parents=True, exist_ok=True)
        print("✅ Directory created! Add documents (PDF, TXT, DOCX, MD) to continue.")
        print("💡 Example: Place sample.pdf in data/docs/")
        return []
    
    # Check if directory has files
    if not any(doc_path.rglob("*")):
        print(f"⚠️  Directory '{path}' is empty. Add documents to load.")
        return []
    
    try:
        print(f"📚 Loading documents from: {path}")
        reader = SimpleDirectoryReader(
            input_dir=path, 
            recursive=True,  # Load from subdirectories too
            exclude_hidden=True  # Skip .git, __pycache__, etc.
        )
        documents = reader.load_data()
        print(f"✅ Loaded {len(documents)} document(s)")
        return documents
        
    except Exception as e:
        print(f"❌ Error loading documents: {str(e)}")
        print("💡 Verify file formats: PDF, TXT, DOCX, MD, HTML")
        return []
