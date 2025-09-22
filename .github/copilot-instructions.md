# Copilot Instructions for `ai_search_web`

## Project Overview
`ai_search_web` is a Python-based project aimed at building scalable search systems. The project includes components for data processing, search algorithms, and web scraping. It is structured to support modular development and experimentation.

## Codebase Structure
- **`projects/`**: Contains the main project files.
  - `config.py`: Placeholder for configuration settings.
  - `crawler.py`: Placeholder for web crawling logic.
  - `docs/`: Reserved for documentation.
- **`requirements.txt`**: Lists Python dependencies.
- **`assignments/` and `notes/`**: Likely used for auxiliary or academic purposes.

## Key Dependencies
- **Core Libraries**: `numpy`, `pandas`, `scikit-learn`
- **Search-Specific**: `whoosh`, `rank-bm25`
- **Web Scraping**: `beautifulsoup4`, `requests`
- **Natural Language Processing**: `nltk`
- **Notebooks**: `jupyter`

## Development Workflows
### Setting Up the Environment
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Project
- Currently, the main project files (`config.py` and `crawler.py`) are placeholders. Implement the logic before running.

### Testing
- No explicit test framework is set up. Add tests as needed using `unittest` or `pytest`.

## Conventions and Patterns
- **Configuration**: Use `config.py` for global settings.
- **Crawler**: Implement web scraping logic in `crawler.py`.
- **Dependencies**: Keep `requirements.txt` updated when adding new libraries.

## Integration Points
- **Search Algorithms**: Use `whoosh` and `rank-bm25` for implementing search functionality.
- **Web Scraping**: Use `beautifulsoup4` and `requests` for crawling and parsing web data.

## Notes
- The project is in its early stages. Focus on setting up modular and reusable components.
- Document any new modules or workflows in the `docs/` directory.