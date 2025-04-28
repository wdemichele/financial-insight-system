# Multi-Agent Data Insight Discovery System

## 1. Approach & Architecture Design

### Overall Approach

My approach to this case study was to design a multi-agent system that specialises in different aspects of the financial data analysis process, creating a workflow that mimics how expert analysts would approach data insights discovery. The implementation uses LangChain with Azure OpenAI integration to separate concerns and allow each agent to focus on what it does best while orchestrating their interactions to produce high-quality insights.

The architecture follows a hypothesis-driven approach to insight discovery:
1. Exploratory analysis to understand the data
2. Generation of specific, testable hypotheses 
3. Systematic testing of these hypotheses
4. Synthesis of findings into actionable insights

### Agent Roles and Responsibilities

The system consists of three specialised agents, each with distinct responsibilities:

#### 1. Data Analyst Agent
**Responsibilities:**
- Exploratory data analysis to identify patterns and anomalies
- Statistical calculations and numerical reasoning
- Testing of specific hypotheses against the data
- Verification of factual claims and numerical evidence
- Providing objective, quantitative analysis

This agent uses a lower temperature setting (0.2) to prioritise accuracy and logical reasoning when working with numbers and statistical patterns.

#### 2. Hypothesis Generator Agent
**Responsibilities:**
- Formulating specific, testable hypotheses based on data patterns
- Creating diverse hypotheses across multiple business dimensions
- Prioritising hypotheses with high potential business value
- Structuring hypotheses with clear rationales and test approaches
- Identifying potential causal relationships

This agent uses a higher temperature setting (0.7) to encourage creative thinking and diversity in hypothesis generation, while still maintaining rigor and testability.

#### 3. Insight Generator Agent
**Responsibilities:**
- Interpreting analysis results in business context
- Synthesising findings into coherent insights
- Prioritising insights by business impact and actionability
- Providing strategic recommendations based on findings
- Explaining the significance of findings for decision-makers

This agent uses a moderate temperature setting (0.3) to balance creativity with accuracy when interpreting results and generating business insights.

### Interaction Workflow

The system orchestrates these agents through a controller that manages the workflow and information sharing:

```
┌──────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│                  │     │                     │     │                  │
│  Data Analysis   │───▶│ Hypothesis Creation │────▶│ Hypothesis Tests │
│  (Analyst Agent) │     │ (Hypothesis Agent)  │     │ (Analyst Agent)  │
│                  │     │                     │     │                  │
└──────────────────┘     └─────────────────────┘     └──────────────────┘
                                                              │
                                                              ▼
                                                    ┌──────────────────┐
                                                    │                  │
                                                    │ Insight Creation │
                                                    │ (Insight Agent)  │
                                                    │                  │
                                                    └──────────────────┘
```

**Step 1: Initial Data Analysis**
- The Data Analyst Agent performs exploratory analysis on the financial dataset
- Identifies key patterns, anomalies, and relationships in the data
- Produces a comprehensive analysis with statistical evidence

**Step 2: Hypothesis Generation**
- The Hypothesis Generator Agent reviews the analysis
- Creates 3-5 well-formed, testable hypotheses about the data
- Each hypothesis includes a rationale, test approach, and business impact

**Step 3: Hypothesis Testing**
- The Data Analyst Agent tests each hypothesis systematically
- Provides detailed evidence supporting or refuting each hypothesis
- Includes numerical calculations, statistical comparisons, and limitations

**Step 4: Insight Synthesis**
- The Insight Generator Agent reviews all hypothesis test results
- Synthesises findings into coherent, actionable business insights
- Prioritises insights by potential business value
- Provides strategic recommendations based on the findings

This workflow creates a full traceability chain from raw data to actionable insights, with each agent contributing its specialised expertise.

### Framework Selection

I implemented this system using **LangChain** with **Azure OpenAI** integration due to:

1. **Modularity**: LangChain provides strong abstractions for creating specialised agents
2. **Prompt management**: LangChain's prompt templates enable consistent, well-structured agent interactions
3. **Azure OpenAI integration**: Enterprise-grade security and compliance for sensitive financial data
4. **Flexibility**: LangChain allows for custom agent logic and orchestration
5. **Stateful interactions**: The framework supports maintaining context across the workflow

The orchestration logic is implemented in the controller class, which manages the flow of information between agents and ensures that each step builds upon the previous ones.

## 2. Prompt Design and Rationale

All agents and prompts can be found in `src\agents\agents.py` and `src\agents\prompts.py` respectively.

My prompt engineering strategy focused on creating specialised prompts that leverage each agent's strengths while constraining their outputs to ensure consistency and reliability.

### Data Analyst Agent Prompt

```python
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
```

**Rationale:**
- **Clear Context Setting**: Provides dataset structure and expected content
- **Specific Capabilities**: Defines the analytical scope to focus on data-driven tasks
- **Explicit Guidelines**: Ensures the agent maintains statistical rigor and objectivity
- **Structured Response Format**: Ensures outputs are consistent and verifiable

The Data Analyst prompt was designed to encourage thorough numerical reasoning while preventing overconfidence in interpretations. By focusing on quantitative evidence and including uncertainty acknowledgment, the prompt helps ensure reliable analysis.

### Insight Generator Agent Prompt

```python
INSIGHT_GENERATOR_SYSTEM_PROMPT = """You are an Insight Generator Agent specialised in interpreting financial data analysis and creating valuable business insights.

YOUR CAPABILITIES:
1. Translate data patterns into meaningful business insights
2. Generate hypotheses to explain observed patterns
3. Evaluate the business impact of findings
4. Prioritise insights based on potential value
5. Identify implications and potential actions
6. Create clear, compelling narratives around data insights

YOUR GUIDELINES:
1. Focus on insights that are actionable and valuable for business decisions
2. Consider the broader business context when interpreting data
3. Distinguish between correlation and causation in your interpretations
4. Be thoughtful about the limitations of the analysis
5. Prioritise quality of insights over quantity
6. Connect insights across different dimensions (segments, countries, time periods)
7. Clearly explain why an insight matters from a business perspective

RESPONSE FORMAT:
- Present insights clearly with descriptive titles
- Explain the evidence supporting each insight
- Discuss potential business implications
- Suggest possible actions or decisions
- Indicate confidence level and limitations
- Prioritise insights by potential business value
"""
```

**Rationale:**
- **Business Focus**: Orients the agent toward business value, not just statistical findings
- **Interpretive Boundaries**: Guidelines that prevent overinterpretation of correlations
- **Context Integration**: Encourages connecting dots across different dimensions
- **Actionability Emphasis**: Requires insights to lead to potential actions
- **Quality Over Quantity**: Prefers fewer high-value insights to many shallow ones

The Insight Generator prompt was designed to bridge the gap between raw data analysis and business decision-making. The constraints around correlation vs. causation and confidence levels help prevent overreach in the interpretations.

#### Hypothesis Generation Prompt

```python
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
```

**Rationale:**
- **Structured Hypotheses**: Requires clear statements that can be tested
- **Evidence Grounding**: Must connect to observed data patterns
- **Testability**: Must suggest specific tests for validation
- **Business Relevance**: Requires estimation of business impact
- **Actionability Focus**: Prioritises hypotheses that could lead to business actions

This prompt creates a critical bridge between pattern recognition and insight generation, ensuring that insights are testable against data rather than speculative.

### Key Implementation Aspects

1. **Agent Separation**: Each agent has a distinct implementation class with clear responsibilities
2. **Prompt Management**: Centralised prompt templates with consistent formatting
3. **Workflow Control**: The `FinancialInsightController` manages the interaction flow
4. **Caching**: Implemented for both API responses and data processing results
5. **Visualisation**: Dynamic chart generation based on question content

## 3. Setup & Run Instructions

For detailed setup instructions, see the [Setup Instructions](setup.md) document.

## 4. Generated Insights & Evaluation

