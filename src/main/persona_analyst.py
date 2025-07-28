
import os
import json
import sys
import re
import pdfplumber
import spacy
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime

try:
    from outline_extractor import extract_outline_with_pdfplumber
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from outline_extractor import extract_outline_with_pdfplumber


try:
    nlp = spacy.load("en_core_web_md")
    print("spaCy model 'en_core_web_md' loaded successfully.")
except OSError:
    print("spaCy model 'en_core_web_md' not found. Please ensure it's downloaded locally.", file=sys.stderr)
    sys.exit(1)

def get_text_content_for_section(pdf_path, page_number, section_title, next_section_page_number=None, next_section_title=None):
    text_content_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_number > len(pdf.pages):
                return ""

            for current_p_idx in range(page_number - 1, len(pdf.pages)):
                page = pdf.pages[current_p_idx]
                lines = page.extract_text_lines(layout=True, strip=True)
                
                found_title = False
                for line_data in lines:
                    cleaned_line_text = line_data['text'].strip()
                    
                    if not found_title:
                        if section_title in cleaned_line_text:
                            found_title = True
                            text_content_parts.append(cleaned_line_text)
                            continue
                        else:
                            continue

                    if next_section_page_number and next_section_title:
                        if current_p_idx == (next_section_page_number - 1):
                            if next_section_title in cleaned_line_text:
                                break
                    
                    text_content_parts.append(cleaned_line_text)

                if next_section_page_number and current_p_idx >= (next_section_page_number - 1):
                    break


    except Exception as e:
        print(f"Error extracting content for section '{section_title}' from '{pdf_path}': {e}", file=sys.stderr)

    full_text = " ".join(text_content_parts)
    return re.sub(r'\s+', ' ', full_text).strip()


def analyze_document_collection(pdf_file_paths, persona_definition, job_to_be_done):
    all_extracted_sections = []
    metadata = {
        "input_documents": [os.path.basename(f) for f in pdf_file_paths],
        "persona": persona_definition,
        "job_to_be_done": job_to_be_done,
        "processing_timestamp": datetime.now().isoformat()
    }

    for pdf_file_path in pdf_file_paths:
        print(f"Extracting outline for {os.path.basename(pdf_file_path)}...")
        outline_result = extract_outline_with_pdfplumber(pdf_file_path)

        section_boundaries = []
        for i, entry in enumerate(outline_result['outline']):
            section_boundaries.append({
                "title": entry['text'],
                "page": entry['page'],
                "doc_path": pdf_file_path,
                "next_title": outline_result['outline'][i+1]['text'] if i+1 < len(outline_result['outline']) else None,
                "next_page": outline_result['outline'][i+1]['page'] if i+1 < len(outline_result['outline']) else None
            })

        for section_info in section_boundaries:
            section_content = get_text_content_for_section(
                section_info['doc_path'],
                section_info['page'],
                section_info['title'],
                section_info['next_page'],
                section_info['next_title']
            )
            
            all_extracted_sections.append({
                "document": os.path.basename(section_info['doc_path']),
                "page_number": section_info['page'],
                "section_title": section_info['title'],
                "full_text_content": section_content,
                "importance_rank": 0
            })

    if not all_extracted_sections:
        return {"metadata": metadata, "extracted_sections": [], "sub_section_analysis": []}

    query_text = f"Persona: {persona_definition}. Job: {job_to_be_done}"
    query_doc = nlp(query_text)

    section_texts = [sec["full_text_content"] for sec in all_extracted_sections]

    corpus = section_texts + [query_text]

    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(corpus)

    query_vector = tfidf_matrix[-1]
    section_vectors = tfidf_matrix[:-1]

    similarities = cosine_similarity(query_vector, section_vectors).flatten()

    ranked_sections = []
    for i, section in enumerate(all_extracted_sections):
        section["importance_rank"] = float(similarities[i])
        ranked_sections.append(section)

    ranked_sections.sort(key=lambda x: x["importance_rank"], reverse=True)

    sub_section_analysis = []
    top_n_sections_for_sub_analysis = 5

    query_keywords = [token.lemma_ for token in query_doc if token.is_alpha and not token.is_stop and not token.is_punct]
    
    for i, section in enumerate(ranked_sections):
        if i >= top_n_sections_for_sub_analysis:
            break

        if not section["full_text_content"]:
            continue

        doc = nlp(section["full_text_content"])
        relevant_sentences = []
        
        for sent in doc.sents:
            sent_keywords = [token.lemma_ for token in sent if token.is_alpha and not token.is_stop and not token.is_punct]

            intersection = len(set(query_keywords) & set(sent_keywords))
            union = len(set(query_keywords) | set(sent_keywords))

            if union > 0:
                jaccard_similarity = intersection / union
                if jaccard_similarity > 0.05:
                    relevant_sentences.append(sent.text.strip())

            current_refined_text_length = sum(len(s) for s in relevant_sentences)
            if current_refined_text_length > 1000:
                break

        if relevant_sentences:
            sub_section_analysis.append({
                "document": section["document"],
                "page_number": section["page_number"],
                "refined_text": " ".join(relevant_sentences)
            })

    final_extracted_sections = [{k: v for k, v in sec.items() if k != 'full_text_content'} for sec in ranked_sections]

    return {
        "metadata": metadata,
        "extracted_sections": final_extracted_sections,
        "sub_section_analysis": sub_section_analysis
    }

if __name__ == "__main__":

    if len(sys.argv) < 5:
        print("Usage: python src/persona_analyst.py <comma_separated_pdf_paths> <persona_definition_str> <job_to_be_done_str> <output_json_path>")
        print("Example: python src/persona_analyst.py \"input_data/scenario1/doc1.pdf,input_data/scenario1/doc2.pdf\" \"PhD Researcher\" \"Comprehensive literature review\" output_results/scenario1_output.json")
        sys.exit(1)

    pdf_paths_str = sys.argv[1]
    persona_def = sys.argv[2]
    job_def = sys.argv[3]
    output_json_path = sys.argv[4]

    pdf_files = [p.strip() for p in pdf_paths_str.split(',') if p.strip()]
    if not pdf_files:
        print("Error: No PDF file paths provided.", file=sys.stderr)
        sys.exit(1)

    for p_file in pdf_files:
        if not os.path.exists(p_file):
            print(f"Error: PDF file not found at '{p_file}'. Please check path.", file=sys.stderr)
            sys.exit(1)

    output_dir = os.path.dirname(output_json_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Starting analysis for scenario:")
    print(f"  PDFs: {[os.path.basename(f) for f in pdf_files]}")
    print(f"  Persona: '{persona_def}'")
    print(f"  Job: '{job_def}'")

    result = analyze_document_collection(pdf_files, persona_def, job_def)

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    print(f"Analysis complete. Output saved to '{output_json_path}'")