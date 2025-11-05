"""
DeepEval evaluation script for the agent.
"""

import json
import os
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from api.agent.agent import get_agent


def evaluate_agent():
    """Run DeepEval evaluation on the agent."""
    
    # Test cases for evaluation
    test_cases = [
        {
            "input": "What are the top 5 leads by potential value?",
            "expected_output": "A list of 5 leads with their potential values",
            "context": "T2SQL query about CRM leads"
        },
        {
            "input": "How many leads are in the database?",
            "expected_output": "A count of leads in the database",
            "context": "T2SQL query about lead count"
        },
        {
            "input": "What are the amenities in the property?",
            "expected_output": "Information about property amenities from brochures",
            "context": "RAG query about property details"
        },
        {
            "input": "Tell me about the location of the project",
            "expected_output": "Location information from project brochures",
            "context": "RAG query about project location"
        },
        {
            "input": "What is the total potential value of all leads?",
            "expected_output": "Sum of all lead potential values",
            "context": "T2SQL query about aggregated data"
        }
    ]
    
    results = []
    agent = get_agent()
    
    for i, test_case in enumerate(test_cases):
        print(f"Evaluating test case {i+1}/{len(test_cases)}: {test_case['input']}")
        
        try:
            # Run agent
            initial_state = {
                "messages": [],
                "query": test_case["input"],
                "query_type": "unknown",
                "response": "",
                "metadata": {}
            }
            
            result = agent.invoke(initial_state)
            actual_output = result.get("response", "")
            query_type = result.get("query_type", "unknown")
            
            # Create test case for DeepEval
            test_case_obj = LLMTestCase(
                input=test_case["input"],
                actual_output=actual_output,
                expected_output=test_case["expected_output"],
                context=test_case["context"]
            )
            
            # Evaluate with Answer Relevancy
            relevancy_metric = AnswerRelevancyMetric(threshold=0.7)
            assert_test(test_case_obj, [relevancy_metric])
            
            # Evaluate with Faithfulness (if applicable)
            faithfulness_metric = FaithfulnessMetric(threshold=0.7)
            assert_test(test_case_obj, [faithfulness_metric])
            
            # Store results
            test_result = {
                "test_case_id": i + 1,
                "input": test_case["input"],
                "expected_output": test_case["expected_output"],
                "actual_output": actual_output,
                "query_type": query_type,
                "relevancy_score": relevancy_metric.score,
                "faithfulness_score": faithfulness_metric.score if hasattr(faithfulness_metric, 'score') else None,
                "status": "passed"
            }
            
        except Exception as e:
            print(f"Error evaluating test case {i+1}: {e}")
            test_result = {
                "test_case_id": i + 1,
                "input": test_case["input"],
                "expected_output": test_case["expected_output"],
                "actual_output": None,
                "query_type": None,
                "error": str(e),
                "status": "failed"
            }
        
        results.append(test_result)
    
    # Calculate overall scores
    passed_tests = [r for r in results if r.get("status") == "passed"]
    total_score = len(passed_tests) / len(results) if results else 0
    
    relevancy_scores = [r.get("relevancy_score", 0) for r in passed_tests if r.get("relevancy_score")]
    avg_relevancy = sum(relevancy_scores) / len(relevancy_scores) if relevancy_scores else 0
    
    # Create evaluation summary
    evaluation_summary = {
        "total_tests": len(results),
        "passed_tests": len(passed_tests),
        "failed_tests": len(results) - len(passed_tests),
        "overall_score": total_score,
        "average_relevancy": avg_relevancy,
        "test_results": results
    }
    
    # Save results to JSON file
    output_file = "agent_evaluation_scores.json"
    with open(output_file, 'w') as f:
        json.dump(evaluation_summary, f, indent=2)
    
    print(f"\nEvaluation complete!")
    print(f"Overall Score: {total_score:.2%}")
    print(f"Average Relevancy: {avg_relevancy:.2f}")
    print(f"Results saved to {output_file}")
    
    return evaluation_summary


if __name__ == "__main__":
    # Set environment variables if needed
    if not os.getenv('GEMINI_API_KEY'):
        print("Warning: GEMINI_API_KEY not set. Some tests may fail.")
    
    evaluate_agent()

