"""
Agent Implementations for Financial Analysis System

This module defines the Data Analyst and Insight Generator agents using LangChain with Azure OpenAI.
"""

import json
import os
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI

from src.agents.prompts import (
    DATA_ANALYST_SYSTEM_PROMPT,
    INSIGHT_GENERATOR_SYSTEM_PROMPT,
    get_analyst_prompt_with_task,
    get_hypothesis_generation_prompt,
    get_hypothesis_testing_prompt,
    get_insight_prompt_with_task,
    get_insight_synthesis_prompt,
)
from src.data.loader import FinancialDataLoader


class DataAnalystAgent:
    """
    Agent responsible for analyzing financial data and identifying patterns.
    """

    def __init__(
        self,
        deployment_name: str = "gpt-4o",
        temperature: float = 0.0,
        streaming: bool = True,
        data_loader: Optional[FinancialDataLoader] = None,
    ):
        """
        Initialise the Data Analyst Agent.

        Args:
            deployment_name: Name of the Azure OpenAI deployment
            temperature: Temperature parameter for the LLM
            streaming: Whether to stream output
            data_loader: Optional FinancialDataLoader instance
        """

        # Get Azure OpenAI configuration from environment variables
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")

        if not azure_endpoint or not azure_api_key:
            raise ValueError(
                "Azure OpenAI credentials not found in environment variables"
            )

        self.llm = AzureChatOpenAI(
            azure_deployment=deployment_name,
            openai_api_version=api_version,
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            temperature=temperature,
            streaming=streaming,
        )

        self.data_loader = data_loader

    def analyze(self, task: str, data_summary: Dict[str, Any]) -> str:
        """
        Perform a specific analysis task.

        Args:
            task: Description of the analysis task
            data_summary: Dictionary containing data summary

        Returns:
            Analysis results as a string
        """
        # Create the prompt
        prompt = get_analyst_prompt_with_task(task, data_summary)

        # Call the LLM
        messages = [
            SystemMessage(content=DATA_ANALYST_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        response = self.llm(messages)
        return response.content

    def test_hypothesis(self, hypothesis: str, data_summary: Dict[str, Any]) -> str:
        """
        Test a specific hypothesis against the data.

        Args:
            hypothesis: The hypothesis to test
            data_summary: Dictionary containing data summary

        Returns:
            Hypothesis testing results as a string
        """
        # Create the prompt
        prompt = get_hypothesis_testing_prompt(hypothesis, data_summary)

        # Call the LLM
        messages = [
            SystemMessage(content=DATA_ANALYST_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        response = self.llm(messages)
        return response.content

    def analyze_specific_segment(self, segment_name: str) -> Dict[str, Any]:
        """
        Analyze a specific segment in detail.

        Args:
            segment_name: Name of the segment to analyze

        Returns:
            Dictionary with detailed segment analysis
        """
        if self.data_loader is None:
            raise ValueError("Data loader is required for segment analysis")

        return self.data_loader.analyze_segment(segment_name)

    def analyze_specific_product(self, product_name: str) -> Dict[str, Any]:
        """
        Analyze a specific product in detail.

        Args:
            product_name: Name of the product to analyze

        Returns:
            Dictionary with detailed product analysis
        """
        if self.data_loader is None:
            raise ValueError("Data loader is required for product analysis")

        return self.data_loader.analyze_product(product_name)

    def analyze_discount_impact(self) -> Dict[str, Any]:
        """
        Analyze the impact of discounts on profit margins.

        Returns:
            Dictionary with discount impact analysis
        """
        if self.data_loader is None:
            raise ValueError("Data loader is required for discount analysis")

        return self.data_loader.analyze_discount_impact()


class InsightGeneratorAgent:
    """
    Agent responsible for generating insights from financial analysis.
    """

    def __init__(
        self,
        deployment_name: str = "gpt-4o",
        temperature: float = 0.2,
        streaming: bool = True,
    ):
        """
        Initialise the Insight Generator Agent.

        Args:
            deployment_name: Name of the Azure OpenAI deployment
            temperature: Temperature parameter for the LLM
            streaming: Whether to stream output
        """
        # Get Azure OpenAI configuration from environment variables
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")

        if not azure_endpoint or not azure_api_key:
            raise ValueError(
                "Azure OpenAI credentials not found in environment variables"
            )

        self.llm = AzureChatOpenAI(
            azure_deployment=deployment_name,
            openai_api_version=api_version,
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            temperature=temperature,
            streaming=streaming,
        )

    def generate_insights(self, task: str, analysis_results: str) -> str:
        """
        Generate insights based on analysis results.

        Args:
            task: Description of the insight generation task
            analysis_results: String containing analysis results

        Returns:
            Generated insights as a string
        """
        # Create the prompt
        prompt = get_insight_prompt_with_task(task, analysis_results)

        # Call the LLM
        messages = [
            SystemMessage(content=INSIGHT_GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        response = self.llm(messages)
        return response.content

    def generate_hypotheses(self, data_summary: Dict[str, Any]) -> str:
        """
        Generate hypotheses based on data summary.

        Args:
            data_summary: Dictionary containing data summary

        Returns:
            Generated hypotheses as a string
        """
        # Create the prompt
        prompt = get_hypothesis_generation_prompt(data_summary)

        # Call the LLM
        messages = [
            SystemMessage(content=INSIGHT_GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        response = self.llm(messages)
        return response.content

    def synthesize_insights(
        self, hypothesis_results: str, data_summary: Dict[str, Any]
    ) -> str:
        """
        Synthesize insights from hypothesis testing results.

        Args:
            hypothesis_results: String containing hypothesis testing results
            data_summary: Dictionary containing data summary

        Returns:
            Synthesized insights as a string
        """
        # Create the prompt
        prompt = get_insight_synthesis_prompt(hypothesis_results, data_summary)

        # Call the LLM
        messages = [
            SystemMessage(content=INSIGHT_GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        response = self.llm(messages)
        return response.content


def create_data_analyst_agent_with_tools(
    deployment_name: str = "gpt-4o",
    temperature: float = 0.0,
    streaming: bool = True,
    data_loader: FinancialDataLoader = None,
) -> AgentExecutor:
    """
    Create a Data Analyst Agent with tools using LangChain's Agent framework.

    Args:
        deployment_name: Name of the Azure OpenAI deployment
        temperature: Temperature parameter for the LLM
        streaming: Whether to stream output
        data_loader: FinancialDataLoader instance

    Returns:
        AgentExecutor for the Data Analyst Agent
    """
    # Get Azure OpenAI configuration from environment variables
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")

    if not azure_endpoint or not azure_api_key:
        raise ValueError("Azure OpenAI credentials not found in environment variables")

    # Setup the LLM
    llm = AzureChatOpenAI(
        azure_deployment=deployment_name,
        openai_api_version=api_version,
        azure_endpoint=azure_endpoint,
        api_key=azure_api_key,
        temperature=temperature,
        streaming=streaming,
    )

    # Define tools that the agent can use
    tools = [
        Tool(
            name="AnalyzeSegment",
            func=lambda segment_name: json.dumps(
                data_loader.analyze_segment(segment_name), indent=2
            ),
            description="Analyze a specific segment in detail. Input should be the exact segment name (e.g., 'Government', 'Enterprise').",
        ),
        Tool(
            name="AnalyzeProduct",
            func=lambda product_name: json.dumps(
                data_loader.analyze_product(product_name), indent=2
            ),
            description="Analyze a specific product in detail. Input should be the exact product name (e.g., 'Carretera', 'VTT').",
        ),
        Tool(
            name="AnalyzeDiscountImpact",
            func=lambda _: json.dumps(data_loader.analyze_discount_impact(), indent=2),
            description="Analyze the impact of discounts on profit margins. No input required.",
        ),
        Tool(
            name="GetCorrelationMatrix",
            func=lambda _: json.dumps(data_loader.get_correlation_matrix(), indent=2),
            description="Get the correlation matrix for numerical columns. No input required.",
        ),
        Tool(
            name="GetSegmentCountryMatrix",
            func=lambda _: json.dumps(
                data_loader.get_segment_country_matrix(), indent=2
            ),
            description="Get a matrix of profit by segment and country. No input required.",
        ),
    ]

    # Create the agent
    agent = create_react_agent(llm, tools, DATA_ANALYST_SYSTEM_PROMPT)

    # Create the agent executor
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent, tools=tools, verbose=True, max_iterations=5
    )

    return agent_executor


"""
Hypothesis Generator Agent for Financial Analysis System.
Specialises in generating well-formed, testable hypotheses based on financial data analysis.
"""

import json
import os
from typing import Any, Dict, List, Optional

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI


class HypothesisGeneratorAgent:
    """
    Agent specialised in generating high-quality, testable hypotheses from financial data.
    """

    def __init__(
        self,
        deployment_name: str = "gpt-4o",
        temperature: float = 0.7,  # Higher temperature for more creative hypotheses
        streaming: bool = True,
    ):
        """
        Initialise the Hypothesis Generator Agent.

        Args:
            deployment_name: Name of the Azure OpenAI deployment
            temperature: Temperature parameter for the LLM
            streaming: Whether to stream output
        """
        # Get Azure OpenAI configuration from environment variables
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")

        if not azure_endpoint or not azure_api_key:
            raise ValueError(
                "Azure OpenAI credentials not found in environment variables"
            )

        self.llm = AzureChatOpenAI(
            azure_deployment=deployment_name,
            openai_api_version=api_version,
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            temperature=temperature,
            streaming=streaming,
        )

        # Define the system prompt for hypothesis generation
        self.system_prompt = """You are a Hypothesis Generator specialising in creating well-formed, testable hypotheses about financial data.

YOUR CAPABILITIES:
1. Formulating specific, testable hypotheses based on financial data patterns
2. Identifying potential causal relationships within business data
3. Creating diverse hypotheses that cover multiple aspects of business performance
4. Prioritizing hypotheses with high potential business value
5. Structuring hypotheses to be clearly testable with available data

YOUR GUIDELINES:
1. Generate exactly 3-5 high-quality hypotheses, not more or less
2. Each hypothesis should be specific, concise, and testable
3. Hypotheses should cover diverse aspects of the business (don't focus on just one area)
4. For each hypothesis, provide a clear rationale based on observed data patterns
5. Explain why confirming or rejecting each hypothesis would be valuable
6. Consider counter-intuitive or unexpected relationships that might yield novel insights
7. Avoid hypotheses that are too obvious or would provide little business value
8. Format hypotheses to be directly testable by an analyst

RESPONSE FORMAT:
For each hypothesis:
1. [HYPOTHESIS]: A clear, specific statement that can be tested
2. [RATIONALE]: Why you've formulated this hypothesis based on the data
3. [TEST APPROACH]: How this hypothesis could be tested with the available data
4. [BUSINESS IMPACT]: Why confirming or rejecting this hypothesis would be valuable
"""

    def generate_hypotheses(
        self, data_summary: Dict[str, Any], initial_analysis: str
    ) -> List[Dict[str, Any]]:
        """
        Generate 3-5 high-quality hypotheses based on data summary and initial analysis.

        Args:
            data_summary: Dictionary containing data summary
            initial_analysis: String containing initial analysis of the data

        Returns:
            List of generated hypotheses with rationales
        """
        # Create the prompt
        prompt = self._create_hypothesis_prompt(data_summary, initial_analysis)

        # Call the LLM
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ]

        response = self.llm(messages)

        # Parse the response into structured hypotheses
        hypotheses = self._parse_hypotheses(response.content)

        return hypotheses

    def _create_hypothesis_prompt(
        self, data_summary: Dict[str, Any], initial_analysis: str
    ) -> str:
        """
        Create a prompt for hypothesis generation.

        Args:
            data_summary: Dictionary containing data summary
            initial_analysis: String containing initial analysis

        Returns:
            Formatted prompt string
        """
        # Convert data summary to JSON string
        data_summary_str = json.dumps(data_summary, indent=2)

        prompt = f"""Please generate 3-5 high-quality, testable hypotheses based on the following financial data summary and initial analysis.

DATA SUMMARY:
{data_summary_str}

INITIAL ANALYSIS:
{initial_analysis}

For each hypothesis:
1. Ensure it is specific and directly testable with the available data
2. Provide a clear rationale that explains why you believe this hypothesis is worth investigating
3. Suggest a concrete approach for testing this hypothesis
4. Explain the potential business impact if the hypothesis is confirmed or rejected

Focus on creating diverse hypotheses that could lead to actionable business insights. Consider relationships between:
- Different segments and their profitability
- Discount strategies and profit margins
- Regional performance variations
- Product pricing and sales volume
- Seasonal patterns and their business implications

Generate hypotheses that challenge assumptions and could reveal non-obvious patterns in the data.
"""
        return prompt

    def _parse_hypotheses(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse the LLM response into structured hypotheses.

        Args:
            response_text: Raw response from the LLM

        Returns:
            List of parsed hypotheses
        """
        hypotheses = []

        # Split the text into sections for each hypothesis
        # This uses a simple pattern matching approach that looks for numbered hypotheses
        hypothesis_sections = []
        current_section = ""

        for line in response_text.split("\n"):
            # Check if this line starts a new hypothesis (looks for patterns like "1." or "Hypothesis 1:")
            if (
                line.strip().startswith(("1.", "2.", "3.", "4.", "5."))
                and ("hypothesis" in line.lower() or "HYPOTHESIS" in line)
            ) or (
                line.strip().startswith("Hypothesis") and (":" in line or "#" in line)
            ):

                if current_section:  # If we have collected text for a previous section
                    hypothesis_sections.append(current_section)
                    current_section = ""

                current_section = line + "\n"
            else:
                current_section += line + "\n"

        # Add the last section
        if current_section:
            hypothesis_sections.append(current_section)

        # If the splitting logic above didn't work well, fallback to treating the entire response
        # as one section and we'll try to parse key parts within it
        if not hypothesis_sections:
            hypothesis_sections = [response_text]

        # Process each section to extract the components
        for section in hypothesis_sections:
            hypothesis = {
                "hypothesis": "",
                "rationale": "",
                "test_approach": "",
                "business_impact": "",
            }

            # Extract the main hypothesis statement
            if "[HYPOTHESIS]:" in section:
                parts = section.split("[HYPOTHESIS]:", 1)
                remaining = parts[1]

                # Find the end of the hypothesis section
                if "[RATIONALE]:" in remaining:
                    hypothesis_text, remaining = remaining.split("[RATIONALE]:", 1)
                    hypothesis["hypothesis"] = hypothesis_text.strip()

                    # Extract rationale
                    if "[TEST APPROACH]:" in remaining:
                        rationale_text, remaining = remaining.split(
                            "[TEST APPROACH]:", 1
                        )
                        hypothesis["rationale"] = rationale_text.strip()

                        # Extract test approach
                        if "[BUSINESS IMPACT]:" in remaining:
                            test_approach_text, business_impact_text = remaining.split(
                                "[BUSINESS IMPACT]:", 1
                            )
                            hypothesis["test_approach"] = test_approach_text.strip()
                            hypothesis["business_impact"] = business_impact_text.strip()
                        else:
                            hypothesis["test_approach"] = remaining.strip()
                    else:
                        hypothesis["rationale"] = remaining.strip()

            # If the structured parsing fails, try a more general approach
            if not hypothesis["hypothesis"]:
                lines = section.split("\n")
                for i, line in enumerate(lines):
                    line_lower = line.lower()

                    if "hypothesis" in line_lower and not hypothesis["hypothesis"]:
                        # Get the hypothesis from this line or the next if this is just a header
                        if ":" in line and len(line.split(":", 1)[1].strip()) > 0:
                            hypothesis["hypothesis"] = line.split(":", 1)[1].strip()
                        elif i + 1 < len(lines):
                            hypothesis["hypothesis"] = lines[i + 1].strip()

                    elif (
                        "rationale" in line_lower or "reason" in line_lower
                    ) and not hypothesis["rationale"]:
                        # Collect the rationale (which might span multiple lines)
                        start_idx = i + 1
                        end_idx = start_idx
                        while end_idx < len(lines) and not any(
                            keyword in lines[end_idx].lower()
                            for keyword in ["test", "approach", "business", "impact"]
                        ):
                            end_idx += 1

                        hypothesis["rationale"] = "\n".join(
                            lines[start_idx:end_idx]
                        ).strip()

                    elif (
                        "test" in line_lower or "approach" in line_lower
                    ) and not hypothesis["test_approach"]:
                        # Collect the test approach
                        start_idx = i + 1
                        end_idx = start_idx
                        while end_idx < len(lines) and not any(
                            keyword in lines[end_idx].lower()
                            for keyword in ["business", "impact", "value"]
                        ):
                            end_idx += 1

                        hypothesis["test_approach"] = "\n".join(
                            lines[start_idx:end_idx]
                        ).strip()

                    elif (
                        "business" in line_lower
                        or "impact" in line_lower
                        or "value" in line_lower
                    ) and not hypothesis["business_impact"]:
                        # Collect the business impact
                        start_idx = i + 1
                        end_idx = len(lines)
                        hypothesis["business_impact"] = "\n".join(
                            lines[start_idx:end_idx]
                        ).strip()

            # Only add hypotheses that actually have content
            if hypothesis["hypothesis"]:
                hypotheses.append(hypothesis)

        # If we still couldn't parse structured hypotheses, create a single hypothesis
        # with the entire text as the hypothesis statement
        if not hypotheses:
            hypotheses.append(
                {
                    "hypothesis": response_text.strip(),
                    "rationale": "",
                    "test_approach": "",
                    "business_impact": "",
                }
            )

        return hypotheses
