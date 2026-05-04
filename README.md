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
# Also runs generate_group_agents() to add Magdeburg Ivories + Rosetta Stone
python scripts/generate_agents.py

# Step 2 — Download images locally (prevents URL expiry)
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

Open `frontend/index.html` in your browser. The `API_BASE` in the HTML is set to `http://localhost:5005`.

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

Evaluation is run from the command line using `test_evaluation.py`:

```bash
# Run evaluation across all 10 artefacts (3 averaged runs each)
python evaluation_pipeline/test_evaluation.py

# Generate a readable report from results
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

## Adding a New Artefact

To add a new artefact to the system:

1. Ensure it exists in `data/british_museum_collections.json`
2. Add its title to `TARGET_TITLES` in both `evaluation/hard_mcq_generator.py` and `evaluation/soft_mcq_generator.py`
3. Run `python scripts/generate_agents.py` to generate the character profile
4. Run `python evaluation/combined_mcq_generator.py` to generate evaluation questions
5. Add its metadata to the `artefacts` object in `frontend/index.html`

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
