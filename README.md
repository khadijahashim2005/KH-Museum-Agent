# KH Museum Agent

An individual NLP dissertation component that generates interactive AI museum guide characters from British Museum artefact data. Built on top of the [AutoGame](https://github.com/AutoGame-copy) group project infrastructure.

## Overview

The system uses a three-agent pipeline to generate, run, and evaluate contextually appropriate museum guides:

1. **Collector** — generates a character profile and avatar from artefact data
2. **Interactor** — manages real-time visitor conversation with three safety safeguards
3. **QA-Judge** — evaluates agent responses across four dimensions

The system runs in two modes:

- **Individual frontend** — custom museum-themed UI serving 10 British Museum artefacts
- **Group frontend integration** — plugs into the AutoGame React frontend as a drop-in backend

---

## Project Structure

```
KH-Museum-Agent/
├── .env                          ← API keys and agent IDs (pre-configured)
├── requirements.txt              ← Python dependencies
├── api/
│   ├── main.py                   ← Individual frontend backend (port 5005)
│   ├── main_group.py             ← Group frontend backend (port 5004)
│   ├── collector.py              ← Step 1: generates character profile
│   ├── interactor.py             ← Step 2: manages conversation
│   ├── evaluator.py              ← Step 3: per-session hard + soft evaluation
│   └── safety/
│       ├── __init__.py
│       ├── boundary_check.py     ← Challenge 1: out-of-scope refusal
│       ├── consistency_guard.py  ← Challenge 2: profile drift prevention
│       └── context_manager.py    ← Challenge 3: token limit management
│
├── scripts/
│   ├── generate_agents.py        ← Pre-generate all agent profiles (run once)
│   │                               includes generate_group_agents() method
│   └── download_images.py        ← Download Mistral images locally (run once)
│
├── evaluation/
│   ├── __init__.py
│   ├── hard_mcq_generator.py     ← Generate factual MCQ questions
│   ├── soft_mcq_generator.py     ← Generate contextual MCQ questions (LLM)
│   ├── combined_mcq_generator.py ← Combine into full testing set
│   ├── inspect_infobox_keys.py   ← Utility: explore dataset infobox fields
│   └── utils.py                  ← Shared helpers
│
├── evaluation_pipeline/
│   ├── __init__.py
│   ├── run_evaluation.py         ← Live 4-dimension evaluation
│   ├── report.py                 ← Generate human-readable report
│   └── test_evaluation.py        ← Run evaluation from command line
│
├── frontend/
│   └── index.html                ← Individual museum-themed frontend
│
└── data/
    ├── british_museum_collections.json  ← Source dataset (add manually)
    ├── cached_agents.json               ← Pre-generated profiles (created by scripts)
    ├── museum_events.json               ← Event metadata (created by generate_agents.py)
    ├── images/                          ← Downloaded agent avatars
    ├── hard_testing_set.json            ← Hard MCQ testing set (created by evaluation/)
    ├── soft_testing_set.json            ← Soft MCQ testing set (created by evaluation/)
    ├── full_testing_set.json            ← Combined testing set (created by evaluation/)
    ├── evaluation_results.json          ← Evaluation results (created by pipeline)
    └── evaluation_report.txt            ← Human-readable report (created by report.py)
```

---

## Prerequisites

- Python 3.11+
- Node.js (for group frontend only)
- A [Mistral AI](https://console.mistral.ai) account with:
  - `COLLECTOR_AGENT_ID` — Collector agent
  - `INTERACTOR_AGENT_ID` — Interactor agent
  - `QA_JUDGE_AGENT_ID` — QA-Judge agent

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/khadijahashim/KH-Museum-Agent.git
cd KH-Museum-Agent

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

All required packages are listed in `requirements.txt`. This includes Flask, Flask-CORS, mistralai, python-dotenv, and all evaluation dependencies.

### 2. Configure environment variables

A `.env` file is already included in the repository with the necessary Mistral API key and agent IDs configured. The application will work out of the box without any changes.

If you have your own Mistral account and want to use your own agents, replace the values in `.env`:

```env
MISTRAL_API_KEY=your_key_here
COLLECTOR_AGENT_ID=your_collector_agent_id
INTERACTOR_AGENT_ID=your_interactor_agent_id
QA_JUDGE_AGENT_ID=your_qa_judge_agent_id
```

---

## Run Order (First Time Setup)

Agent profiles have already been pre-generated and images have already been downloaded — the application will work immediately after setup. The scripts below are provided for reference if you need to regenerate everything from scratch:

```bash
# Generate all agent profiles (~20 minutes)
# Also runs generate_group_agents() to add Magdeburg Ivories + Rosetta Stone
python scripts/generate_agents.py

# Download images locally (prevents Mistral signed URL expiry)
python scripts/download_images.py
```

---

## Running the Application

### Individual frontend

```bash
python api/main.py          # starts on port 5005
```

Open `frontend/index.html` in your browser. The `API_BASE` in the HTML is set to `http://localhost:5005`.

### Group frontend integration

```bash
# Terminal 1
python api/main_group.py    # starts on port 5004

# Terminal 2 — from AutoGame-copy/frontend/
cd frontend
npm install
npm start                   # React app on port 3000, proxies to 5004
```

Make sure `AutoGame-copy/frontend/package.json` has:

```json
"proxy": "http://127.0.0.1:5004"
```

---

## Running Evaluation

> **Note:** Evaluation results have already been generated and are included in the repository at `data/evaluation_results.json` and `data/evaluation_report.txt`. If you want to regenerate them from scratch, delete both files before running the pipeline below.

The evaluation pipeline runs in three stages:

```bash
# Stage 1 — defines the evaluation functions (no output, imported by test_evaluation.py)
python evaluation_pipeline/run_evaluation.py

# Stage 2 — runs evaluation across all 10 artefacts (3 averaged runs each)
# saves results to data/evaluation_results.json
python evaluation_pipeline/test_evaluation.py

# Stage 3 — generates a human-readable report from the results
# saves to data/evaluation_report.txt
python evaluation_pipeline/report.py
```

Edit `TEST_INDEX` and `N_RUNS` at the top of `test_evaluation.py` to control which artefact is evaluated and how many runs to average.

The script supports **resume** — if interrupted, it skips artefacts already saved in `evaluation_results.json` and picks up from where it left off.

---

## Evaluation Framework

The live evaluation pipeline scores agents across four dimensions:

| Dimension      | Weight | Method                                       |
| -------------- | ------ | -------------------------------------------- |
| Hard knowledge | 30%    | MCQ accuracy from structured artefact fields |
| Soft knowledge | 30%    | LLM-as-judge (QA-Judge agent)                |
| Safety         | 20%    | Adversarial refusal testing (5 prompts)      |
| Consistency    | 20%    | Character identity questions (4 prompts)     |

Results are saved to `data/evaluation_results.json` and a summary report to `data/evaluation_report.txt`.

---

## Safety Safeguards

Three safeguards are applied on every conversation turn before the Mistral API is called:

| File                   | Challenge   | Behaviour                                             |
| ---------------------- | ----------- | ----------------------------------------------------- |
| `boundary_check.py`    | Challenge 1 | Refuses out-of-scope queries without an API call      |
| `context_manager.py`   | Challenge 3 | Compresses history when estimated tokens exceed 4,000 |
| `consistency_guard.py` | Challenge 2 | Reinjects character profile every 8 turns             |

---

## Artefacts

### Individual frontend (indices 0–9)

| Index | Artefact                     |
| ----- | ---------------------------- |
| 0     | Abbott Papyrus               |
| 1     | El-Amra Clay Model of Cattle |
| 2     | Benin Ivory Mask             |
| 3     | Bronze Head of Queen Idia    |
| 4     | Musicians Plate              |
| 5     | Statue of Ashurnasirpal II   |
| 6     | Guisborough Helmet           |
| 7     | Bell Shrine of Conall Cael   |
| 8     | Copán Bench Panel            |
| 9     | Empress Pepper Pot           |

### Group frontend (indices 10–11)

| Index | Artefact          | Character                      |
| ----- | ----------------- | ------------------------------ |
| 10    | Magdeburg Ivories | Brother Albrecht von Magdeburg |
| 11    | Rosetta Stone     | Dr. Amina Farouk               |

---

## API Endpoints

| Endpoint               | Method | Description                                             |
| ---------------------- | ------ | ------------------------------------------------------- |
| `/init-conversation`   | POST   | Load cached agent, start Interactor, return first reply |
| `/response`            | POST   | Pass visitor message to Interactor, return reply        |
| `/evaluate-agent`      | POST   | Run full 4-dimension evaluation on current session      |
| `/agent-images/<file>` | GET    | Serve locally stored agent avatar images                |
| `/health`              | GET    | Health check                                            |

---

## Tech Stack

- **Backend** — Python, Flask, Flask-CORS
- **AI** — Mistral AI (agents API)
- **Frontend** — Vanilla HTML, CSS, JavaScript
- **Group frontend** — React (AutoGame-copy)
- **Evaluation** — Custom MCQ pipeline, LLM-as-judge

---

## Author

Khadija Hashim — King's College London
