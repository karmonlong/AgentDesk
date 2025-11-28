# GEMINI Project Analysis: office-assistant

## Project Overview

This project is a Python-based "Office Assistant" web application. It leverages the LangGraph framework and the Kimi Large Language Model to provide intelligent document processing and chat capabilities. The backend is built with FastAPI, serving a web interface and a set of REST APIs.

The application has two main functionalities:
1.  **Document Processing:** Users can upload documents (PDF, DOCX, TXT, etc.) and perform various operations like summarization, content generation, format conversion, and data extraction. This workflow is managed by a LangGraph state machine defined in `graph/document_graph.py`.
2.  **Multi-Agent Chat:** A chat interface (`/chat` and `/command`) allows users to interact with a system of multiple AI agents. This system, defined in `agents/multi_agents.py`, routes user queries to the appropriate agent (e.g., a document analysis agent, a general knowledge agent).

The entire application is containerized within a Python environment, with dependencies managed by `pip` and `requirements.txt`.

## Building and Running

The project uses a `Makefile` to simplify common development tasks.

### 1. Installation and Configuration

-   **Installation:** To set up the project, run the following command. It will create a Python virtual environment in `./venv` and install all required dependencies from `requirements.txt`.
    ```bash
    make install
    ```
-   **Configuration:** The application requires API credentials for the Kimi LLM. Copy the example environment file and fill in your key.
    ```bash
    cp .env.example .env
    # Now, edit the .env file and add your KIMI_API_KEY
    ```

### 2. Running the Application

There are three primary ways to run the application:

-   **Development Mode:** For active development, this command starts the server with hot-reloading.
    ```bash
    make dev
    ```
-   **Production Mode:** This command runs the main `app.py` script directly, suitable for a production environment.
    ```bash
    make run
    ```
-   **Command-Line Interface (CLI):** To use the document processing features without a web browser, run:
    ```bash
    make run-cli
    ```

After starting the web server, the main interface is available at `http://localhost:8000`, and the auto-generated FastAPI documentation can be viewed at `http://localhost:8000/docs`.

## Development Conventions

### Code Style and Linting

-   **Formatting:** The project uses `black` for code formatting and `isort` for import sorting. To automatically format the entire codebase, run:
    ```bash
    make format
    ```
-   **Linting:** `flake8` is used for code linting. To check for style issues and potential errors, run:
    ```bash
    make lint
    ```

### Testing

-   The project uses `pytest` for testing. Tests are located in the `tests/` directory (though this directory is not present in the initial structure). To run the test suite, use:
    ```bash
    make test
    ```

### Project Structure

The codebase is organized into several key directories:

-   `app.py`: The main FastAPI web server entrypoint. It defines all routes and handles HTTP requests.
-   `agents/`: Contains the logic for the AI agents, including the router and specialized agents for different tasks.
-   `graph/`: Defines the LangGraph state machine for the document processing workflow.
-   `tools/`: Provides utility functions for file I/O (`file_tools.py`) and document manipulation (`document_tools.py`).
-   `templates/`: Holds the Jinja2 HTML templates for the frontend.
-   `uploads/`: The default directory for storing uploaded files and processing results.
-   `Makefile`: The central script for automating installation, running, testing, and maintenance tasks.
-   `requirements.txt`: Lists all Python package dependencies.
