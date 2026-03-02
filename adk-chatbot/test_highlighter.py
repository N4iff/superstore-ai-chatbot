# #!/usr/bin/env python3
# """
# Real PDF Highlighter - Searches for and highlights actual text
# """
# import fitz  # PyMuPDF
# from datetime import datetime

# def highlight_specific_text():
#     """
#     Test: Highlight specific Arabic text on page 17
#     This simulates what happens when RAG retrieves text
#     """
    
#     print("🧪 Testing Text-Based Highlighting...")
    
#     # Example: Text that RAG would retrieve from page 17
#     # This is what the compliance agent actually gets from ChromaDB
#     text_to_find = "تهيئة البيانات عند جمع أو شراء أو إدارة أو تنظيم البيانات"
#     page_num = 17
    
#     print(f"📄 Searching for text on page {page_num}...")
#     print(f"🔍 Text: {text_to_find[:50]}...")
    
#     # Open PDF
#     pdf_path = "data/ai-principles.pdf"
#     doc = fitz.open(pdf_path)
    
#     page_index = page_num - 1
#     page = doc[page_index]
    
#     # Search for the text
#     text_instances = page.search_for(text_to_find)
    
#     if text_instances:
#         print(f"✅ Found {len(text_instances)} instance(s) of the text!")
        
#         # Highlight each instance
#         for i, inst in enumerate(text_instances, 1):
#             highlight = page.add_highlight_annot(inst)
#             highlight.set_colors(stroke=(1, 1, 0))  # Yellow
#             highlight.update()
#             print(f"  ✅ Highlighted instance {i}")
#     else:
#         print("❌ Text not found - trying shorter phrase...")
#         # Try with shorter text (first 30 characters)
#         shorter_text = text_to_find[:30]
#         text_instances = page.search_for(shorter_text)
        
#         if text_instances:
#             print(f"✅ Found with shorter phrase!")
#             for inst in text_instances:
#                 highlight = page.add_highlight_annot(inst)
#                 highlight.set_colors(stroke=(1, 1, 0))
#                 highlight.update()
#         else:
#             print("❌ Still not found - the text might not match exactly")
    
#     # Save
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     output_filename = f"sdaia_real_highlight_{timestamp}.pdf"
#     output_path = f"data/{output_filename}"
    
#     doc.save(output_path)
#     doc.close()
    
#     print(f"\n✅ SUCCESS!")
#     print(f"📥 File: {output_path}")
#     print(f"\n👀 Open this file and check page {page_num} for yellow highlighting!")
    
#     return output_path

# if __name__ == "__main__":
#     result = highlight_specific_text()