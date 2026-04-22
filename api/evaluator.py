# ============================================================
# evaluator.py
# Step 3: Evaluates the Interactor agent using:
# - Hard knowledge (MCQ + Precision/Recall)
# - Soft knowledge (LLM-as-judge)
# ============================================================

import os
import json
import sys
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()


class Evaluator:
    def __init__(self, artefact: dict, profile: str, interactor):
        self.client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        self.judge_agent_id = os.getenv("QA_JUDGE_AGENT_ID")
        self.artefact = artefact
        self.profile = profile
        self.interactor = interactor

    def evaluate_hard_knowledge(self) -> dict:
        """
        Generate MCQ questions from structured artefact fields
        and evaluate the agent's answers using Precision/Recall
        """
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from evaluation.hard_mcq_generator import build_hard_question_objects

        questions = build_hard_question_objects(self.artefact)
        results = []
        correct_count = 0

        for q in questions:
            agent_answer = self.interactor.chat(
                f"Please answer this question with ONLY the exact option text, nothing else: {q['question']} Options: {', '.join(q['options'])}"
            )

            is_correct = q['correct_answer'].lower().strip() in agent_answer.lower().strip()
            if is_correct:
                correct_count += 1

            precision, recall = self._calculate_precision_recall(
                agent_answer, q['correct_answer']
            )

            results.append({
                "question": q['question'],
                "correct_answer": q['correct_answer'],
                "agent_answer": agent_answer,
                "is_correct": is_correct,
                "precision": round(precision, 2),
                "recall": round(recall, 2)
            })

        accuracy = correct_count / len(questions) if questions else 0
        avg_precision = sum(r['precision'] for r in results) / len(results) if results else 0
        avg_recall = sum(r['recall'] for r in results) / len(results) if results else 0

        return {
            "type": "hard_knowledge",
            "total_questions": len(questions),
            "correct": correct_count,
            "accuracy": round(accuracy, 2),
            "avg_precision": round(avg_precision, 2),
            "avg_recall": round(avg_recall, 2),
            "results": results
        }

    def evaluate_soft_knowledge(self) -> dict:
        """
        Generate questions from artefact summary
        and evaluate using QA-Judge agent
        """
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        import api.config.llm_client as llm_module
        import evaluation.soft_mcq_generator as soft_module
        soft_module.call_llm = llm_module.call_llm

        from evaluation.soft_mcq_generator import build_soft_question_objects

        questions = build_soft_question_objects(self.artefact)
        results = []
        scores = []

        for q in questions:
            agent_answer = self.interactor.chat(q['question'])
            judgment = self._judge_answer(
                q['question'],
                agent_answer,
                q['correct_answer'],
                q['source_summary']
            )
            score = self._parse_judgment_score(judgment)
            scores.append(score)
            results.append({
                "question": q['question'],
                "correct_answer": q['correct_answer'],
                "agent_answer": agent_answer,
                "judgment": judgment,
                "score": score
            })

        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "type": "soft_knowledge",
            "total_questions": len(questions),
            "avg_score": round(avg_score, 2),
            "results": results
        }

    def _judge_answer(self, question, agent_answer, correct_answer, source_summary) -> str:
        """Use KH-QA-Judge agent to evaluate answer"""
        qa_input = f"""Question: {question}
AgentAnswer: {agent_answer}
Reference: {source_summary}
CorrectAnswer: {correct_answer}"""

        response = self.client.beta.conversations.start(
            agent_id=self.judge_agent_id,
            inputs=[{"role": "user", "content": qa_input}],
        )
        return response.outputs[0].content.strip()

    def _calculate_precision_recall(self, agent_answer, correct_answer):
        """Calculate precision and recall scores"""
        agent_words = set(agent_answer.lower().split())
        correct_words = set(correct_answer.lower().split())
        matches = agent_words.intersection(correct_words)
        precision = len(matches) / len(agent_words) if agent_words else 0
        recall = len(matches) / len(correct_words) if correct_words else 0
        return precision, recall

    def _parse_judgment_score(self, judgment: str) -> float:
        """Parse score from QA-Judge response"""
        try:
            clean = judgment.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            return float(data.get("score", 0))
        except:
            return 0.0