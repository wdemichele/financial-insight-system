"""
Orchestration Controller for Financial Analysis System

This module manages the coordination between the Data Analyst and Insight Generator agents.
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.agents.agents import (
    DataAnalystAgent,
    HypothesisGeneratorAgent,
    InsightGeneratorAgent,
)
from src.data.loader import FinancialDataLoader


class FinancialInsightController:
    """
    Controller for orchestrating the multi-agent financial insight discovery system.
    """

    def __init__(
        self,
        data_path: str,
        output_dir: str = "output",
        analyst_deployment: str = "gpt-4o",
        insight_deployment: str = "gpt-4o",
        log_interactions: bool = True,
        streaming: bool = True,
    ):
        """
        Initialise the Financial Insight Controller.

        Args:
            data_path: Path to the financial data file
            output_dir: Directory for output files
            analyst_deployment: Azure OpenAI deployment name for the Data Analyst Agent
            insight_deployment: Azure OpenAI deployment name for the Insight Generator Agent
            log_interactions: Whether to log agent interactions
            streaming: Whether to stream agent outputs
        """
        self.data_path = data_path
        self.output_dir = output_dir
        self.log_interactions = log_interactions

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Initialise data loader
        self.data_loader = FinancialDataLoader(data_path)

        # Load the data and generate summary statistics
        self.data = self.data_loader.load_data()
        self.data_summary = self.data_loader.get_summary_statistics()

        # Save summary statistics
        self.data_loader.save_summary_to_json(f"{output_dir}/data_summary.json")

        # Initialise agents
        self.analyst_agent = DataAnalystAgent(
            deployment_name=analyst_deployment,
            temperature=0.1,
            streaming=streaming,
            data_loader=self.data_loader,
        )

        self.hypothesis_agent = HypothesisGeneratorAgent(
            deployment_name=analyst_deployment,
            temperature=0.7,  # Higher temperature for creative hypothesis generation
            streaming=streaming,
        )

        self.insight_agent = InsightGeneratorAgent(
            deployment_name=insight_deployment, temperature=0.4, streaming=streaming
        )

        # Initialise interaction log
        self.interaction_log = []

    def log_interaction(self, agent: str, input_data: Any, output_data: Any) -> None:
        """
        Log an agent interaction.

        Args:
            agent: Name of the agent
            input_data: Input data for the agent
            output_data: Output data from the agent
        """
        if not self.log_interactions:
            return

        interaction = {
            "timestamp": time.time(),
            "agent": agent,
            "input": input_data,
            "output": output_data,
        }

        self.interaction_log.append(interaction)

    def save_interaction_log(self) -> str:
        """
        Save the interaction log to a file.

        Returns:
            Path to the saved log file
        """
        if not self.interaction_log:
            return None

        log_path = f"{self.output_dir}/interaction_log.json"

        with open(log_path, "w") as f:
            json.dump(self.interaction_log, f, indent=2)

        return log_path

    def run_initial_analysis(self) -> str:
        """
        Run initial exploratory analysis of the financial data.

        Returns:
            Analysis results as a string
        """
        # Define the initial analysis task
        task = """
        Perform an initial exploratory analysis of the financial dataset. 
        Identify the most significant patterns, trends, or anomalies in the data.
        Focus on:
        1. Differences in performance across segments
        2. Patterns in profit margins
        3. Notable country-specific trends
        4. Product performance variations
        5. The relationship between discounts and profitability
        """

        # Run the analysis
        analysis_results = self.analyst_agent.analyze(task, self.data_summary)

        # Log the interaction
        self.log_interaction("DataAnalystAgent", task, analysis_results)

        # Save the results
        with open(f"{self.output_dir}/initial_analysis.txt", "w") as f:
            f.write(analysis_results)

        return analysis_results

    def generate_hypotheses(self, analysis_results: str) -> List[Dict[str, Any]]:
        """
        Generate hypotheses based on initial analysis using the dedicated Hypothesis Generator.

        Args:
            analysis_results: Results from initial analysis

        Returns:
            List of generated hypotheses with additional metadata
        """
        # Generate hypotheses using the dedicated hypothesis agent
        hypotheses = self.hypothesis_agent.generate_hypotheses(
            data_summary=self.data_summary, initial_analysis=analysis_results
        )

        # Log the interaction
        self.log_interaction(
            "HypothesisGeneratorAgent",
            {"data_summary": self.data_summary, "initial_analysis": analysis_results},
            hypotheses,
        )

        # Save the results
        with open(f"{self.output_dir}/hypotheses.json", "w") as f:
            json.dump(hypotheses, f, indent=2)

        # Also save a more readable text version
        with open(f"{self.output_dir}/hypotheses.txt", "w") as f:
            for i, hypothesis in enumerate(hypotheses, 1):
                f.write(f"HYPOTHESIS {i}:\n")
                f.write(f"{hypothesis['hypothesis']}\n\n")
                f.write(f"RATIONALE:\n{hypothesis['rationale']}\n\n")
                f.write(f"TEST APPROACH:\n{hypothesis['test_approach']}\n\n")
                f.write(f"BUSINESS IMPACT:\n{hypothesis['business_impact']}\n\n")
                f.write("-" * 80 + "\n\n")

        return hypotheses

    def full_hypothesis_workflow(self) -> str:
        """
        Run the complete hypothesis workflow from initial analysis to final insights.

        Returns:
            Final insights as a string
        """
        print("Starting the hypothesis workflow...")

        # Step 1: Initial Analysis
        print("\n=== Running Initial Analysis ===")
        analysis_results = self.run_initial_analysis()

        # Step 2: Generate Hypotheses
        print("\n=== Generating Hypotheses ===")
        hypotheses = self.generate_hypotheses(analysis_results)

        # Step 3: Parse Hypotheses
        print("\n=== Parsing Hypotheses ===")
        structured_hypotheses = self.parse_hypotheses(hypotheses)

        # Step 4: Test Hypotheses
        print("\n=== Testing Hypotheses ===")
        testing_results = []
        for hypothesis in structured_hypotheses:
            print(f"Testing hypothesis: {hypothesis['title']}")
            result = self.analyst_agent.test_hypothesis(
                hypothesis["description"], self.data_summary
            )
            testing_results.append({"hypothesis": hypothesis, "result": result})

        # Step 5: Synthesize Insights
        print("\n=== Synthesizing Insights ===")
        combined_results = self.format_hypothesis_results(testing_results)
        insights = self.insight_agent.synthesize_insights(
            combined_results, self.data_summary
        )

        # Save results
        with open(f"{self.output_dir}/final_insights.txt", "w") as f:
            f.write(insights)

        print("\n=== Hypothesis Workflow Complete ===")
        return insights

    def parse_hypotheses(self, hypotheses_text: str) -> List[Dict[str, Any]]:
        """
        Parse raw hypotheses text into structured format.

        Args:
            hypotheses_text: Raw text containing hypotheses

        Returns:
            List of structured hypothesis objects
        """
        # This is a simplified implementation - in production, you would want more robust parsing
        structured_hypotheses = []
        hypothesis_sections = hypotheses_text.split("Hypothesis")

        # Skip the first section if it doesn't contain a hypothesis
        start_idx = 0 if hypothesis_sections[0].strip() else 1

        for i, section in enumerate(hypothesis_sections[start_idx:], 1):
            # Clean up the section
            section = section.strip()
            if not section:
                continue

            # Try to extract a title from the first line
            lines = section.split("\n")
            title_line = lines[0].strip()

            # Remove any leading numbers or special characters
            title = re.sub(r"^[0-9.:\-]*\s*", "", title_line)

            # Default values
            importance = "Medium"
            confidence = "Medium"

            # Check for importance indicators
            if "high importance" in section.lower() or "critical" in section.lower():
                importance = "High"
            elif "low importance" in section.lower() or "minor" in section.lower():
                importance = "Low"

            # Check for confidence indicators
            if (
                "high confidence" in section.lower()
                or "strong evidence" in section.lower()
            ):
                confidence = "High"
            elif "low confidence" in section.lower() or "tentative" in section.lower():
                confidence = "Low"

            structured_hypotheses.append(
                {
                    "id": f"hyp_{i}",
                    "title": title,
                    "description": section,
                    "importance": importance,
                    "confidence": confidence,
                }
            )

        return structured_hypotheses

    def format_hypothesis_results(self, testing_results: List[Dict[str, Any]]) -> str:
        """
        Format tested hypotheses for synthesis.

        Args:
            testing_results: List of testing result objects

        Returns:
            Formatted string for synthesis
        """
        result = []

        for i, item in enumerate(testing_results, 1):
            hypothesis = item["hypothesis"]
            test_result = item["result"]

            result.append(
                f"HYPOTHESIS {i}:\n{hypothesis['description']}\n\nTEST RESULT:\n{test_result}\n\n"
            )

        return "\n".join(result)

    def test_hypotheses(self, hypotheses: str) -> List[Dict[str, str]]:
        """
        Test the generated hypotheses.

        Args:
            hypotheses: String containing hypotheses

        Returns:
            List of dictionaries with hypothesis testing results
        """
        # Extract individual hypotheses from the text
        # This is a simplified approach; in a production system,
        # you would want more robust parsing
        hypothesis_sections = hypotheses.split("Hypothesis")

        # Remove any empty sections
        hypothesis_sections = [
            section.strip() for section in hypothesis_sections if section.strip()
        ]

        # Test each hypothesis
        testing_results = []

        for i, section in enumerate(hypothesis_sections):
            # Clean up the hypothesis text
            hypothesis_text = f"Hypothesis: {section}"

            # Test the hypothesis
            result = self.analyst_agent.test_hypothesis(
                hypothesis_text, self.data_summary
            )

            # Log the interaction
            self.log_interaction("DataAnalystAgent", hypothesis_text, result)

            # Add to results
            testing_results.append({"hypothesis": hypothesis_text, "result": result})

            # Save individual result
            with open(f"{self.output_dir}/hypothesis_test_{i+1}.txt", "w") as f:
                f.write(f"HYPOTHESIS:\n{hypothesis_text}\n\nRESULT:\n{result}")

        return testing_results

    def synthesize_insights(self, testing_results: List[Dict[str, str]]) -> str:
        """
        Synthesize insights from hypothesis testing results.

        Args:
            testing_results: List of hypothesis testing results

        Returns:
            Synthesized insights as a string
        """
        # Combine all hypothesis testing results into a single text
        combined_results = "\n\n".join(
            [
                f"HYPOTHESIS {i+1}:\n{result['hypothesis']}\n\nTEST RESULT:\n{result['result']}"
                for i, result in enumerate(testing_results)
            ]
        )

        # Synthesize insights
        insights = self.insight_agent.synthesize_insights(
            combined_results, self.data_summary
        )

        # Log the interaction
        self.log_interaction("InsightGeneratorAgent", combined_results, insights)

        # Save the results
        with open(f"{self.output_dir}/synthesized_insights.txt", "w") as f:
            f.write(insights)

        return insights

    def run_full_insight_discovery(self) -> str:
        """
        Run the complete insight discovery process.

        Returns:
            Final insights as a string
        """
        print("Starting the financial insight discovery process...")

        # Step 1: Initial Analysis
        print("\n=== Running Initial Analysis ===")
        analysis_results = self.run_initial_analysis()

        # Step 2: Generate Hypotheses
        print("\n=== Generating Hypotheses ===")
        hypotheses = self.generate_hypotheses(analysis_results)

        # Step 3: Test Hypotheses
        print("\n=== Testing Hypotheses ===")
        testing_results = self.test_hypotheses(hypotheses)

        # Step 4: Synthesize Insights
        print("\n=== Synthesizing Insights ===")
        insights = self.synthesize_insights(testing_results)

        # Step 5: Save all interaction logs
        self.save_interaction_log()

        print("\n=== Insight Discovery Complete ===")
        return insights

    def run_specific_analysis(
        self, analysis_type: str, parameter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a specific type of analysis.

        Args:
            analysis_type: Type of analysis to run ("segment", "product", "discount")
            parameter: Optional parameter for the analysis (e.g., segment name)

        Returns:
            Analysis results as a dictionary
        """
        if analysis_type == "segment" and parameter:
            result = self.analyst_agent.analyze_specific_segment(parameter)
            self.log_interaction(
                "DataAnalystAgent", f"Analyze segment: {parameter}", result
            )
            return result

        elif analysis_type == "product" and parameter:
            result = self.analyst_agent.analyze_specific_product(parameter)
            self.log_interaction(
                "DataAnalystAgent", f"Analyze product: {parameter}", result
            )
            return result

        elif analysis_type == "discount":
            result = self.analyst_agent.analyze_discount_impact()
            self.log_interaction("DataAnalystAgent", "Analyze discount impact", result)
            return result

        else:
            raise ValueError(f"Invalid analysis type: {analysis_type}")

    def generate_insights_for_analysis(
        self, analysis_result: Dict[str, Any], analysis_type: str
    ) -> str:
        """
        Generate insights for a specific analysis result.

        Args:
            analysis_result: Analysis result dictionary
            analysis_type: Type of analysis that was performed

        Returns:
            Generated insights as a string
        """
        # Convert analysis result to string
        analysis_str = json.dumps(analysis_result, indent=2)

        # Define task based on analysis type
        if analysis_type == "segment":
            task = f"Generate insights about the {analysis_result.get('segment_name', 'specified')} segment, focusing on profitability drivers and performance patterns."
        elif analysis_type == "product":
            task = f"Generate insights about the {analysis_result.get('product_name', 'specified')} product, focusing on its performance across segments and countries."
        elif analysis_type == "discount":
            task = "Generate insights about the impact of discounts on profitability, focusing on optimal discount strategies for different segments."
        else:
            task = "Generate insights from the provided analysis, focusing on business implications and actionable recommendations."

        # Generate insights
        insights = self.insight_agent.generate_insights(task, analysis_str)

        # Log the interaction
        self.log_interaction(
            "InsightGeneratorAgent", {"task": task, "analysis": analysis_str}, insights
        )

        return insights

    def run_q_and_a(self, question: str) -> str:
        """
        Run a Q&A interaction with the system.

        Args:
            question: User's question about the financial data

        Returns:
            Answer to the question
        """
        # Determine which agent should handle the question
        if any(
            keyword in question.lower()
            for keyword in [
                "why",
                "insight",
                "reason",
                "implication",
                "suggest",
                "recommend",
                "strategy",
            ]
        ):
            # Insight-oriented question, send to Insight Generator
            task = f"Answer the following question about the financial data: {question}"

            # Include both the question and data summary
            enhanced_summary = {"question": question, "data_summary": self.data_summary}

            # Convert to string for the agent
            enhanced_summary_str = json.dumps(enhanced_summary, indent=2)

            # Get answer from Insight Generator
            answer = self.insight_agent.generate_insights(task, enhanced_summary_str)

            # Log the interaction
            self.log_interaction(
                "InsightGeneratorAgent",
                {"task": task, "data": enhanced_summary},
                answer,
            )

        elif any(
            keyword in question.lower()
            for keyword in ["hypothesis", "hunch", "theory", "conjecture", "test"]
        ):
            # Hypothesis-oriented question, send to Hypothesis Generator then test with Analyst

            # First generate a hypothesis
            hypotheses = self.hypothesis_agent.generate_hypotheses(
                data_summary=self.data_summary,
                initial_analysis=f"User question: {question}",
            )

            # Log the interaction
            self.log_interaction(
                "HypothesisGeneratorAgent",
                {"data_summary": self.data_summary, "question": question},
                hypotheses,
            )

            # Test the first hypothesis
            if hypotheses:
                hypothesis_text = hypotheses[0]["hypothesis"]
                test_result = self.analyst_agent.test_hypothesis(
                    hypothesis_text, self.data_summary
                )

                # Log the interaction
                self.log_interaction("DataAnalystAgent", hypothesis_text, test_result)

                # Synthesize answer
                answer = f"Based on your question, I've generated and tested a hypothesis:\n\n"
                answer += f"**Hypothesis**: {hypothesis_text}\n\n"
                answer += f"**Analysis Results**:\n{test_result}\n\n"

                if len(hypotheses) > 1:
                    answer += "I also considered these additional hypotheses:\n\n"
                    for i, h in enumerate(hypotheses[1:], 2):
                        answer += f"{i}. {h['hypothesis']}\n"
            else:
                # Fallback to analyst if no hypotheses generated
                answer = self.analyst_agent.analyze(
                    f"Answer this question: {question}", self.data_summary
                )

        else:
            # Analysis-oriented question, send to Data Analyst
            task = f"Answer the following question about the financial data: {question}"

            # Get answer from Data Analyst
            answer = self.analyst_agent.analyze(task, self.data_summary)

            # Log the interaction
            self.log_interaction(
                "DataAnalystAgent",
                {"task": task, "data_summary": self.data_summary},
                answer,
            )

        return answer