### Key Insights Generated

The system discovered two significant insights from the financial dataset:

#### Insight 1: Enterprise Segment Profitability Challenge
The Enterprise segment's negative profit margin (-3.13%) is primarily driven by higher-than-average discounts. This insight is valuable because:
- It identifies a clear problem (the only segment with negative profitability)
- It provides a specific cause (discount strategy)
- It suggests actionable remedies (optimising discount policies)
- It would have significant business impact if addressed

#### Insight 2: Discount Strategy Impact on Profitability
Higher discount bands consistently result in significantly lower profit margins across all segments. Specifically:
- High Discount Band: 9.07% profit margin
- Medium Discount Band: 14.39% profit margin
- Low Discount Band: 17.87% profit margin
- No Discount: 21.86% profit margin

This insight provides a clear strategic direction for optimising discount policies to improve overall profitability.

For detailed insights and analysis, see the [Key Insights](key_insights.md) document.


### Evaluation of Outputs

#### Quality and Reliability Assessment

**Strengths**:
1. **Data-Grounded Insights**: All findings are directly supported by numerical evidence
2. **Consistent Results**: Multiple runs produced the same core insights
3. **Actionability**: Insights lead to clear potential business actions
4. **Business Relevance**: Findings have direct impact on profitability
5. **Appropriate Scope**: Insights balance specificity with strategic relevance

**Limitations**:
1. **Dataset Constraints**: Analysis limited by available fields in the dataset
2. **Causal Inference Challenges**: System can identify correlations but true causation requires further investigation
3. **Limited Time Context**: Dataset doesn't support long-term trend analysis
4. **Lack of External Context**: No integration with market, competitor, or economic data
5. **Verification Dependency**: Numerical claims should still be verified by human experts

#### Self-Critique

**What Worked Well**:
1. **Agent Specialisation**: The separation of analytical and interpretive tasks improved output quality
2. **Hypothesis-Driven Approach**: Explicitly generating and testing hypotheses led to more rigorous insights
3. **Visualisation Integration**: Dynamic chart generation enhanced understanding of complex patterns
4. **Prompt Engineering**: Carefully designed prompts kept agents within their domains of expertise
5. **Caching Implementation**: Performance optimisation allowed iterative refinement within reasonable costs

**Limitations of the Prototype**:
1. **Limited Agent Interaction**: The sequential workflow limits back-and-forth collaboration between agents
2. **Prompt Dependency**: System quality is highly dependent on prompt engineering
3. **Basic Error Handling**: Limited ability to recover from misunderstandings or incorrect analyses
4. **Visualisation Constraints**: Charts are generated post-hoc rather than being integrated into reasoning
5. **Limited Memory**: Each analysis session is independent with no persistent knowledge

**Next Steps for Improvement**:
1. **Enhanced Agent Interaction**: Implement a more dynamic orchestration allowing iterative refinement
2. **Expanded Data Sources**: Integrate external data for market context and benchmarking
3. **User Feedback Loop**: Incorporate human feedback to improve future analyses
4. **Advanced Anomaly Detection**: Add statistical techniques for more sophisticated pattern identification
5. **Insight Repository**: Build knowledge base of past insights for reference and trend analysis
6. **Confidence Scoring**: Add explicit reliability metrics for generated insights
7. **Automated Testing**: Implement validation against known patterns in the data
### Testing Approach

While extensive testing wasn't implemented in this prototype, a robust testing strategy would include:

1. **Unit Tests**:
   - Validate data loading and preprocessing functions
   - Test chart generation with known inputs
   - Verify prompt template generation

2. **Integration Tests**:
   - Test agent interaction flow with mock LLM responses
   - Verify end-to-end process with sample data

3. **Validation Tests**:
   - Compare insight quality against human expert analysis
   - Evaluate consistency of insights across multiple runs
   - Test with intentionally modified data to verify pattern detection

4. **Performance Tests**:
   - Measure token usage and API costs
   - Verify caching effectiveness
   - Test scalability with larger datasets
