# User Guide — KH Museum Agent

## Overview

KH Museum Agent is an AI-powered interactive museum guide. It generates a personalised digital character for a given British Museum artefact and lets you hold a conversation with that character as if you were speaking with a knowledgeable guide in the gallery. An automated evaluation system measures the quality of each guide across four dimensions.

---

## Quick-Start Checklist

Before your first session, confirm the following are in place:

| Step | What to do                                                                                                                     |
| ---- | ------------------------------------------------------------------------------------------------------------------------------ |
| 1    | Python 3.10+ installed                                                                                                         |
| 2    | `pip install -r requirements.txt` run from the project root                                                                    |
| 3    | `.env` file present with the necessary `MISTRAL_API_KEY`, `COLLECTOR_AGENT_ID`, `INTERACTOR_AGENT_ID`, and `QA_JUDGE_AGENT_ID` |
| 4    | `data/cached_agents.json` populated (run `python scripts/generate_agents.py` once if the file does not exist)                  |

---

## Starting the Application

Open a terminal in the project root and run:

```
python api/main.py
```

Then open your browser and navigate to:

```
http://localhost:5005
```

You will see the three-panel museum interface shown below.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         KH Museum Agent                             │
├──────────────────┬───────────────────────────┬──────────────────────┤
│  CHARACTER BIO   │       CONVERSATION        │   ARTEFACT DETAILS   │
│                  │                           │                      │
│  [Portrait]      │  ┌─────────────────────┐  │  Title               │
│                  │  │ Guide: Hello! I am… │  │  Date created        │
│  Name            │  └─────────────────────┘  │  Culture / Origin    │
│  Age             │                           │  Materials           │
│  Background      │  ┌─────────────────────┐  │  Gallery location    │
│  Expertise       │  │ You: …              │  │  Discovery site      │
│  Cultural link   │  └─────────────────────┘  │  Dimensions          │
│                  │                           │  Wikipedia →         │
│                  │  [Type your message…] [➤] │                      │
│                  │  [Evaluate Agent]         │                      │
└──────────────────┴───────────────────────────┴──────────────────────┘
```

---

## Session Walk-through

### Step 1 — Select an Artefact

Use the dropdown at the top of the page to choose one of the ten available British Museum artefacts, for example the **Rosetta Stone** or the **Benin Ivory Mask**.

As soon as you select an artefact:

- The right panel fills in with the artefact's metadata (date, origin, materials, gallery, dimensions, and a Wikipedia link).
- The left panel loads the AI-generated character portrait and biography.
- The character sends an opening greeting in the centre chat panel.

> **Tip:** The character's background, name, and cultural connection are all unique to the artefact — each guide is different.

---

### Step 2 — Converse with the Guide

Type your question in the message box at the bottom of the centre panel and press **Send** (or press Enter).

**Example questions to try:**

| Type of question        | Example                                                            |
| ----------------------- | ------------------------------------------------------------------ |
| Factual / historical    | "When was this artefact made?"                                     |
| Materials and craft     | "What is it made from and how was it decorated?"                   |
| Cultural context        | "What does this object tell us about the society that created it?" |
| Personal (in-character) | "How did you come to care for this object?"                        |
| Gallery location        | "Where can I find this in the museum today?"                       |

The guide responds in character, drawing on the artefact's history and its own fictional backstory.

**What happens if you ask something off-topic?**

The system applies a boundary check before every response. If your question falls outside the guide's scope (homework help, medical advice, political opinions, harmful requests, etc.), the guide will politely decline in character and redirect to the artefact. For example:

> _"That falls a little outside what I can help with — but I'd love to tell you more about the inscription on this stone…"_

---

### Step 3 — Evaluating the Guide (Optional)

After you have held a conversation, You can run the evaluation script by entering the following commands in the terminal. 
NOTE: This has already been done. In order to re-run the evaluation -> delete data/evaluation_results.json and data/evaluation_report.txt. After that you can run the following list of commands.

```
cd evaluation_pipeline
python run_evaluation.py
python test_evaluation.py
python report_evaluation.py
```


The system runs a four-dimensional evaluation automatically:

```
Evaluation dimensions
─────────────────────────────────────────────────────────────
 Hard Knowledge  (30%)  Multiple-choice questions on specific
                         artefact facts (location, date, materials…)

 Soft Knowledge  (30%)  Contextual questions judged by a second
                         AI for depth of understanding

 Safety          (20%)  Five tests checking the guide correctly
                         refuses out-of-scope requests

 Consistency     (20%)  Four tests verifying the guide stays
                         in character and references the artefact
─────────────────────────────────────────────────────────────
```

A progress bar and per-dimension scores appear on screen when evaluation completes. A full human-readable report is also saved to `data/evaluation_report.txt`.

**Sample evaluation summary output:**

```
  Artefact                          Hard  Soft  Safe  Cons   Avg
  ──────────────────────────────── ───── ───── ───── ───── ─────
  Guisborough Helmet                1.00  0.90  1.00  1.00  0.97
  Empress pepper pot                1.00  0.77  1.00  1.00  0.93
  Bronze Head of Queen Idia         0.58  0.73  1.00  1.00  0.79
  ──────────────────────────────── ───── ───── ───── ───── ─────
  MEAN                                                      0.92
```

Scores range from 0.0 to 1.0 (1.0 = perfect). The system mean across all artefacts is **0.92**.

---

## Group Mode

A second configuration integrates the agent into a shared group project interface. To run it:

```
python api/main_group.py
```

Then navigate to `http://localhost:5004`.

This mode loads two shared artefacts (the **Magdeburg Ivories** and the **Rosetta Stone**) with pre-assigned character names and existing group-project portraits. All other features — conversation, safety safeguards, evaluation — behave identically to the individual mode.

---

## All Ten Artefacts at a Glance

| #   | Artefact                     | Period          | Origin   |
| --- | ---------------------------- | --------------- | -------- |
| 1   | Abbott Papyrus               | c. 1100 BCE     | Egypt    |
| 2   | El-Amra Clay Model of Cattle | c. 3500 BCE     | Egypt    |
| 3   | Benin Ivory Mask             | 16th century    | Nigeria  |
| 4   | Bronze Head of Queen Idia    | 16th century    | Nigeria  |
| 5   | Musicians Plate              | 7th century     | Cyprus   |
| 6   | Statue of Ashurnasirpal II   | 883–859 BCE     | Iraq     |
| 7   | Guisborough Helmet           | 2nd–3rd century | England  |
| 8   | Bell Shrine of Conall Cael   | 8th century     | Ireland  |
| 9   | Copán Bench Panel            | 8th century     | Honduras |
| 10  | Empress Pepper Pot           | 4th century     | England  |
