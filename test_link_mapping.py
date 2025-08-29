#!/usr/bin/env python3
"""
Test script pentru funcționalitatea de link mapping
"""

import sys
import os

# Adaugă calea către backend în PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from backend.approaches.approach import Document, ExtraInfo, DataPoints

def test_link_mapping():
    # Simulează o listă de documente cu linkuri lungi
    documents = [
        Document(
            id="1",
            content="Aceasta este o informație despre primul document.",
            sourcepage="https://mihairagstorageaccount.blob.core.windows.net/prod-mihai-container/28406.pdf?se=2025-08-28T12%3A57%3A58Z&sp=r&sv=2024-08-04&sr=b&sig=Zh59wiAQg%2Bm272wf8M/GG9bjPtQsSxnNiyiiqnRBe5w%3D#page=1",
            sourcefile="document1.pdf"
        ),
        Document(
            id="2", 
            content="Aceasta este o informație despre al doilea document.",
            sourcepage="https://mihairagstorageaccount.blob.core.windows.net/prod-mihai-container/28407.pdf?se=2025-08-28T12%3A57%3A58Z&sp=r&sv=2024-08-04&sr=b&sig=XyZ123abc%2Bdef456ghi%3D#page=1",
            sourcefile="document2.pdf"
        ),
        Document(
            id="3",
            content="Aceasta este o informație despre al treilea document.",
            sourcepage="https://mihairagstorageaccount.blob.core.windows.net/prod-mihai-container/28408.pdf?se=2025-08-28T12%3A57%3A58Z&sp=r&sv=2024-08-04&sr=b&sig=ABC789xyz%2Buvw012stu%3D#page=2",
            sourcefile="document3.pdf"
        )
    ]
    
    # Creează o instanță minimă a clasei pentru testare
    class TestApproach:
        def create_link_mapping(self, results):
            """
            Creează un mapping între ID-uri scurte (link1, link2, etc.) și linkurile lungi reale.
            """
            link_mapping = {}
            link_counter = 1
            
            for doc in results:
                if doc.sourcepage:
                    link_id = f"link{link_counter}"
                    link_mapping[link_id] = doc.sourcepage
                    link_counter += 1
            
            return link_mapping
        
        def get_sources_content(self, results, use_semantic_captions, use_image_citation, link_mapping=None):
            def nonewlines(s):
                return s.replace("\n", " ").replace("\r", " ")

            def format_source(doc):
                # Extrage titlul și pagina din sourcefile, elimină '_' de la început dacă există
                if doc.sourcefile:
                    titlu_pagina = doc.sourcefile.lstrip('_').strip()
                else:
                    titlu_pagina = doc.sourcepage or ""
                
                original_link = doc.sourcepage or ""
                
                # Dacă avem un mapping de linkuri, folosim ID-ul scurt în loc de linkul lung
                if link_mapping and original_link:
                    link_id = None
                    for short_id, long_link in link_mapping.items():
                        if long_link == original_link:
                            link_id = short_id
                            break
                    
                    if link_id:
                        return f"[{titlu_pagina}]({link_id})"
                
                return f"[{titlu_pagina}]({original_link})"

            return [
                format_source(doc) + ": " + nonewlines(doc.content or "")
                for doc in results
            ]
    
    # Testează funcționalitatea
    approach = TestApproach()
    
    print("=== TESTARE LINK MAPPING ===")
    print()
    
    # Creează mapping-ul
    link_mapping = approach.create_link_mapping(documents)
    print("Link mapping creat:")
    for short_id, long_link in link_mapping.items():
        print(f"  {short_id} -> {long_link[:50]}...")
    print()
    
    # Testează cu mapping
    sources_with_mapping = approach.get_sources_content(
        documents, 
        use_semantic_captions=False, 
        use_image_citation=False, 
        link_mapping=link_mapping
    )
    
    print("Surse cu mapping (linkuri scurte):")
    for i, source in enumerate(sources_with_mapping, 1):
        print(f"  {i}. {source}")
    print()
    
    # Testează fără mapping (original)
    sources_without_mapping = approach.get_sources_content(
        documents, 
        use_semantic_captions=False, 
        use_image_citation=False
    )
    
    print("Surse fără mapping (linkuri lungi):")
    for i, source in enumerate(sources_without_mapping, 1):
        print(f"  {i}. {source[:100]}...")
    print()
    
    # Calculează economiile
    total_chars_with_mapping = sum(len(source) for source in sources_with_mapping)
    total_chars_without_mapping = sum(len(source) for source in sources_without_mapping)
    saved_chars = total_chars_without_mapping - total_chars_with_mapping
    saved_percentage = (saved_chars / total_chars_without_mapping) * 100
    
    print("=== REZULTATE ===")
    print(f"Caractere cu mapping: {total_chars_with_mapping}")
    print(f"Caractere fără mapping: {total_chars_without_mapping}")
    print(f"Caractere economisate: {saved_chars}")
    print(f"Procentul economisit: {saved_percentage:.1f}%")
    print()
    
    # Testează simularea în frontend
    print("=== SIMULARE FRONTEND ===")
    print("Mapping de linkuri pentru frontend:")
    for short_id, long_link in link_mapping.items():
        print(f"  '{short_id}': '{long_link}'")
    print()
    
    print("Exemplu de înlocuire în frontend:")
    example_response = "Documentul [document1.pdf](link1) conține informații importante despre [document2.pdf](link2)."
    print(f"Răspuns cu ID-uri scurte: {example_response}")
    
    # Simulează înlocuirea din frontend
    frontend_response = example_response
    for short_id, long_link in link_mapping.items():
        frontend_response = frontend_response.replace(f"({short_id})", f"({long_link})")
    
    print(f"Răspuns cu linkuri reale: {frontend_response[:100]}...")
    
    return True

if __name__ == "__main__":
    test_link_mapping()
