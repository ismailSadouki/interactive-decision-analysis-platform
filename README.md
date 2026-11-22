## Run the Application

### Requirements
- Python 3.10 or higher (Python 3.11+ recommended).

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Launch the application

```bash
streamlit run app.py
```

The application will be available at:

http://localhost:8501

### 5. Run tests (optional)

```bash
python -m pytest
```

**Note:** The Streamlit application does not require Node.js or PostgreSQL.
