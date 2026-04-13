"""
Demo Evaluator with Mock Scores
Shows how evaluation system works without using API calls
Perfect for testing when quota is exceeded
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import statistics
import random

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

BASE_DIR = Path(__file__).resolve().parent

EVALUATION_CRITERIA = {
    "clarity": "How clear and understandable is the response?",
    "unambiguity": "Is the response free from ambiguity and confusing language?",
    "relevance": "How relevant is the response to the query asked?",
    "completeness": "Does the response provide sufficient information to answer the query?",
    "coherence": "Is the response logically structured and coherent?",
}


def generate_mock_evaluation(query: str, response: str, seed: int = None) -> dict:
    """
    Generate realistic mock scores based on response characteristics
    Uses heuristics to simulate LLM judgment
    """
    if seed is not None:
        random.seed(seed)
    
    # Heuristics for scoring
    response_lower = response.lower()
    query_lower = query.lower()
    
    # Base scores
    base_clarity = 3.5 + random.uniform(-0.5, 1.5)
    base_relevance = 3.8 + random.uniform(-0.5, 1.2)
    
    # Adjust based on response characteristics
    if len(response) < 50:
        base_clarity -= 0.5
        base_completeness = 2.5
    elif len(response) > 500:
        base_clarity -= 0.3
        base_completeness = 4.2
    else:
        base_completeness = 3.8
    
    # Check if response addresses query
    query_words = set(query.lower().split())
    response_words = set(response.lower().split())
    relevance_overlap = len(query_words & response_words) / max(len(query_words), 1)
    
    if relevance_overlap > 0.5:
        base_relevance += 0.5
    
    scores = {
        "clarity": round(min(5.0, max(0.0, base_clarity)), 1),
        "unambiguity": round(min(5.0, max(0.0, base_clarity + random.uniform(-0.2, 0.3))), 1),
        "relevance": round(min(5.0, max(0.0, base_relevance)), 1),
        "completeness": round(min(5.0, max(0.0, base_completeness)), 1),
        "coherence": round(min(5.0, max(0.0, base_clarity - random.uniform(-0.2, 0.3))), 1),
    }
    
    # Generate reasoning
    reasoning_map = {
        "clarity": "Response is " + ("very clear and easy to understand" if scores["clarity"] > 4 else "reasonably clear" if scores["clarity"] > 3 else "somewhat unclear"),
        "unambiguity": "Response is " + ("precise and unambiguous" if scores["unambiguity"] > 4 else "mostly clear with minor ambiguities" if scores["unambiguity"] > 3 else "difficult to interpret"),
        "relevance": "Response is " + ("highly relevant to the query" if scores["relevance"] > 4 else "mostly relevant with some tangents" if scores["relevance"] > 3 else "partially addresses the query"),
        "completeness": "Response " + ("thoroughly covers the topic" if scores["completeness"] > 4 else "addresses key points" if scores["completeness"] > 3 else "lacks important information"),
        "coherence": "Response is " + ("well-structured and logical" if scores["coherence"] > 4 else "mostly coherent" if scores["coherence"] > 3 else "somewhat disorganized"),
    }
    
    return {
        "scores": {
            criterion: {
                "score": scores[criterion],
                "reasoning": reasoning_map[criterion]
            }
            for criterion in EVALUATION_CRITERIA.keys()
        },
        "raw_scores": scores
    }


def evaluate_chatbot_response_demo(query: str, response: str, seed: int = None) -> dict:
    """
    Demo evaluation - returns realistic mock scores
    """
    logger.info(f"[DEMO MODE] Evaluating: {query[:60]}...")
    
    eval_data = generate_mock_evaluation(query, response, seed)
    raw_scores = eval_data["raw_scores"]
    
    overall_score = statistics.mean(raw_scores.values())
    
    return {
        "query": query,
        "response": response,
        "scores": eval_data["scores"],
        "overall_score": round(overall_score, 2),
        "max_score": round(max(raw_scores.values()), 2),
        "min_score": round(min(raw_scores.values()), 2),
        "api_calls_used": 0,
        "mode": "DEMO",
        "metadata": {
            "evaluation_time": datetime.now().isoformat(),
            "note": "Mock scores for demonstration (API quota exceeded)",
            "num_criteria": len(EVALUATION_CRITERIA),
        }
    }


def run_evaluation_demo(test_responses: list[dict], output_file: Optional[str] = None) -> dict:
    """
    Run demo evaluation with mock scores
    """
    logger.info(f"[DEMO MODE] Starting evaluation of {len(test_responses)} responses...")
    logger.info("Note: Using realistic mock scores (API quota exceeded)")
    
    results = {
        "evaluation_summary": {
            "total_tests": len(test_responses),
            "timestamp": datetime.now().isoformat(),
            "mode": "DEMO - Mock Scores",
            "criteria": list(EVALUATION_CRITERIA.keys()),
            "note": "Free tier quota exceeded - showing how evaluation works with realistic mock data"
        },
        "test_results": [],
        "statistics": {}
    }
    
    # Evaluate each response
    for i, test in enumerate(test_responses, 1):
        logger.info(f"[DEMO {i}/{len(test_responses)}] Evaluating...")
        evaluation = evaluate_chatbot_response_demo(test["query"], test["response"], seed=i)
        results["test_results"].append(evaluation)
    
    # Calculate statistics
    if results["test_results"]:
        all_scores = [r["overall_score"] for r in results["test_results"]]
        criterion_scores = {crit: [] for crit in EVALUATION_CRITERIA.keys()}
        
        for result in results["test_results"]:
            for criterion, score_data in result["scores"].items():
                criterion_scores[criterion].append(score_data["score"])
        
        results["statistics"] = {
            "overall": {
                "mean": round(statistics.mean(all_scores), 2),
                "median": round(statistics.median(all_scores), 2),
                "stdev": round(statistics.stdev(all_scores), 2) if len(all_scores) > 1 else 0.0,
                "min": round(min(all_scores), 2),
                "max": round(max(all_scores), 2),
            },
            "by_criterion": {
                crit: {
                    "mean": round(statistics.mean(scores), 2),
                    "median": round(statistics.median(scores), 2),
                    "stdev": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0.0,
                }
                for crit, scores in criterion_scores.items()
            }
        }
    
    # Save results
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {output_file}")
    
    return results


def print_evaluation_report_demo(results: dict) -> None:
    """Pretty print demo evaluation results"""
    print("\n" + "="*80)
    print("CHATBOT EVALUATION REPORT - DEMO MODE")
    print("="*80)
    print("⚠️  NOTICE: Using realistic mock scores (API quota exceeded)")
    print("    Once quota resets, replace with actual LLM evaluation")
    print("="*80)
    
    summary = results["evaluation_summary"]
    print(f"\nEvaluation Timestamp: {summary['timestamp']}")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Mode: {summary['mode']}")
    print(f"Note: {summary['note']}")
    
    # Overall Statistics
    if "statistics" in results and results["statistics"]:
        stats = results["statistics"]["overall"]
        print("\n" + "-"*80)
        print("OVERALL STATISTICS")
        print("-"*80)
        print(f"Mean Score:   {stats['mean']}/5.0")
        print(f"Median Score: {stats['median']}/5.0")
        print(f"Std Dev:      {stats['stdev']}")
        print(f"Min Score:    {stats['min']}/5.0")
        print(f"Max Score:    {stats['max']}/5.0")
        
        # Per-criterion statistics
        print("\n" + "-"*80)
        print("PER-CRITERION STATISTICS")
        print("-"*80)
        for crit, crit_stats in results["statistics"]["by_criterion"].items():
            print(f"\n{crit.upper()}:")
            print(f"  Mean:   {crit_stats['mean']}/5.0")
            print(f"  Median: {crit_stats['median']}/5.0")
            print(f"  Std Dev: {crit_stats['stdev']}")
    
    # Individual test results
    print("\n" + "-"*80)
    print("INDIVIDUAL TEST RESULTS")
    print("-"*80)
    for i, result in enumerate(results["test_results"], 1):
        print(f"\nTest {i}:")
        print(f"Query: {result['query']}")
        print(f"Response: {result['response'][:100]}..." if len(result['response']) > 100 else f"Response: {result['response']}")
        print(f"Overall Score: {result['overall_score']}/5.0")
        print("Criteria Scores:")
        for criterion, score_data in result["scores"].items():
            print(f"  {criterion}: {score_data['score']}/5.0 - {score_data['reasoning']}")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("1. Wait for API quota reset (~1 hour)")
    print("2. Run: python eval_lite_cli.py --mode quick")
    print("3. This will fetch real scores from LLM")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Example usage
    test_responses = [
        {
            "query": "What is machine learning?",
            "response": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It uses algorithms to analyze data, identify patterns, and make decisions based on those patterns."
        },
        {
            "query": "How do neural networks work?",
            "response": "Neural networks are computational systems inspired by biological neural networks. They consist of interconnected nodes (neurons) organized in layers. Data flows through these layers, with each connection having adjustable weights that are updated during training to minimize prediction errors."
        },
        {
            "query": "What is the difference between supervised and unsupervised learning?",
            "response": "Supervised learning trains on labeled data where the correct answers are known, helping the model learn the relationship between inputs and outputs. Unsupervised learning finds patterns in unlabeled data without predefined targets. Supervised is better for specific prediction tasks, while unsupervised excels at exploration and pattern discovery."
        },
    ]
    
    # Create results directory
    results_dir = BASE_DIR / "evaluation_results"
    results_dir.mkdir(exist_ok=True)
    
    # Run demo evaluation
    results = run_evaluation_demo(
        test_responses,
        output_file=results_dir / "demo_results_mock.json"
    )
    
    # Print report
    print_evaluation_report_demo(results)
