# Round 1B Approach: Persona-Driven Document Intelligence

## Objective
To act as an intelligent document analyst by extracting and prioritizing the most relevant sections from a collection of documents, tailored to a specific **"Persona Definition"** and **"Job-to-be-Done."**

## Methodology
Building upon the structural insights from Round 1A, Round 1B introduces a layer of semantic understanding:

### 1. Document Structuring (Leveraging 1A)
- For each PDF in the provided collection, the Round 1A outline extraction module (`outline_extractor.py`) is invoked to obtain its structural hierarchy.

### 2. Section Content Extraction
- Extract the full text content for each identified heading.
- Carefully segment text blocks that fall under a heading until the next logical section or the end of a page.

### 3. Semantic Analysis and Relevance Ranking
- **Query Formulation:**  
  Combine the "Persona" (role) and "Job-to-be-Done" (task) into a single, semantically rich query string.

- **Vectorization and Similarity:**  
  Use **spaCy** for efficient linguistic processing (e.g., lemmatization) and **scikit-learn's TfidfVectorizer** to convert both the query and all extracted document sections into numerical vector representations.  
  Calculate cosine similarity between the query vector and each section's vector to determine relevance scores.

- **Global Ranking:**  
  Rank all sections across the entire document collection by their similarity scores to identify the most pertinent information.

### 4. Sub-Section Analysis (Refined Text)
- For the top-ranked sections, perform a deeper dive to extract **"refined text."**  
- Identify the most relevant sentences within those sections, typically through keyword overlap and sentence-level similarity to the original persona/job query.
