# Journal Entry Automation Tool

#### Video Demo: (https://youtu.be/Zov-_5xhVpc)

**Description**:
The Journal Entry Automation Tool is a specialized financial technology application designed to streamline a critical step in the financial close process. Built using SQLite, Flask, and Python, this tool automates the analytical profiling of General Ledger (GL) journal entries, ensuring data integrity and compliance while reducing manual effort.

Below are the various files included in my FINAL Project Folder explainin
**app.py**: 
The **Journal Entry Profiling Tool** is a Flask-based web application designed to automate the validation and auditing of financial journal entries. The application workflow begins with a secure file upload system (`/upload`) that accepts CSV datasets, validating file extensions and storing them temporarily. A key feature is the interactive column mapping interface (`/map`), which allows users to dynamically align their specific dataset headers (e.g., "Date", "Account #") with the system's required schema (e.g., "Posting_Date", "GL_Account") without altering their original files manually. Once mapped, the data is normalized and loaded into an in-memory SQLite database, where the core engine (`/execution`) runs a series of predefined SQL-based audit rules—such as detecting Segregation of Duties (SOD) conflicts, identifying duplicate postings, and flagging entries made on weekends. The results are then aggregated and presented in a comprehensive report, highlighting any transactions that violate these compliance controls.

**rules.py**: 
The application's logic is modularized by isolating all audit logic within `rules.py`, ensuring the system remains highly scalable and maintainable. This design pattern separates the validation rules from the core application logic, allowing developers or auditors to easily append, modify, or remove SQL-based rule sets without risking regression in the main application flow. The `JE_RULES` structure is designed to be extensible; adding a new compliance check is as simple as defining a new dictionary entry with the SQL query and metadata. Looking forward, this modular architecture lays the groundwork for integrating an AI-driven agent. By decoupling the rules, we can deploy a machine learning model or LLM agent capable of analyzing historical data patterns to autonomously generate and propose new, sophisticated SQL rules for detecting emerging fraud vectors or anomalies that static rule sets might miss.

**templates**:
The application utilizes four distinct HTML templates to guide the user through the audit workflow:
*   **`templates/index.html`**: Serves as the landing page and entry point. It features a simple, clean interface for users to select and upload their CSV datasets, complete with flash message support to display validation errors (e.g., "Invalid file type") directly to the user.
*   **`templates/map.html`**: Provides the interactive mapping interface. This template dynamically generates dropdown menus for each required system header (like "GL_Account" or "Posting_Date"), populating them with the columns found in the user's uploaded file, ensuring accurate data alignment before processing.
*   **`templates/successful.html`**: Acts as a confirmation and staging area. Once mapping is complete, this page confirms the file is ready and lists the specific audit rules (from `rules.py`) that are about to be executed, giving the user transparency into the checks being performed before they trigger the analysis.
*   **`templates/results.html`**: Displays the final audit report. It iterates through the execution results, rendering HTML tables for any journal entries that were flagged by the SQL rules, or displaying a "no entries found" message if the data passed specific compliance checks.

**Uploads Folder**: 
The application manages data integrity through a dedicated `uploads/` directory, which acts as the secure repository for incoming data. To rigorously test the system's robustness, we utilized Gemini to generate a diverse suite of synthetic datasets (`Dataset_1.csv` through `Dataset_5.csv`), each simulating different financial scenarios and header conventions (e.g., "Trx_Date" vs. "Posting_Date") to challenge the mapping logic. The workflow is designed so that a standardized "mapped" file (e.g., `mapped_Dataset_1.csv`) is only generated and saved to the `uploads/` folder *after* the user successfully uploads a raw file and completes the validation process via the mapping interface. This ensures that only verified, normalized data is ever passed to the execution engine for analysis, maintaining strict quality control over the inputs used for audit rule testing.

**requirements.txt**:
To ensure a consistent and reproducible development environment, the project's dependencies are explicitly defined in `requirements.txt`. The application relies on **Flask** as its core web framework to handle routing, templating, and request management, while **pandas** is utilized for its powerful data manipulation capabilities, specifically for reading CSV files, handling dataframes, and interfacing with the SQL engine. Standard libraries such as `sqlite3`, `io`, and `os` are leveraged directly from Python and do not require external installation. Users can easily install the necessary packages by running `pip install -r requirements.txt`, ensuring the application has all the required components to execute the data processing and audit workflows correctly.

**Setup Instructions**:
1.  **Clone the repository**.
2.  **Create a virtual environment**: `python -m venv .venv`
3.  **Activate the virtual environment**:
    *   Windows: `.venv\Scripts\activate`
    *   Mac/Linux: `source .venv/bin/activate`
4.  **Install dependencies**: `pip install -r requirements.txt`
5.  **Get a Gemini API Key**:
    *   Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   Click "Create API key".
    *   Copy the key.
6.  **Configure Environment**:
    *   Open the `.env` file.
    *   Replace `YOUR_API_KEY_HERE` with your actual API key.
7.  **Run the application**: `python app.py`

**.'venv'**:
I structured the project to use a Python virtual environment (`.venv`) to ensure a clean and isolated development workspace. By doing this, I could manage the application's dependencies—specifically **Flask** and **pandas**—locally within the project directory, effectively preventing any version conflicts with other tools on my system. This setup allowed me to safely install and test the exact package versions defined in `requirements.txt` without affecting my global Python environment, ensuring the application remains portable and easy to run on any machine.

**AI usage**:
While the core concept, architectural design, and audit logic of this Journal Entry Analysis Tool are entirely my own original work, I leveraged Gemini as an intelligent assistant during the development process. I utilized the AI primarily for troubleshooting syntax errors, generating synthetic test datasets, and refining specific code snippets to follow best practices. This collaboration allowed me to focus more on the strategic aspects of the application—such as the scalable rule engine and user workflow—while using AI to accelerate the implementation details, ensuring the final product represents my own vision and problem-solving approach.