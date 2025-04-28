"""
Main script for running the Multi-Agent Financial Analysis System.
"""

import argparse
import os

from dotenv import load_dotenv

from src.orchestration.controller import FinancialInsightController


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run the Financial Insight Discovery System"
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["discovery", "analysis", "qa"],
        default="discovery",
        help="Mode to run: discovery (full insight discovery), analysis (specific analysis), or qa (question answering)",
    )

    parser.add_argument(
        "--data-path",
        type=str,
        default="data/Financial Sample.xlsx",
        help="Path to the financial data Excel file",
    )

    parser.add_argument(
        "--output-dir", type=str, default="output", help="Directory for output files"
    )

    parser.add_argument(
        "--analysis-type",
        type=str,
        choices=["segment", "product", "discount"],
        help="Type of analysis to run (for analysis mode)",
    )

    parser.add_argument(
        "--parameter",
        type=str,
        help="Parameter for analysis (e.g., segment name, product name)",
    )

    parser.add_argument("--question", type=str, help="Question to answer (for qa mode)")

    parser.add_argument(
        "--analyst-deployment",
        type=str,
        default="gpt-4o",
        help="Azure OpenAI deployment name for the Data Analyst Agent",
    )

    parser.add_argument(
        "--insight-deployment",
        type=str,
        default="gpt-4o",
        help="Azure OpenAI deployment name for the Insight Generator Agent",
    )

    parser.add_argument(
        "--no-streaming", action="store_true", help="Disable streaming of agent outputs"
    )

    args = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv()

    # Check for Azure OpenAI credentials
    required_env_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
    missing_vars = [var for var in required_env_vars if var not in os.environ]

    if missing_vars:
        print(
            f"Error: Missing required environment variables: {', '.join(missing_vars)}"
        )
        print("Please set your Azure OpenAI credentials before running the script")
        return

    # Initialise the controller
    controller = FinancialInsightController(
        data_path=args.data_path,
        output_dir=args.output_dir,
        analyst_deployment=args.analyst_deployment,
        insight_deployment=args.insight_deployment,
        streaming=not args.no_streaming,
    )

    # Run the requested mode
    if args.mode == "discovery":
        print("Running full insight discovery process...")
        insights = controller.run_full_insight_discovery()
        print("\n=== FINAL INSIGHTS ===")
        print(insights)

    elif args.mode == "analysis":
        if not args.analysis_type:
            print("Error: analysis-type is required for analysis mode")
            return

        print(f"Running specific analysis: {args.analysis_type} {args.parameter or ''}")
        analysis_result = controller.run_specific_analysis(
            args.analysis_type, args.parameter
        )

        print("\n=== ANALYSIS RESULT ===")
        # Format and print analysis result for readability
        import json

        print(json.dumps(analysis_result, indent=2))

        # Generate insights for the analysis
        print("\n=== GENERATING INSIGHTS FROM ANALYSIS ===")
        insights = controller.generate_insights_for_analysis(
            analysis_result, args.analysis_type
        )

        print("\n=== INSIGHTS ===")
        print(insights)

    elif args.mode == "qa":
        if not args.question:
            print("Error: question is required for qa mode")
            return

        print(f"Answering question: {args.question}")
        answer = controller.run_q_and_a(args.question)

        print("\n=== ANSWER ===")
        print(answer)

    # Save interaction log
    controller.save_interaction_log()
    print(f"\nAll outputs have been saved to the {args.output_dir} directory.")


if __name__ == "__main__":
    main()
