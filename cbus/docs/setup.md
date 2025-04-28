# Setup Instructions

This document provides detailed instructions for setting up and running the Multi-Agent Financial Analysis System.

## Prerequisites

- Python 3.9 or higher
- Azure OpenAI API access

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/wdemichele/financial-insight-system.git
   cd financial-insight-system
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   
   Create a `.env` file in the project root with your Azure OpenAI credentials:
   ```
   # Azure OpenAI API credentials
   AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_API_VERSION=your_api_version

   # Deployment names (these should match your Azure OpenAI deployments, e.g. `gpt-4o`)
   ANALYST_DEPLOYMENT=your-analyst-deployment-name
   HYPOTHESIS_DEPLOYMENT=your-hypothesis-deployment-name
   INSIGHT_DEPLOYMENT=your-insight-deployment-name
   ```

    > **Note:** If Azure credentials aren't set up, you can look at Recent Conversations to see performance



6. **Start the web server:**

    If you want to run the web application interface:

   ```bash
   python app.py
   ```

7. **Access the web interface:**

   Open your browser and navigate to `http://localhost:5000` or `http://127.0.0.1:5000/`

## Directory Structure

Ensure your project has the following structure:
```
financial-insight-system/
├── cache/                        # Cached responses
├── conversations/                # Previous conversations
├── data/
│   └── Financial Sample.xlsx     # Your dataset
├── output/                       # Output directory
├── src/
│   ├── agents/
│   │   ├── agents.py             # Base agent implementations
│   │   └── prompts.py            # Prompts for other agents
│   ├── cache/
│   │   └── manager.py            # Cached message storer
│   ├── conversation/
│   │   └── manager.py            # Conversations manager
│   ├── data/
│   │   └── loader.py             # Data loader
│   ├── dataset/
│   │   └── manager.py            # Extracts the key findings from the dataset
│   ├── orchestration/
│   │   └── controller.py         # Orchestration logic
│   └── visualisations/
│       └── visualisation.py      # Generates visualisations
├── .env                          # Environment variables
├── .gitignore
├── main.py                       # Main entry point
└── requirements.txt              # Dependencies
```

## Azure OpenAI Setup

1. **Create an Azure OpenAI resource** in the Azure portal

2. **Deploy models** in the Azure OpenAI Studio:
   - Deploy a model for the analyst agent (e.g., gpt-4o)
   - Deploy a model for the hypothesis generator agent (e.g., gpt-4o)
   - Deploy a model for the insight generator agent (e.g., gpt-4o)

3. **Note the deployment names** and add them to your `.env` file



## Troubleshooting

### Common Issues

1. **API Authentication Errors:**
   - Double-check your Azure OpenAI API key and endpoint in the `.env` file
   - Ensure your Azure subscription has access to the required models

2. **Model Deployment Issues:**
   - Verify that the deployment names in your `.env` file match the actual deployments in Azure OpenAI Studio
   - Check that the models have been successfully deployed and are active

3. **Package Import Errors:**
   - Make sure you've activated the virtual environment
   - Try reinstalling requirements: `pip install -r requirements.txt`

4. **Data Loading Issues:**
   - Ensure the dataset file path is correct
   - Check that the Excel file has the expected structure
