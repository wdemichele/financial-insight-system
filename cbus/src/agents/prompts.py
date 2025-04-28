"""
Agent Prompt Templates for Financial Analysis System

This module defines the prompt templates for the data analyst and insight generator agents.
"""

from typing import Any, Dict, List

from langchain.prompts import PromptTemplate

# Data Analyst Agent System Prompt
DATA_ANALYST_SYSTEM_PROMPT = """You are a Financial Data Analyst Agent specialised in identifying patterns, trends, and insights in financial datasets.

DATASET CONTEXT:
- The financial dataset contains sales and profit data across different market segments, countries, products, and time periods
- Key metrics include: Sales, Profit, Units Sold, Discounts, Manufacturing Price, Sale Price, etc.
- The data covers different segments (Government, Midmarket, Enterprise, etc.), countries, and products

YOUR CAPABILITIES:
1. Analyze financial data to identify significant patterns and anomalies
2. Apply statistical reasoning to understand relationships between variables
3. Test specific hypotheses about business performance
4. Provide precise, quantitative analysis with supporting evidence
5. Generate visualisations and statistical summaries

YOUR GUIDELINES:
1. Always base your analysis on the provided data
2. Use precise numerical values and calculations
3. Present relative comparisons (%, ratios, rankings) when relevant
4. Think step-by-step when performing complex analysis
5. Acknowledge limitations in your analysis
6. Focus on findings that would be valuable for business decisions
7. Be alert to unexpected patterns or outliers in the data

RESPONSE FORMAT:
- Present your findings in a clear, structured format
- Include precise calculations and metrics
- Support claims with specific data points
- Suggest areas for further investigation when appropriate
- When appropriate, frame your analysis as actionable insights
"""

# Data Analyst Task Template
DATA_ANALYST_TASK_TEMPLATE = """
ANALYSIS TASK: {task}

AVAILABLE DATA:
{data_summary}

Based on this information, perform the requested analysis. 
Think step-by-step, showing your reasoning process, calculations, and interpretations.

Focus on identifying:
1. Clear patterns in the data
2. Significant contrasts or comparisons
3. Unusual or unexpected findings
4. Potential relationships between variables
5. Findings with potential business implications

When complete, present your findings in a structured format with appropriate numerical evidence.
"""

DATA_ANALYST_PROMPT = PromptTemplate(
    input_variables=["task", "data_summary"], template=DATA_ANALYST_TASK_TEMPLATE
)

# Insight Generator Agent System Prompt
INSIGHT_GENERATOR_SYSTEM_PROMPT = """You are an Insight Generator Agent specialised in interpreting financial data analysis and creating valuable business insights.

YOUR CAPABILITIES:
1. Translate data patterns into meaningful business insights
2. Generate hypotheses to explain observed patterns
3. Evaluate the business impact of findings
4. Prioritize insights based on potential value
5. Identify implications and potential actions
6. Create clear, compelling narratives around data insights

YOUR GUIDELINES:
1. Focus on insights that are actionable and valuable for business decisions
2. Consider the broader business context when interpreting data
3. Distinguish between correlation and causation in your interpretations
4. Be thoughtful about the limitations of the analysis
5. Prioritize quality of insights over quantity
6. Connect insights across different dimensions (segments, countries, time periods)
7. Clearly explain why an insight matters from a business perspective

RESPONSE FORMAT:
- Present insights clearly with descriptive titles
- Explain the evidence supporting each insight
- Discuss potential business implications
- Suggest possible actions or decisions
- Indicate confidence level and limitations
- Prioritize insights by potential business value
"""

# Insight Generator Task Template
INSIGHT_GENERATOR_TASK_TEMPLATE = """
INSIGHT GENERATION TASK: {task}

ANALYSIS RESULTS:
{analysis_results}

Based on these analysis results, perform the requested insight generation task.
Think critically about what these patterns and findings mean for the business.

For each potential insight:
1. Clearly describe the pattern or finding
2. Explain why it matters from a business perspective
3. Assess the reliability of the evidence
4. Suggest implications for business strategy or decisions
5. Identify any follow-up questions or analyses that would strengthen the insight

When complete, present your insights in order of potential business value, 
with clear explanations of supporting evidence and business implications.
"""

INSIGHT_GENERATOR_PROMPT = PromptTemplate(
    input_variables=["task", "analysis_results"],
    template=INSIGHT_GENERATOR_TASK_TEMPLATE,
)

# Hypothesis Generation Template
HYPOTHESIS_GENERATION_TEMPLATE = """
Based on the following data summary, generate 3-5 specific hypotheses that could explain interesting patterns or anomalies in the financial data.

DATA SUMMARY:
{data_summary}

For each hypothesis:
1. State the hypothesis clearly
2. Explain what data patterns led you to formulate this hypothesis
3. Describe what additional analysis would help confirm or refute it
4. Estimate its potential business importance (high/medium/low)

Focus on generating hypotheses that, if confirmed, would lead to actionable business insights.
"""

