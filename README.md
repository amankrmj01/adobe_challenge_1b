# Adobe Challenge 1B: Persona-Driven Document Intelligence

## Objective
Act as an intelligent document analyst by extracting and prioritizing the most relevant sections from a collection of documents, tailored to a specific "Persona Definition" and "Job-to-be-Done."

## Methodology
Building upon the structural insights from Round 1A, Round 1B introduces a layer of semantic understanding:

1. **Document Structuring (Leveraging 1A):**
   - For each PDF in the provided collection, the outline extraction module (`outline_extractor.py`) is invoked to obtain its structural hierarchy.

2. **Section Content Extraction:**
   - The full text content for each identified heading is extracted by segmenting text blocks under each heading until the next logical section or end of page.

3. **Semantic Analysis and Relevance Ranking:**
   - **Query Formulation:** The "Persona" (role) and "Job-to-be-Done" (task) are combined into a single, semantically rich query string.
   - **Vectorization and Similarity:** Linguistic processing is performed using spaCy (lemmatization), and scikit-learn's `TfidfVectorizer` converts the query and all extracted document sections into numerical vectors. Cosine similarity is calculated between the query vector and each section's vector to determine relevance scores.
   - **Global Ranking:** All sections across the document collection are ranked by similarity scores to identify the most pertinent information.

4. **Sub-Section Analysis (Refined Text):**
   - For the top-ranked sections, a deeper analysis extracts the most relevant sentences, using keyword overlap and sentence-level similarity to the persona/job query.

## Key Files
- `outline_extractor.py`: Extracts document structure and headings from PDFs.
- `persona_analyst.py`: Performs semantic analysis and relevance ranking.
- `analyzer.py`: Orchestrates the workflow and scenario processing.
- `config.py`: Configuration for input/output directories.

## Technologies Used
- Python
- spaCy (linguistic processing)
- scikit-learn (TF-IDF vectorization, cosine similarity)

## Usage
1. Place your input PDFs and scenario files in the designated input directory. The input directory should contain subfolders for each scenario. Each scenario folder must include:
   - One or more PDF files to be analyzed.
   - `persona.txt`: Contains the persona definition (role).
   - `job.txt`: Contains the job-to-be-done (task).
2. Build the Docker image:
   ```sh
   docker build -t amankrmj01/adobe-1b .
   ```
3. Run the Docker container, mounting your input and output directories:
   ```sh
   docker run --rm -v D:\dev_mode\test\input_1b:/data/input_1b:ro -v D:\dev_mode\test\output_1b:/data/output_1b --network none amankrmj01/adobe-1b
   ```
   - Replace `D:\dev_mode\test\input_1b` with the path to your input folder containing scenario subfolders and files.
   - Replace `D:\dev_mode\test\output_1b` with the path to your desired output folder.

## Docker
A Dockerfile is provided to simplify setup and execution:
- Uses a Python base image.
- Installs all required dependencies from `requirements.txt`.
- Copies source files and sets up the entrypoint to run `main.py`.

This allows you to run the solution in a consistent environment without manual Python setup.

## Scenario Example
- **Persona:** Travel Planner
- **Job-to-be-Done:** Find the best travel options for a client.

The system will rank and extract the most relevant sections and sentences from the provided documents for this scenario.
