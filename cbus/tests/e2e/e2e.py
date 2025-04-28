"""
End-to-End Tests for the Multi-Agent Financial Analysis System

Run with: pytest -xvs tests/test_e2e.py
"""

import json
import os

# Add parent directory to path to import modules
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.agents import DataAnalystAgent, InsightGeneratorAgent
from src.data.loader import FinancialDataLoader
from src.orchestration.controller import FinancialInsightController


# Fixtures for common test resources
@pytest.fixture
def test_data_path():
    """Path to test data file"""
    # Check if test data exists, if not create a sample data file
    test_data_path = "tests/data/test_financial_sample.xlsx"
    os.makedirs(os.path.dirname(test_data_path), exist_ok=True)

    if not os.path.exists(test_data_path):
        # Create a simple test dataframe
        df = pd.DataFrame(
            {
                "Segment": ["Government", "Enterprise", "Midmarket"] * 2,
                "Country": ["USA", "Canada", "France"] * 2,
                "Product": ["Carretera", "VTT", "Velo"] * 2,
                "Discount Band": ["None", "Low", "Medium"] * 2,
                "Units Sold": [100, 200, 300, 400, 500, 600],
                "Manufacturing Price": [10, 20, 30, 15, 25, 35],
                "Sale Price": [20, 40, 60, 30, 50, 70],
                "Gross Sales": [2000, 8000, 18000, 12000, 25000, 42000],
                "Discounts": [0, 800, 3600, 1200, 5000, 12600],
                "Sales": [2000, 7200, 14400, 10800, 20000, 29400],
                "COGS": [1000, 4000, 9000, 6000, 12500, 21000],
                "Profit": [1000, 3200, 5400, 4800, 7500, 8400],
                "Date": pd.date_range(start="1/1/2023", periods=6),
                "Month Number": [1, 2, 3, 4, 5, 6],
                "Month Name": ["January", "February", "March", "April", "May", "June"],
                "Year": [2023] * 6,
            }
        )

        # Save to Excel
        df.to_excel(test_data_path, index=False)

    return test_data_path


@pytest.fixture
def test_output_dir():
    """Directory for test outputs"""
    output_dir = "tests/output"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing"""

    class MockResponse:
        def __init__(self, content):
            self.content = content

    return MockResponse("This is a mock LLM response for testing purposes.")


# Data Loader Tests
def test_data_loader_initialisation(test_data_path):
    """Test that the data loader initialises correctly"""
    loader = FinancialDataLoader(test_data_path)
    assert loader.file_path == test_data_path
    assert loader.data is None
    assert loader.summary_stats == {}


def test_data_loader_load_data(test_data_path):
    """Test that the data loader can load data correctly"""
    loader = FinancialDataLoader(test_data_path)
    df = loader.load_data()

    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "Segment" in df.columns
    assert "Profit" in df.columns
    assert loader.data is not None


def test_data_loader_get_summary_statistics(test_data_path):
    """Test that the data loader can generate summary statistics"""
    loader = FinancialDataLoader(test_data_path)
    stats = loader.get_summary_statistics()

    assert stats is not None
    assert isinstance(stats, dict)
    assert "row_count" in stats
    assert "segment_analysis" in stats
    assert "country_analysis" in stats
    assert len(stats["segment_analysis"]) > 0


def test_data_loader_save_summary(test_data_path, test_output_dir):
    """Test that the data loader can save summary statistics to a file"""
    loader = FinancialDataLoader(test_data_path)
    output_path = os.path.join(test_output_dir, "test_summary.json")

    saved_path = loader.save_summary_to_json(output_path)

    assert saved_path == output_path
    assert os.path.exists(output_path)

    # Verify JSON can be loaded
    with open(output_path, "r") as f:
        loaded_stats = json.load(f)

    assert loaded_stats is not None
    assert isinstance(loaded_stats, dict)
    assert "segment_analysis" in loaded_stats


# Agent Tests with Mocked LLM
@patch("langchain.chat_models.ChatOpenAI")
def test_data_analyst_agent(mock_chat, test_data_path, mock_llm_response):
    """Test that the Data Analyst Agent functions correctly"""
    # Configure mock
    mock_instance = MagicMock()
    mock_instance.return_value = mock_llm_response
    mock_chat.return_value = mock_instance

    # Create agent with mocked LLM
    loader = FinancialDataLoader(test_data_path)
    loader.load_data()
    summary = loader.get_summary_statistics()

    agent = DataAnalystAgent(data_loader=loader)

    # Test analysis function
    result = agent.analyze("Test analysis task", summary)
    assert result is not None
    assert isinstance(result, str)

    # Test hypothesis testing function
    result = agent.test_hypothesis("Test hypothesis", summary)
    assert result is not None
    assert isinstance(result, str)


@patch("langchain.chat_models.ChatOpenAI")
def test_insight_generator_agent(mock_chat, mock_llm_response):
    """Test that the Insight Generator Agent functions correctly"""
    # Configure mock
    mock_instance = MagicMock()
    mock_instance.return_value = mock_llm_response
    mock_chat.return_value = mock_instance

    # Create agent with mocked LLM
    agent = InsightGeneratorAgent()

    # Test generate insights function
    result = agent.generate_insights("Test insight task", "Test analysis results")
    assert result is not None
    assert isinstance(result, str)

    # Test generate hypotheses function
    result = agent.generate_hypotheses({"test": "data"})
    assert result is not None
    assert isinstance(result, str)


# Controller Tests with Mocked Agents
class MockController(FinancialInsightController):
    """Mock controller that overrides agent methods to avoid actual LLM calls"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run_initial_analysis(self):
        """Mock implementation"""
        analysis = "This is a mock initial analysis result."
        with open(f"{self.output_dir}/initial_analysis.txt", "w") as f:
            f.write(analysis)
        return analysis

    def generate_hypotheses(self, analysis_results):
        """Mock implementation"""
        hypotheses = "Hypothesis 1: This is a mock hypothesis.\nHypothesis 2: This is another mock hypothesis."
        with open(f"{self.output_dir}/hypotheses.txt", "w") as f:
            f.write(hypotheses)
        return hypotheses

    def test_hypotheses(self, hypotheses):
        """Mock implementation"""
        results = [
            {
                "hypothesis": "Hypothesis 1: This is a mock hypothesis.",
                "result": "Testing result 1: The hypothesis is supported by the data.",
            },
            {
                "hypothesis": "Hypothesis 2: This is another mock hypothesis.",
                "result": "Testing result 2: The hypothesis is partially supported by the data.",
            },
        ]

        for i, result in enumerate(results):
            with open(f"{self.output_dir}/hypothesis_test_{i+1}.txt", "w") as f:
                f.write(
                    f"HYPOTHESIS:\n{result['hypothesis']}\n\nRESULT:\n{result['result']}"
                )

        return results

    def synthesize_insights(self, testing_results):
        """Mock implementation"""
        insights = "Insight 1: This is a mock insight based on hypothesis testing.\nInsight 2: This is another mock insight."
        with open(f"{self.output_dir}/synthesized_insights.txt", "w") as f:
            f.write(insights)
        return insights

    def run_q_and_a(self, question):
        """Mock implementation"""
        return f"Mock answer to: {question}"


