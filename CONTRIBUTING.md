# Contributing Guidelines

Thank you for your interest in contributing!

## Development Workflow
1. Fork and clone the repository.
2. Create an isolated virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run tests:
   ```bash
   python -m unittest discover -s tests -v
   ```
5. Submit a descriptive Pull Request.
