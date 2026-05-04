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
├── api/
│   ├── main.py                  ← Individual frontend backend (port 5005)
│   ├── main_group.py            ← Group frontend backend (port 5004)
│   ├── collector.py             ← Step 1: generates character profile
│   ├── interactor.py            ← Step 2: manages conversation
│   └── safety/
│       ├── boundary_check.py    ← Challenge 1: out-of-scope refusal
│       ├── consistency_guard.py ← Challenge 2: profile drift prevention
│       └── context_manager.py   ← Challenge 3: token limit management
│
├── scripts/
│   ├── generate_agents.py       ← Pre-generate all agent profiles (run once)
│   ├── generate_group_agents.py ← Pre-generate group artefact profiles
│   └── download_images.py       ← Download Mistral images locally (run once)
│
├── evaluation/
│   ├── hard_mcq_generator.py    ← Generate factual MCQ questions
│   ├── soft_mcq_generator.py    ← Generate contextual MCQ questions (LLM)
│   ├── combined_mcq_generator.py← Combine into full testing set
│   ├── evaluation_script.py     ← Group project evaluation (4-dimension)
│   └── utils.py                 ← Shared helpers
│
├── evaluation_pipeline/
│   ├── run_evaluation.py        ← Live 4-dimension evaluation
│   └── report.py                ← Generate human-readable report
│
├── frontend/
│   └── index.html               ← Individual museum-themed frontend
│
├── data/
│   ├── cached_agents.json       ← Pre-generated profiles (created by scripts)
│   ├── images/                  ← Downloaded agent avatars
│   ├── hard_testing_set.json    ← Hard MCQ testing set
│   ├── soft_testing_set.json    ← Soft MCQ testing set
│   ├── full_testing_set.json    ← Combined testing set
│   └── evaluation_results.json  ← Evaluation results
│
└── scripts/
    └── test_evaluation.py       ← Run evaluation from command line
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

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
MISTRAL_API_KEY=your_key_here
COLLECTOR_AGENT_ID=your_collector_agent_id
INTERACTOR_AGENT_ID=your_interactor_agent_id
QA_JUDGE_AGENT_ID=your_qa_judge_agent_id
```

### 3. Add the British Museum dataset

Copy `british_museum_collections.json` into `data/`:

```
KH-Museum-Agent/data/british_museum_collections.json
```

---

## Run Order (First Time Setup)

Run these once before starting the application:

```bash
# Step 1 — Pre-generate all agent profiles (~20 minutes)
python scripts/generate_agents.py

# Step 2 — Download images locally (prevents expiry)
python scripts/download_images.py

# Step 3 — Generate evaluation testing sets
python evaluation/combined_mcq_generator.py
```

---

## Running the Application

### Individual frontend

```bash
python api/main.py          # starts on port 5005
```

Open `frontend/index.html` in your browser. Make sure `API_BASE` in the HTML is set to `http://localhost:5005`.

### Group frontend integration

```bash
# Terminal 1
python api/main_group.py    # starts on port 5004

# Terminal 2 — from AutoGame-copy/frontend/
npm install
npm start                   # React app on port 3000, proxies to 5004
```

Make sure `AutoGame-copy/frontend/package.json` has:

```json
"proxy": "http://127.0.0.1:5004"
```

---

## Running Evaluation

### From the UI

Start the application, select an artefact, chat with the agent, then click **Run Evaluation**.

### From the command line

```bash
# Evaluate a single artefact (3 averaged runs)
python scripts/test_evaluation.py

# Generate a readable report
python evaluation_pipeline/report.py
```

Edit `TEST_INDEX` in `test_evaluation.py` to change which artefact is evaluated (0–9).

---

## Evaluation Framework

The live evaluation pipeline scores agents across four dimensions:

| Dimension      | Weight | Method                              |
| -------------- | ------ | ----------------------------------- |
| Hard knowledge | 30%    | MCQ accuracy from structured fields |
| Soft knowledge | 30%    | LLM-as-judge (QA-Judge agent)       |
| Safety         | 20%    | Adversarial refusal testing         |
| Consistency    | 20%    | Character identity questions        |

Results are saved to `data/evaluation_results.json` and a summary report to `data/evaluation_report.txt`.

---

## Safety Safeguards

Three safeguards are applied on every conversation turn before the Mistral API is called:

| Safeguard              | Challenge   | Behaviour                                                                                       |
| ---------------------- | ----------- | ----------------------------------------------------------------------------------------------- |
| `boundary_check.py`    | Challenge 1 | Refuses out-of-scope queries (harmful, medical, legal, political, homework) without an API call |
| `context_manager.py`   | Challenge 3 | Compresses conversation history using LLM summarisation when estimated tokens exceed 4,000      |
| `consistency_guard.py` | Challenge 2 | Reinjection of character profile every 8 turns to prevent persona drift                         |

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
Individual NLP Dissertation Component, 2025–2026