def test_controller_initialisation(test_data_path, test_output_dir):
    """Test that the controller initialises correctly"""
    controller = MockController(
        data_path=test_data_path, output_dir=test_output_dir, streaming=False
    )

    assert controller.data_path == test_data_path
    assert controller.output_dir == test_output_dir
    assert controller.data is not None
    assert controller.data_summary is not None
    assert os.path.exists(f"{test_output_dir}/data_summary.json")


def test_controller_run_full_insight_discovery(test_data_path, test_output_dir):
    """Test the full insight discovery process"""
    controller = MockController(
        data_path=test_data_path, output_dir=test_output_dir, streaming=False
    )

    insights = controller.run_full_insight_discovery()

    assert insights is not None
    assert isinstance(insights, str)
    assert os.path.exists(f"{test_output_dir}/initial_analysis.txt")
    assert os.path.exists(f"{test_output_dir}/hypotheses.txt")
    assert os.path.exists(f"{test_output_dir}/hypothesis_test_1.txt")
    assert os.path.exists(f"{test_output_dir}/synthesized_insights.txt")
    assert os.path.exists(f"{test_output_dir}/interaction_log.json")


def test_controller_qa_functionality(test_data_path, test_output_dir):
    """Test the Q&A functionality"""
    controller = MockController(
        data_path=test_data_path, output_dir=test_output_dir, streaming=False
    )

    question = "Which segment has the highest profit margin?"
    answer = controller.run_q_and_a(question)

    assert answer is not None
    assert isinstance(answer, str)
    assert question in answer  # Our mock simply echoes the question


# Integration test with mocked LLM responses
@patch("src.agents.agents.ChatOpenAI")
def test_integration_specific_analysis(
    mock_chat, test_data_path, test_output_dir, mock_llm_response
):
    """Test specific analysis functionality with integration between components"""
    # Configure mock
    mock_instance = MagicMock()
    mock_instance.return_value = mock_llm_response
    mock_chat.return_value = mock_instance

    controller = MockController(
        data_path=test_data_path, output_dir=test_output_dir, streaming=False
    )

    # Test segment analysis
    segment_result = controller.run_specific_analysis("segment", "Government")
    assert segment_result is not None
    assert isinstance(segment_result, dict)

    # Test generating insights for the analysis
    if "error" not in segment_result:
        insights = controller.generate_insights_for_analysis(segment_result, "segment")
        assert insights is not None
        assert isinstance(insights, str)


# Main test function that runs the full system with mocks
def test_full_system_with_mocks(test_data_path, test_output_dir):
    """Test the full system with mocked components"""
    # Create controller with mocked agents
    controller = MockController(
        data_path=test_data_path, output_dir=test_output_dir, streaming=False
    )

    # Run full insight discovery
    insights = controller.run_full_insight_discovery()
    assert insights is not None

    # Verify that all expected output files exist
    expected_files = [
        "data_summary.json",
        "initial_analysis.txt",
        "hypotheses.txt",
        "synthesized_insights.txt",
        "interaction_log.json",
    ]

    for file in expected_files:
        assert os.path.exists(os.path.join(test_output_dir, file))

    # Test Q&A functionality
    answer = controller.run_q_and_a("What is the most profitable segment?")
    assert answer is not None


if __name__ == "__main__":
    # Run the tests manually if needed
    pytest.main(["-xvs", __file__])