HYPOTHESIS_GENERATION_PROMPT = PromptTemplate(
    input_variables=["data_summary"], template=HYPOTHESIS_GENERATION_TEMPLATE
)

# Hypothesis Testing Template
HYPOTHESIS_TESTING_TEMPLATE = """
HYPOTHESIS TO TEST: {hypothesis}

AVAILABLE DATA SUMMARY:
{data_summary}

Your task is to thoroughly test this hypothesis using the available data.

Please:
1. Break down the hypothesis into testable components
2. Identify what specific data you need to analyze
3. Perform the necessary calculations and comparisons
4. Determine whether the data supports, refutes, or is inconclusive about the hypothesis
5. Provide numerical evidence for your conclusion
6. Note any limitations in your testing approach

Be precise and thorough in your analysis, showing your reasoning process and calculations.
"""

HYPOTHESIS_TESTING_PROMPT = PromptTemplate(
    input_variables=["hypothesis", "data_summary"], template=HYPOTHESIS_TESTING_TEMPLATE
)

# Final Insight Synthesis Template
INSIGHT_SYNTHESIS_TEMPLATE = """
TESTED HYPOTHESES AND RESULTS:
{hypothesis_results}

DATA SUMMARY:
{data_summary}

Your task is to synthesize the hypothesis testing results into 2-3 valuable, actionable business insights.

For each insight:
1. Provide a clear, specific title for the insight
2. Summarize the supporting evidence from the hypothesis testing
3. Explain why this insight matters from a business perspective
4. Suggest specific actions or decisions that could be made based on this insight
5. Note any limitations or areas for further investigation

Prioritize insights based on:
- Strength of supporting evidence
- Potential business impact
- Actionability
- Novelty or unexpectedness

Present your insights in a clear, structured format that would be valuable for business decision-makers.
"""

INSIGHT_SYNTHESIS_PROMPT = PromptTemplate(
    input_variables=["hypothesis_results", "data_summary"],
    template=INSIGHT_SYNTHESIS_TEMPLATE,
)


def get_analyst_prompt_with_task(task: str, data_summary: Dict[str, Any]) -> str:
    """
    Generate a complete prompt for the Data Analyst Agent.

    Args:
        task: The specific analysis task
        data_summary: Dictionary containing data summary information

    Returns:
        Complete formatted prompt string
    """
    # Convert data summary to a formatted string representation
    data_summary_str = format_data_summary(data_summary)

    # Format the task template
    task_prompt = DATA_ANALYST_PROMPT.format(task=task, data_summary=data_summary_str)

    # Combine system prompt and task prompt
    return f"{DATA_ANALYST_SYSTEM_PROMPT}\n\n{task_prompt}"


def get_insight_prompt_with_task(task: str, analysis_results: str) -> str:
    """
    Generate a complete prompt for the Insight Generator Agent.

    Args:
        task: The specific insight generation task
        analysis_results: String containing analysis results

    Returns:
        Complete formatted prompt string
    """
    # Format the task template
    task_prompt = INSIGHT_GENERATOR_PROMPT.format(
        task=task, analysis_results=analysis_results
    )

    # Combine system prompt and task prompt
    return f"{INSIGHT_GENERATOR_SYSTEM_PROMPT}\n\n{task_prompt}"


def get_hypothesis_generation_prompt(data_summary: Dict[str, Any]) -> str:
    """
    Generate a prompt for hypothesis generation.

    Args:
        data_summary: Dictionary containing data summary information

    Returns:
        Formatted hypothesis generation prompt
    """
    data_summary_str = format_data_summary(data_summary)

    return f"{INSIGHT_GENERATOR_SYSTEM_PROMPT}\n\n{HYPOTHESIS_GENERATION_PROMPT.format(data_summary=data_summary_str)}"


def get_hypothesis_testing_prompt(hypothesis: str, data_summary: Dict[str, Any]) -> str:
    """
    Generate a prompt for testing a specific hypothesis.

    Args:
        hypothesis: The hypothesis to test
        data_summary: Dictionary containing data summary information

    Returns:
        Formatted hypothesis testing prompt
    """
    data_summary_str = format_data_summary(data_summary)

    return f"{DATA_ANALYST_SYSTEM_PROMPT}\n\n{HYPOTHESIS_TESTING_PROMPT.format(hypothesis=hypothesis, data_summary=data_summary_str)}"


def get_insight_synthesis_prompt(
    hypothesis_results: str, data_summary: Dict[str, Any]
) -> str:
    """
    Generate a prompt for synthesizing insights from hypothesis testing results.

    Args:
        hypothesis_results: String containing hypothesis testing results
        data_summary: Dictionary containing data summary information

    Returns:
        Formatted insight synthesis prompt
    """
    data_summary_str = format_data_summary(data_summary)

    return f"{INSIGHT_GENERATOR_SYSTEM_PROMPT}\n\n{INSIGHT_SYNTHESIS_PROMPT.format(hypothesis_results=hypothesis_results, data_summary=data_summary_str)}"


