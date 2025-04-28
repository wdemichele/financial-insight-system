"""
Integration Tests for the Multi-Agent Financial Analysis System

These tests simulate a complete end-to-end workflow using mocked LLM responses.
"""

import json
import os
import sys
from unittest.mock import patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.agents import DataAnalystAgent, InsightGeneratorAgent
from src.data.loader import FinancialDataLoader
from src.orchestration.controller import FinancialInsightController


@patch("langchain.chat_models.ChatOpenAI")
def test_full_insight_discovery_workflow(
    mock_chat, test_data_path, test_output_dir, mock_openai_response
):
    """Test the complete insight discovery workflow with mocked LLM responses"""
    # Setup mock
    mock_chat.return_value = mock_openai_response

    # Initialise controller
    controller = FinancialInsightController(
        data_path=test_data_path, output_dir=test_output_dir, streaming=False
    )

    # Run the full process
    insights = controller.run_full_insight_discovery()

    # Verify output files were created
    assert os.path.exists(os.path.join(test_output_dir, "data_summary.json"))
    assert os.path.exists(os.path.join(test_output_dir, "initial_analysis.txt"))
    assert os.path.exists(os.path.join(test_output_dir, "hypotheses.txt"))
    assert os.path.exists(os.path.join(test_output_dir, "interaction_log.json"))

    # At least one hypothesis test file should exist
    hypothesis_files = [
        f for f in os.listdir(test_output_dir) if f.startswith("hypothesis_test_")
    ]
    assert len(hypothesis_files) > 0

    # Final insights file should exist
    assert os.path.exists(os.path.join(test_output_dir, "synthesized_insights.txt"))

    # Verify insights content
    assert insights is not None
    assert isinstance(insights, str)
    assert "Insight" in insights
    assert "Enterprise" in insights  # Based on our mock data


@patch("langchain.chat_models.ChatOpenAI")
def test_data_analyst_specific_analysis(
    mock_chat, test_data_path, test_output_dir, mock_openai_response
):
    """Test the Data Analyst Agent's specific analysis capabilities"""
    # Setup mock
    mock_chat.return_value = mock_openai_response

    # Create data loader
    loader = FinancialDataLoader(test_data_path)
    loader.load_data()

    # Create analyst agent
    analyst = DataAnalystAgent(data_loader=loader, streaming=False)

    # Test segment analysis
    segment_result = analyst.analyze_specific_segment("Enterprise")
    assert segment_result is not None
    assert isinstance(segment_result, dict)
    assert "segment_name" in segment_result
    assert segment_result["segment_name"] == "Enterprise"

    # Test product analysis
    product_result = analyst.analyze_specific_product("VTT")
    assert product_result is not None
    assert isinstance(product_result, dict)
    assert "product_name" in product_result
    assert product_result["product_name"] == "VTT"

    # Test discount impact analysis
    discount_result = analyst.analyze_discount_impact()
    assert discount_result is not None
    assert isinstance(discount_result, dict)
    assert "discount_band_analysis" in discount_result


@patch("langchain.chat_models.ChatOpenAI")
def test_q_and_a_functionality(
    mock_chat, test_data_path, test_output_dir, mock_openai_response
):
    """Test the Q&A functionality of the system"""
    # Setup mock
    mock_chat.return_value = mock_openai_response

    # Initialise controller
    controller = FinancialInsightController(
        data_path=test_data_path, output_dir=test_output_dir, streaming=False
    )

    # Ask an analytical question
    analytical_q = "What is the profit margin for each segment?"
    analytical_answer = controller.run_q_and_a(analytical_q)
    assert analytical_answer is not None
    assert isinstance(analytical_answer, str)
    assert (
        "profit margin" in analytical_answer.lower()
        or "segment" in analytical_answer.lower()
    )

    # Ask an insight-oriented question
    insight_q = "Which segment should we focus on improving and why?"
    insight_answer = controller.run_q_and_a(insight_q)
    assert insight_answer is not None
    assert isinstance(insight_answer, str)
    assert (
        "enterprise" in insight_answer.lower()
        or "channel partners" in insight_answer.lower()
    )


@patch("langchain.chat_models.ChatOpenAI")
def test_specific_analysis_with_insights(
    mock_chat, test_data_path, test_output_dir, mock_openai_response
):
    """Test running a specific analysis and generating insights from it"""
    # Setup mock
    mock_chat.return_value = mock_openai_response

    # Initialise controller
    controller = FinancialInsightController(
        data_path=test_data_path, output_dir=test_output_dir, streaming=False
    )

    # Run specific analysis
    discount_analysis = controller.run_specific_analysis("discount")
    assert discount_analysis is not None
    assert isinstance(discount_analysis, dict)

    # Generate insights from the analysis
    insights = controller.generate_insights_for_analysis(discount_analysis, "discount")
    assert insights is not None
    assert isinstance(insights, str)
    assert "discount" in insights.lower() or "margin" in insights.lower()


@patch("langchain.chat_models.ChatOpenAI")
def test_log_and_audit_functionality(
    mock_chat, test_data_path, test_output_dir, mock_openai_response
):
    """Test the logging and auditing capabilities"""
    # Setup mock
    mock_chat.return_value = mock_openai_response

    # Initialise controller with logging enabled
    controller = FinancialInsightController(
        data_path=test_data_path,
        output_dir=test_output_dir,
        log_interactions=True,
        streaming=False,
    )

    # Generate some interactions
    controller.run_initial_analysis()
    controller.run_q_and_a("What is the most profitable segment?")

    # Save and check log
    log_path = controller.save_interaction_log()
    assert log_path is not None
    assert os.path.exists(log_path)

    # Verify log content
    with open(log_path, "r") as f:
        log_data = json.load(f)

    assert isinstance(log_data, list)
    assert len(log_data) >= 2  # At least two interactions

    # Check log structure
    for entry in log_data:
        assert "timestamp" in entry
        assert "agent" in entry
        assert "input" in entry
        assert "output" in entry


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
