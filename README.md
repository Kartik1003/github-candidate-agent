# NEXUS: GitHub Candidate Discovery Agent

NEXUS is an advanced, automated candidate discovery and evaluation pipeline. It acts as an autonomous AI recruiting agent that actively searches GitHub for top engineering talent, comprehensively analyzes their technical footprint, scores them using a hybrid AI approach (LLMs, Semantic Embeddings, and ML ranking), and presents actionable insights via a high-tech "Digital Cockpit" dashboard.

## 🚀 Key Features

### 1. Automated Candidate Discovery Pipeline
The core of NEXUS is a parallelized pipeline that autonomously fetches and analyzes GitHub profiles. It breaks down the evaluation process into concurrent stages:
- **Data Fetching:** Pulls repository details, commit history, top languages, and README samples via the GitHub REST API.
- **LLM Classification:** Uses Generative AI to classify candidates based on their bios and READMEs (e.g., identifying students vs. active job seekers, detecting location).
- **Semantic Scoring:** Employs `sentence-transformers` to create semantic embeddings of candidate profiles, matching them against specific archetypes (Student, Job Seeker, Senior Developer).
- **Machine Learning Ranking:** Uses a trained XGBoost model to predict candidate quality and rank them dynamically based on all aggregated features.

### 2. High-Tech Digital Cockpit Dashboard
NEXUS replaces traditional spreadsheets with an immersive, dark-themed dashboard.
- Built with **React** and **Vite**, utilizing a modern tech aesthetic.
- Supports date-based and week-based data filtering.
- Dedicated Candidate Details routing for deep dives into specific profiles.
- Provides visualizations of candidate GitHub activity, skills, and AI-generated pros/cons.

### 3. CEO Intelligence Features
The backend provides advanced, on-demand candidate insights tailored for executive decision-making:
- **Red Flag Detection:** Identifies warning signs in a candidate's profile.
- **Collaboration & Community Presence:** Analyzes how actively a candidate engages in open source and community projects.
- **Growth Trajectory:** Maps the candidate's skill evolution and commit consistency over time.
- **Role-Fit Scoring:** Allows dynamic scoring of all candidates against specific, custom job requirements.

### 4. Reporting & Notifications
- Automated Google Sheets integration via `gspread` for tabular reporting.
- Email report generation with CSV attachments, built for easy distribution to hiring managers.
- Dynamic email template rendering based on candidate performance.

## 🏗️ Architecture & Tech Stack

NEXUS is built with a modern, decoupled architecture:

### Backend (Python / FastAPI)
- **Framework:** FastAPI for high-performance, asynchronous REST & WebSocket APIs.
- **AI/ML:** `google-genai` (LLMs), `sentence-transformers` (Embeddings), `xgboost`, `scikit-learn` (ML Ranking), `torch`, `numpy`.
- **Data Gathering:** `PyGithub`, `beautifulsoup4`, `requests`.
- **Infrastructure:** SQLite for local caching and data storage, `google-auth` for Sheets integration.

### Frontend (React / Vite)
- **Framework:** React 18+ with Vite for lightning-fast HMR.
- **Routing:** `react-router-dom` for seamless navigation between the Dashboard and Candidate Details views.
- **Styling:** Custom CSS with a focus on dark mode, glassmorphism, and high-performance fonts (Space Grotesk, Manrope).

## ⚙️ Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- GitHub Personal Access Token
- Google Service Account Credentials (for Sheets integration)
- Gemini API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd github-candidate-agent
   ```

2. **Backend Setup**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Set up environment variables (.env)
   # Requires GITHUB_TOKEN, GEMINI_API_KEY, SHEET_ID, etc.
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. **Start the Backend Server**
   ```bash
   cd backend
   python -m uvicorn api:app --reload
   ```

2. **Start the Frontend Development Server**
   ```bash
   cd frontend
   npm run dev
   ```

## 🧠 How the Hybrid Pipeline Works

The pipeline (`pipeline.py`) minimizes latency by executing heavy AI tasks concurrently:
1. **Fetch:** Retrieve GitHub user data and perform a quick regex-based location check.
2. **Parallel AI Execution:**
   - Generates semantic embeddings of the bio/README.
   - LLM classifies the profile (Job Seeker vs Student).
   - LLM extracts portfolio and LinkedIn links.
   - LLM generates a qualitative score based on code consistency and tech depth.
3. **ML Aggregation:** An XGBoost model evaluates the LLM scores and semantic embeddings to produce a final ranking probability.
4. **Storage:** Results are cached in SQLite and JSON formats, preventing redundant API calls.

## 📝 License
Proprietary/Internal use only.