def format_data_summary(data_summary: Dict[str, Any]) -> str:
    """
    Convert a data summary dictionary to a formatted string representation.

    Args:
        data_summary: Dictionary containing data summary information

    Returns:
        Formatted string representation
    """
    import json

    # Format the data summary as a formatted JSON string
    formatted_json = json.dumps(data_summary, indent=2)

    return formatted_json


# Hypothesis Generator System Prompt
HYPOTHESIS_GENERATOR_SYSTEM_PROMPT = """You are a Hypothesis Generator specialising in creating well-formed, testable hypotheses about financial data.

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

# Standard Hypothesis Generation Template
STANDARD_HYPOTHESIS_GENERATION_TEMPLATE = """
Please generate 3-5 high-quality, testable hypotheses based on the following financial data summary and initial analysis.

DATA SUMMARY:
{data_summary}

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

STANDARD_HYPOTHESIS_PROMPT = PromptTemplate(
    input_variables=["data_summary", "initial_analysis"],
    template=STANDARD_HYPOTHESIS_GENERATION_TEMPLATE,
)

# Targeted Hypothesis Generation Template (focused on specific areas)
TARGETED_HYPOTHESIS_GENERATION_TEMPLATE = """
Please generate 3-5 high-quality, testable hypotheses focused specifically on {focus_area} based on the following financial data.

DATA SUMMARY:
{data_summary}

INITIAL ANALYSIS:
{initial_analysis}

For each hypothesis:
1. Ensure it is specific and directly testable with the available data
2. Provide a clear rationale that explains why you believe this hypothesis is worth investigating
3. Suggest a concrete approach for testing this hypothesis
4. Explain the potential business impact if the hypothesis is confirmed or rejected

Focus on creating diverse hypotheses specifically about {focus_area} that could lead to actionable business insights.

Generate hypotheses that challenge assumptions and could reveal non-obvious patterns in the data.
"""

TARGETED_HYPOTHESIS_PROMPT = PromptTemplate(
    input_variables=["focus_area", "data_summary", "initial_analysis"],
    template=TARGETED_HYPOTHESIS_GENERATION_TEMPLATE,
)

# Unexpected Patterns Hypothesis Template (for identifying counter-intuitive patterns)
UNEXPECTED_HYPOTHESIS_GENERATION_TEMPLATE = """
Please generate 3-5 high-quality, testable hypotheses that explore unexpected or counter-intuitive patterns in the following financial data.

DATA SUMMARY:
{data_summary}

INITIAL ANALYSIS:
{initial_analysis}

For each hypothesis:
1. Focus on relationships that might seem surprising or go against conventional business wisdom
2. Provide a clear rationale that explains why you believe this unexpected pattern might exist
3. Suggest a concrete approach for testing this hypothesis
4. Explain the potential business impact if the hypothesis is confirmed or rejected

Look for potential patterns such as:
- Cases where higher prices correlate with higher sales volumes
- Segments that perform better with fewer resources
- Unexpected seasonal patterns
- Counter-intuitive geographic performance variations
- Surprising relationships between discount strategies and customer behavior

The goal is to find insights that might be missed by traditional analysis but could provide significant competitive advantages.
"""

UNEXPECTED_HYPOTHESIS_PROMPT = PromptTemplate(
    input_variables=["data_summary", "initial_analysis"],
    template=UNEXPECTED_HYPOTHESIS_GENERATION_TEMPLATE,
)


def get_hypothesis_prompt(
    data_summary: Dict[str, Any],
    initial_analysis: str,
    prompt_type: str = "standard",
    focus_area: str = None,
) -> str:
    """
    Get the appropriate hypothesis generation prompt based on the prompt type.

    Args:
        data_summary: Dictionary containing data summary
        initial_analysis: Initial analysis text
        prompt_type: Type of prompt to use ("standard", "targeted", or "unexpected")
        focus_area: For targeted prompts, the area to focus on

    Returns:
        Formatted prompt string
    """
    import json

    # Convert data summary to a formatted string
    if isinstance(data_summary, dict):
        data_summary_str = json.dumps(data_summary, indent=2)
    else:
        data_summary_str = str(data_summary)

    # Select the appropriate prompt template
    if prompt_type == "targeted" and focus_area:
        prompt = TARGETED_HYPOTHESIS_PROMPT.format(
            focus_area=focus_area,
            data_summary=data_summary_str,
            initial_analysis=initial_analysis,
        )
    elif prompt_type == "unexpected":
        prompt = UNEXPECTED_HYPOTHESIS_PROMPT.format(
            data_summary=data_summary_str, initial_analysis=initial_analysis
        )
    else:  # Default to standard
        prompt = STANDARD_HYPOTHESIS_PROMPT.format(
            data_summary=data_summary_str, initial_analysis=initial_analysis
        )

    # Combine with system prompt
    return f"{HYPOTHESIS_GENERATOR_SYSTEM_PROMPT}\n\n{prompt}"
