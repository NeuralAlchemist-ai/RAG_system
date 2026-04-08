from query_data import RAGChatBot
from config import EMBEDDING_MODEL
import ollama
import numpy as np
import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


TEST_CASES = [
    {
        "question": "What is the main topic of the document?",
        "expected": "The document is about artificial intelligence applications in healthcare, covering diagnostics, drug discovery and patient care."
    },
    {
        "question": "What was the AI healthcare market value in 2023?",
        "expected": "The global AI healthcare market was valued at 14.6 billion dollars in 2023."
    },
    {
        "question": "How accurate was the Stanford lung cancer detection model?",
        "expected": "The Stanford deep learning model detected lung cancer with 94.5% accuracy, outperforming radiologists by 11%."
    },
    {
        "question": "What does the author recommend for hospitals adopting AI?",
        "expected": "The author recommends a phased adoption approach, starting with low-risk screening workflows before expanding to critical care."
    },
    {
        "question": "What ethical recommendation does the report make?",
        "expected": "The report recommends establishing a dedicated AI ethics committee in every healthcare institution to review model decisions quarterly."
    },
    {
        "question": "What technology does the report recommend to overcome data privacy barriers?",
        "expected": "The report recommends federated learning, which allows models to train across hospitals without sharing raw patient data."
    },
    {
        "question": "What are the two main challenges mentioned in the report?",
        "expected": "The two main challenges are data privacy regulations like HIPAA and GDPR, and model interpretability issues with black box deep learning."
    },
    {
        "question": "What prediction did the LSTM model make about heart failure?",
        "expected": "The LSTM model predicted heart failure 12 months in advance with 87% precision using routine blood test data."
    },
]

class Test:
    def __init__(self):
        self.model = EMBEDDING_MODEL

    def _get_embedding(self, text: str):
        response = ollama.embeddings(model=self.model, prompt=text)
        return response['embedding']
    
    def _cos_sim(self, vec1, vec2):
        v1, v2 = np.array(vec1), np.array(vec2)
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

    def _semantic_similarity(self, expected: str, actual: str):
        expected_emb = self._get_embedding(expected)
        actual_emb = self._get_embedding(actual)
        return self._cos_sim(expected_emb, actual_emb)

    def _grade(self, score: float):
        if score >= 0.8: return "✅ PASS"
        if score >= 0.6: return "⚠️  WEAK"
        return "❌ FAIL"

    def evaluate(self):
        chatbot = RAGChatBot()
        user_id = "test_user"  # For testing
        results = []
        total = 0

        print("\n" + "="*60)
        print("RAG EVALUATION")
        print("="*60)

        for i, case in enumerate(TEST_CASES):
            print(f"\n[{i+1}/{len(TEST_CASES)}] {case['question']}")

            answer, sources = chatbot.ask(case["question"], user_id=user_id, k=3)
            chatbot.clear_history()

            score = self._semantic_similarity(case["expected"], answer)
            total += score

            print(f"Expected  : {case['expected']}")
            print(f"Got       : {answer[:150]}")
            print(f"Score     : {score:.2f} {self._grade(score)}")
            print(f"Sources   : {', '.join(sources)}")

            results.append({
                "question": case["question"],
                "expected": case["expected"],
                "actual": answer,
                "score": round(score, 3),
                "grade": self._grade(score),
                "sources": sources
            })

        avg = total / len(TEST_CASES)
        passed = sum(1 for r in results if r["score"] >= 0.8)

        print("\n" + "="*60)
        print(f"Avg Score : {avg:.2f}/1.00")
        print(f"Passed    : {passed}/{len(TEST_CASES)}")
        print("="*60)

if __name__ == "__main__":
    tester=Test()
    tester.evaluate()