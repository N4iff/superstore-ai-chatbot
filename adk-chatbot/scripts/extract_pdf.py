"""
PDF Text Extractor for SDAIA AI Principles
Extracts text from PDF with page numbers for citation
"""
import fitz  # PyMuPDF
import json
from pathlib import Path


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text from PDF with page numbers
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dicts with page number and text
    """
    doc = fitz.open(pdf_path)
    extracted_pages = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        
        # Clean the text
        text = text.strip()
        
        if text:  # Only add pages with content
            extracted_pages.append({
                "page": page_num + 1,  # 1-indexed for citations
                "text": text
            })
    
    doc.close()
    return extracted_pages


def chunk_text(pages: list[dict], chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """
    Split pages into chunks with overlap for better context
    
    Args:
        pages: List of page dicts
        chunk_size: Target chunk size in words
        overlap: Number of words to overlap between chunks
        
    Returns:
        List of chunks with page numbers and text
    """
    chunks = []
    chunk_id = 0
    
    for page_data in pages:
        page_num = page_data["page"]
        text = page_data["text"]
        words = text.split()
        
        # Split into chunks
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunks.append({
                "id": f"chunk_{chunk_id}",
                "page": page_num,
                "text": chunk_text,
                "word_count": len(chunk_words)
            })
            chunk_id += 1
    
    return chunks


def save_chunks_to_json(chunks: list[dict], output_path: str):
    """Save chunks to JSON file for inspection"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(chunks)} chunks to {output_path}")


if __name__ == "__main__":
    # Paths
    pdf_path = "data/ai-principles.pdf"
    output_path = "data/sdaia_chunks.json"
    
    print("📄 Extracting text from PDF...")
    pages = extract_text_from_pdf(pdf_path)
    print(f"✅ Extracted text from {len(pages)} pages")
    
    print("\n✂️ Chunking text...")
    chunks = chunk_text(pages, chunk_size=500, overlap=50)
    print(f"✅ Created {len(chunks)} chunks")
    
    print("\n💾 Saving chunks to JSON...")
    save_chunks_to_json(chunks, output_path)
    
    # Show sample
    print("\n📋 Sample chunk:")
    print(f"Page: {chunks[0]['page']}")
    print(f"Text preview: {chunks[0]['text'][:200]}...")