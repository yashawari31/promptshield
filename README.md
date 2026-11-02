# PromptShield – Source-Aware Prompt Injection Defense Framework

**PromptShield** is a prompt-injection detection and sanitization prototype designed to identify malicious instructions and potential data-exfiltration attempts in text inputs from different sources.

It combines **rule-based detection, protected-value matching, and Machine Learning (TF-IDF + Logistic Regression)** to evaluate suspicious content and apply a policy-based decision: **ALLOW, SANITIZE, or BLOCK**.

## Problem Statement

Large Language Model (LLM) applications can be vulnerable to prompt injection attacks, where malicious instructions are embedded in user messages, documents, or external tool outputs.

Such attacks may attempt to:
- Override the application's original instructions.
- Extract confidential information or credentials.
- Manipulate the model into performing unintended actions.
- Hide malicious instructions inside otherwise legitimate content.

PromptShield aims to provide an additional screening layer to help identify and handle these threats.

## Key Features

- **Source-Aware Screening:** Supports inputs from users, voice transcripts, documents, and tool outputs.
- **Rule-Based Detection:** Identifies suspicious instruction overrides and potential secret-exfiltration patterns.
- **Machine Learning Detection:** Uses a TF-IDF vectorizer and Logistic Regression classifier to estimate the likelihood of malicious content.
- **Policy-Based Decisions:** Applies configurable security policies to produce ALLOW, SANITIZE, or BLOCK decisions.
- **Content Sanitization:** Attempts to remove suspicious portions while preserving useful text.
- **Protected-Value Matching:** Checks for configured sensitive values.
- **Audit Logging:** Stores screening events in JSONL format for traceability.
- **REST API:** Provides FastAPI endpoints for health checks, screening, and audit retrieval.
- **Interactive Dashboard:** Uses Streamlit to display screening results.

## System Architecture

```text
       User / Document / Tool Output
                    |
                    v
             Streamlit UI
                    |
                    v
              FastAPI Backend
                    |
                    v
             Input Normalization
                    |
                    v
             Detection Pipeline
              /             \
             v               v
       Rule-Based         ML Classifier
        Detection       TF-IDF + Logistic
             \             /
              v           v
              Policy Engine
                    |
          +---------+---------+
          |         |         |
          v         v         v
        ALLOW    SANITIZE    BLOCK
                    |
                    v
             JSONL Audit Logs
```

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| Frontend / Dashboard | Streamlit |
| Machine Learning | Scikit-learn |
| Text Vectorization | TF-IDF |
| ML Algorithm | Logistic Regression |
| Data Handling | JSON / JSONL |
| Testing | Pytest |
| API Testing | Swagger UI |

## Project Structure

```text
PromptShield/
│
├── app/
│   ├── main.py
│   ├── classifier.py
│   ├── detectors.py
│   ├── normalize.py
│   ├── policy.py
│   ├── sanitize.py
│   ├── audit.py
│   └── schemas.py
│
├── ml/
│   └── promptshield_model.joblib
│
├── ui/
│   └── app.py
│
├── tests/
│
├── eval/
│   └── evaluate_pipeline.py
│
├── reports/
│
├── logs/
│   └── audit.jsonl
│
└── requirements.txt
```

## How It Works

1. **Input Collection:** The application receives text along with its source type.
2. **Normalization:** The input is normalized before inspection.
3. **Threat Detection:** Rule-based detectors and the ML classifier examine the content.
4. **Policy Evaluation:** The policy engine considers detected signals, risk score, and input source.
5. **Decision:** The system returns one of three outcomes:
   - `ALLOW` – Input is allowed through screening.
   - `SANITIZE` – Suspicious content is removed where possible.
   - `BLOCK` – Input is rejected by the screening policy.
6. **Audit Logging:** The screening decision and relevant metadata are recorded for later retrieval.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Checks backend health and model status. |
| POST | `/screen` | Screens text and returns a security decision. |
| GET | `/audit/{request_id}` | Retrieves an audit record using its request ID. |

Interactive API documentation is available at:

`http://127.0.0.1:8000/docs`

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/yashawari31/promptshield.git
cd promptshield
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS**
```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the FastAPI backend

```bash
python -m uvicorn app.main:app --reload
```

Backend:

`http://127.0.0.1:8000`

### 5. Start the Streamlit dashboard

Open a second terminal, activate the virtual environment, and run:

```bash
streamlit run ui/app.py
```

Dashboard:

`http://localhost:8501`

## Evaluation Results

The full screening pipeline was evaluated on **500 synthetic/template-generated examples**.

| Metric | Result |
|---|---:|
| Accuracy | 92.0% |
| Precision | 96.1% |
| Recall | 87.6% |
| F1-Score | 91.6% |

The evaluation helped identify both successful detections and false negatives, highlighting the importance of testing against varied attack patterns.

*Note: These results are from a synthetic evaluation dataset and should not be interpreted as production security performance or an independent real-world benchmark.*

## Testing

The project uses Pytest for automated testing.

```bash
pytest -q
```

**Recorded test result:** 35 tests passed.

## Limitations and Future Improvements

- Improve detection of obfuscated, misspelled, and novel prompt-injection attempts.
- Evaluate against public datasets and benchmarks such as BIPIA and InjecAgent.
- Improve detection of indirect prompt injections in external content.
- Expand adversarial testing and reduce false negatives.
- Integrate with LLM applications as a middleware screening layer.
- Extend audit capabilities and add more advanced monitoring.

## Project Information

- **Project:** PromptShield – Source-Aware Prompt Injection Defense Framework
- **Team:** Sin Promesas
- **Event:** VORTEXA 3.0 Hackathon
- **Category:** AI / Machine Learning / Cybersecurity
- **GitHub:** https://github.com/yashawari31/promptshield

---

**Disclaimer:** PromptShield is a prototype security-screening framework. It provides an additional layer of input inspection and is not a guarantee against all prompt-injection or data-exfiltration attacks.