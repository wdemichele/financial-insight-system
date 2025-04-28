"""
Enhanced Flask application for the Financial Analysis Q&A System.
Includes data visualisation, dataset management, conversation history,
and export functionality.
"""

import json
import os
import tempfile
import time

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from src.cache.manager import CacheManager
from src.conversation.manager import ConversationManager
from src.data.loader import FinancialDataLoader
from src.dataset.manager import DatasetManager
from src.orchestration.controller import FinancialInsightController
from src.visualisations.visualisation import VisualisationGenerator

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")

# Set maximum upload size to 16MB
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER", "uploads")
app.config["ALLOWED_EXTENSIONS"] = {"xlsx", "xls", "csv"}

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialise managers
dataset_manager = DatasetManager(os.environ.get("DATA_DIR", "data"))
conversation_manager = ConversationManager(
    os.environ.get("CONVERSATIONS_DIR", "conversations")
)
cache_manager = CacheManager(os.environ.get("CACHE_DIR", "cache"))

# Initialise controller with default settings
controller = None
visualisation_generator = None


def initialise_controller():
    """Initialise the Financial Insight Controller with the dataset."""
    global controller, visualisation_generator

    # Check for required environment variables
    required_env_vars = ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]
    missing_vars = [var for var in required_env_vars if var not in os.environ]

    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    # Get deployment names (use defaults if not specified)
    analyst_deployment = os.environ.get("ANALYST_DEPLOYMENT", "gpt-4")
    insight_deployment = os.environ.get("INSIGHT_DEPLOYMENT", "gpt-4")

    # Get current dataset file path
    current_dataset = dataset_manager.get_current_dataset()
    if current_dataset is None:
        # Use default dataset if no dataset is set
        data_path = os.environ.get("DATA_PATH", "data/Financial Sample.xlsx")
    else:
        data_path = current_dataset["file_path"]

    # Initialise the controller
    output_dir = os.environ.get("OUTPUT_DIR", "output")

    controller = FinancialInsightController(
        data_path=data_path,
        output_dir=output_dir,
        analyst_deployment=analyst_deployment,
        insight_deployment=insight_deployment,
        streaming=False,  # Disable streaming for API use
        log_interactions=True,
    )

    # Run initial analysis to prepare the system
    print(f"Initialising system with dataset: {data_path}")
    controller.data = controller.data_loader.load_data()
    controller.data_summary = controller.data_loader.get_summary_statistics()

    # Initialise visualisation generator
    visualisation_generator = VisualisationGenerator(controller.data_loader)

    print("Initialisation complete!")

    return "Controller initialised successfully"


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


# Routes for Web Interface
@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")


@app.route("/datasets")
def datasets_page():
    """Render the datasets management page."""
    return render_template("datasets.html")


@app.route("/conversations")
def conversations_page():
    """Render the conversations history page."""
    return render_template("conversations.html")


@app.route("/settings")
def settings_page():
    """Render the settings page."""
    return render_template("settings.html")


# API Routes for Q&A
@app.route("/api/ask", methods=["POST"])
def ask_question():
    """API endpoint for asking questions about the financial data."""
    global controller, visualisation_generator

    # Initialise controller if not already done
    if controller is None:
        try:
            initialise_controller()
        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to initialise system: {str(e)}",
                    }
                ),
                500,
            )

    # Get question from request
    data = request.json
    question = data.get("question")
    conversation_id = data.get("conversation_id")

    if not question:
        return jsonify({"status": "error", "message": "No question provided"}), 400

    # Create or set conversation
    if not conversation_id:
        conversation_id = conversation_manager.create_conversation(
            title="New Conversation",
            dataset_id=(
                dataset_manager.get_current_dataset()["id"]
                if dataset_manager.get_current_dataset()
                else None
            ),
        )
    else:
        # Ensure the conversation exists
        if conversation_manager.get_conversation(conversation_id) is None:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Conversation with ID {conversation_id} not found",
                    }
                ),
                404,
            )
        conversation_manager.set_current_conversation(conversation_id)

    # Add question to conversation
    conversation_manager.add_message(conversation_id, "user", question)

    try:
        # Generate cache key based on question and current dataset
        current_dataset = dataset_manager.get_current_dataset()
        dataset_id = current_dataset["id"] if current_dataset else "default"
        cache_key = f"qa_{dataset_id}_{hash(question)}"

        # Check cache for existing answer
        cached_result = cache_manager.get(cache_key)

        if cached_result:
            answer = cached_result["answer"]
            processing_time = cached_result["processing_time"]
            chart_data = cached_result.get("chart_data")
        else:
            # Record start time
            start_time = time.time()

            # Process the question
            answer = controller.run_q_and_a(question)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Generate visualisation if appropriate
            chart_data = None
            if visualisation_generator:
                chart_data = visualisation_generator.generate_chart_for_question(
                    question
                )

            # Cache the result
            cache_manager.set(
                cache_key,
                {
                    "answer": answer,
                    "processing_time": processing_time,
                    "chart_data": chart_data,
                },
            )

        # Add answer to conversation
        conversation_manager.add_message(
            conversation_id,
            "assistant",
            answer,
            processing_time=processing_time,
            chart_data=chart_data,
        )

        # Generate follow-up suggestions
        follow_up_suggestions = conversation_manager.generate_follow_up_questions(
            conversation_id
        )

        return jsonify(
            {
                "status": "success",
                "conversation_id": conversation_id,
                "question": question,
                "answer": answer,
                "processing_time": round(processing_time, 2),
                "chart_data": chart_data,
                "follow_up_suggestions": follow_up_suggestions,
            }
        )

    except Exception as e:
        # Log the error and add system message to conversation
        error_message = f"Error processing question: {str(e)}"
        print(error_message)
        conversation_manager.add_message(conversation_id, "system", error_message)

        return jsonify({"status": "error", "message": error_message}), 500


# API Routes for Stats and Sample Questions
@app.route("/api/stats")
def get_stats():
    """Return basic statistics about the dataset."""
    global controller

    # Initialise controller if not already done
    if controller is None:
        try:
            initialise_controller()
        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to initialise system: {str(e)}",
                    }
                ),
                500,
            )

    try:
        # Check cache for stats
        current_dataset = dataset_manager.get_current_dataset()
        dataset_id = current_dataset["id"] if current_dataset else "default"
        cache_key = f"stats_{dataset_id}"

        cached_stats = cache_manager.get(cache_key)

        if cached_stats:
            return jsonify({"status": "success", "stats": cached_stats})

        # Get basic stats
        stats = {
            "total_rows": len(controller.data),
            "total_sales": float(controller.data_summary.get("total_sales", 0)),
            "total_profit": float(controller.data_summary.get("total_profit", 0)),
            "segments": [
                seg["Segment"]
                for seg in controller.data_summary.get("segment_analysis", [])
            ],
            "countries": [
                country["Country"]
                for country in controller.data_summary.get("country_analysis", [])
            ],
            "products": [
                product["Product"]
                for product in controller.data_summary.get("product_analysis", [])
            ],
        }

        # Add current dataset info
        if current_dataset:
            stats["current_dataset"] = {
                "id": current_dataset["id"],
                "name": current_dataset["name"],
                "description": current_dataset.get("description", ""),
                "date_added": current_dataset.get("date_added", ""),
            }

        # Cache the stats
        cache_manager.set(cache_key, stats)

        return jsonify({"status": "success", "stats": stats})

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Error retrieving stats: {str(e)}"}
            ),
            500,
        )


@app.route("/api/sample_questions")
def get_sample_questions():
    """Return a list of sample questions for the UI."""
    # Get current dataset to tailor questions
    current_dataset = dataset_manager.get_current_dataset()
    dataset_name = current_dataset["name"] if current_dataset else "financial"

    questions = [
        f"Which segment has the highest profit margin in the {dataset_name} dataset?",
        "What is the relationship between discounts and profit margins?",
        "Which country generates the most revenue?",
        "What's the best performing product in the Enterprise segment?",
        "How do sales trends vary across different months?",
        "Why is the Enterprise segment performing differently from others?",
        "What insights can you give me about the Government segment?",
        "How do profit margins compare between different discount bands?",
        "Which product has the highest profit margin in Canada?",
        "What are the top 3 insights about this financial dataset?",
    ]

    return jsonify({"status": "success", "questions": questions})


# API Routes for System Initialisation and Management
@app.route("/api/initialise", methods=["POST"])
def init_api():
    """Initialise the controller explicitly."""
    try:
        # Clear the cache
        cache_manager.clear_all()

        # Initialise controller
        result = initialise_controller()

        return jsonify({"status": "success", "message": result})
    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Initialisation error: {str(e)}"}),
            500,
        )


@app.route("/api/clear_cache", methods=["POST"])
def clear_cache():
    """Clear the cache."""
    try:
        count = cache_manager.clear_all()

        return jsonify(
            {"status": "success", "message": f"Cleared {count} cache entries"}
        )
    except Exception as e:
        return (
            jsonify({"status": "error", "message": f"Error clearing cache: {str(e)}"}),
            500,
        )


# API Routes for Dataset Management
@app.route("/api/datasets", methods=["GET"])
def get_datasets():
    """Get list of available datasets."""
    try:
        datasets = dataset_manager.get_datasets_list()
        current_dataset = dataset_manager.get_current_dataset()

        return jsonify(
            {
                "status": "success",
                "datasets": datasets,
                "current_dataset": current_dataset,
            }
        )
    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Error retrieving datasets: {str(e)}"}
            ),
            500,
        )


@app.route("/api/datasets", methods=["POST"])
def upload_dataset():
    """Upload a new dataset."""
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400

    file = request.files["file"]
    name = request.form.get("name", file.filename)
    description = request.form.get("description", "")

    if file.filename == "":
        return jsonify({"status": "error", "message": "No selected file"}), 400

    if not allowed_file(file.filename):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f'Invalid file type. Allowed types: {", ".join(app.config["ALLOWED_EXTENSIONS"])}',
                }
            ),
            400,
        )

    try:
        # Save the file to a temporary location
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(temp_path)

        # Add the dataset
        success, message, dataset_id = dataset_manager.add_dataset(
            temp_path, name, description
        )

        # Clean up the temporary file
        os.remove(temp_path)

        if not success:
            return jsonify({"status": "error", "message": message}), 400

        # Re-initialise the controller with the new dataset
        initialise_controller()

        return jsonify(
            {
                "status": "success",
                "message": "Dataset uploaded successfully",
                "dataset_id": dataset_id,
            }
        )

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Error uploading dataset: {str(e)}"}
            ),
            500,
        )


@app.route("/api/datasets/<dataset_id>", methods=["DELETE"])
def delete_dataset(dataset_id):
    """Delete a dataset."""
    try:
        success, message = dataset_manager.remove_dataset(dataset_id)

        if not success:
            return jsonify({"status": "error", "message": message}), 404

        # Re-initialise the controller if needed
        initialise_controller()

        return jsonify({"status": "success", "message": message})

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Error deleting dataset: {str(e)}"}
            ),
            500,
        )


@app.route("/api/datasets/<dataset_id>/activate", methods=["POST"])
def activate_dataset(dataset_id):
    """Activate a dataset."""
    try:
        success, message = dataset_manager.set_current_dataset(dataset_id)

        if not success:
            return jsonify({"status": "error", "message": message}), 404

        # Re-initialise the controller with the new dataset
        initialise_controller()

        # Clear the cache for the new dataset
        cache_manager.clear_all()

        return jsonify({"status": "success", "message": message})

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Error activating dataset: {str(e)}"}
            ),
            500,
        )


# API Routes for Conversation Management
@app.route("/api/conversations", methods=["GET"])
def get_conversations():
    """Get list of conversations."""
    try:
        conversations = conversation_manager.get_conversations_list()
        current_conversation = conversation_manager.get_current_conversation()

        current_id = None
        if current_conversation:
            current_id = current_conversation["id"]

        return jsonify(
            {
                "status": "success",
                "conversations": conversations,
                "current_conversation_id": current_id,
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error retrieving conversations: {str(e)}",
                }
            ),
            500,
        )


@app.route("/api/conversations", methods=["POST"])
def create_conversation():
    """Create a new conversation."""
    try:
        data = request.json
        title = data.get("title", f"Conversation {time.strftime('%Y-%m-%d %H:%M')}")

        # Get current dataset id
        current_dataset = dataset_manager.get_current_dataset()
        dataset_id = current_dataset["id"] if current_dataset else None

        conversation_id = conversation_manager.create_conversation(title, dataset_id)

        return jsonify(
            {
                "status": "success",
                "message": "Conversation created successfully",
                "conversation_id": conversation_id,
            }
        )
    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Error creating conversation: {str(e)}"}
            ),
            500,
        )


@app.route("/api/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    """Get a specific conversation."""
    try:
        conversation = conversation_manager.get_conversation(conversation_id)

        if not conversation:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Conversation with ID {conversation_id} not found",
                    }
                ),
                404,
            )

        return jsonify({"status": "success", "conversation": conversation})
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error retrieving conversation: {str(e)}",
                }
            ),
            500,
        )


@app.route("/api/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    """Delete a conversation."""
    try:
        success = conversation_manager.delete_conversation(conversation_id)

        if not success:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Conversation with ID {conversation_id} not found",
                    }
                ),
                404,
            )

        return jsonify(
            {"status": "success", "message": "Conversation deleted successfully"}
        )
    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Error deleting conversation: {str(e)}"}
            ),
            500,
        )


@app.route("/api/conversations/<conversation_id>/activate", methods=["POST"])
def activate_conversation(conversation_id):
    """Activate a conversation."""
    try:
        success = conversation_manager.set_current_conversation(conversation_id)

        if not success:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Conversation with ID {conversation_id} not found",
                    }
                ),
                404,
            )

        return jsonify(
            {"status": "success", "message": "Conversation activated successfully"}
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error activating conversation: {str(e)}",
                }
            ),
            500,
        )


@app.route("/api/conversations/<conversation_id>/export", methods=["GET"])
def export_conversation(conversation_id):
    """Export a conversation."""
    try:
        format = request.args.get("format", "json")

        if format not in ["json", "markdown", "csv", "html"]:
            return (
                jsonify(
                    {"status": "error", "message": f"Invalid export format: {format}"}
                ),
                400,
            )

        # Create a temporary file for the export
        with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as temp:
            temp_path = temp.name

        # Export the conversation
        export_path = conversation_manager.export_conversation(
            conversation_id, format, temp_path
        )

        # Get conversation title for filename
        conversation = conversation_manager.get_conversation(conversation_id)
        filename = f"{conversation['title']}_{time.strftime('%Y%m%d')}.{format}"

        # Send the file
        return send_file(
            export_path,
            as_attachment=True,
            download_name=filename,
            mimetype="application/octet-stream",
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error exporting conversation: {str(e)}",
                }
            ),
            500,
        )


# API Routes for visualisations
@app.route("/api/visualisations/<chart_type>", methods=["GET"])
def get_visualisation(chart_type):
    """Get a specific visualisation."""
    global visualisation_generator

    if visualisation_generator is None:
        try:
            initialise_controller()
        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to initialise system: {str(e)}",
                    }
                ),
                500,
            )

    try:
        # Get parameters
        params = request.args.to_dict()

        # Generate the chart
        chart_data = visualisation_generator.generate_chart_data(chart_type, **params)

        return jsonify({"status": "success", "chart_data": chart_data})
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Error generating visualisation: {str(e)}",
                }
            ),
            500,
        )


# Error handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return (
        jsonify(
            {"status": "error", "message": "File too large. Maximum file size is 16MB."}
        ),
        413,
    )


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"status": "error", "message": "Resource not found."}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    return jsonify({"status": "error", "message": "Internal server error."}), 500


# Add this to your app.py file


# Route for Hypothesis Testing page
@app.route("/hypothesis")
def hypothesis_page():
    """Render the hypothesis testing page."""
    return render_template("hypothesis.html")


# API Routes for Hypothesis Testing
@app.route("/api/generate_hypotheses", methods=["POST"])
def generate_hypotheses_api():
    """API endpoint for generating hypotheses about the financial data."""
    global controller

    # Initialise controller if not already done
    if controller is None:
        try:
            initialise_controller()
        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to initialise system: {str(e)}",
                    }
                ),
                500,
            )

    try:
        # First run an initial analysis
        analysis_results = controller.run_initial_analysis()

        # Generate hypotheses
        hypotheses_text = controller.generate_hypotheses(analysis_results)

        # Parse the hypotheses text into structured format
        structured_hypotheses = controller.parse_hypotheses(hypotheses_text)

        return jsonify(
            {
                "status": "success",
                "hypotheses": structured_hypotheses,
                "raw_text": hypotheses_text,
            }
        )

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Error generating hypotheses: {str(e)}"}
            ),
            500,
        )


@app.route("/api/test_hypothesis", methods=["POST"])
def test_hypothesis_api():
    """API endpoint for testing a specific hypothesis."""
    global controller

    # Initialise controller if not already done
    if controller is None:
        try:
            initialise_controller()
        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to initialise system: {str(e)}",
                    }
                ),
                500,
            )

    # Get hypothesis from request
    data = request.json
    hypothesis_id = data.get("hypothesis_id")
    hypothesis_text = data.get("hypothesis_text")

    if not hypothesis_text:
        return jsonify({"status": "error", "message": "No hypothesis provided"}), 400

    try:
        # Record start time
        start_time = time.time()

        # Test the hypothesis
        result = controller.analyst_agent.test_hypothesis(
            hypothesis_text, controller.data_summary
        )

        # Calculate processing time
        processing_time = time.time() - start_time

        return jsonify(
            {
                "status": "success",
                "hypothesis_id": hypothesis_id,
                "result": result,
                "processing_time": round(processing_time, 2),
            }
        )

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Error testing hypothesis: {str(e)}"}
            ),
            500,
        )


@app.route("/api/synthesize_insights", methods=["POST"])
def synthesize_insights_api():
    """API endpoint for synthesizing insights from tested hypotheses."""
    global controller

    # Initialise controller if not already done
    if controller is None:
        try:
            initialise_controller()
        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to initialise system: {str(e)}",
                    }
                ),
                500,
            )

    # Get tested hypotheses from request
    data = request.json
    tested_hypotheses = data.get("tested_hypotheses", [])

    if not tested_hypotheses or len(tested_hypotheses) < 2:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "At least two tested hypotheses are required",
                }
            ),
            400,
        )

    try:
        # Format hypothesis results for synthesis
        hypothesis_results = controller.format_hypothesis_results(tested_hypotheses)

        # Synthesize insights
        insights = controller.insight_agent.synthesize_insights(
            hypothesis_results, controller.data_summary
        )

        return jsonify({"status": "success", "insights": insights})

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Error synthesizing insights: {str(e)}"}
            ),
            500,
        )


@app.route("/api/export_insights", methods=["POST"])
def export_insights_api():
    """API endpoint for exporting insights."""
    global controller

    # Initialise controller if not already done
    if controller is None:
        try:
            initialise_controller()
        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to initialise system: {str(e)}",
                    }
                ),
                500,
            )

    data = request.json
    insights = data.get("insights")
    format_type = data.get("format", "markdown")

    if not insights:
        return jsonify({"status": "error", "message": "No insights provided"}), 400

    try:
        # Create a temporary file for the export
        with tempfile.NamedTemporaryFile(
            suffix=f".{format_type}", delete=False
        ) as temp:
            temp_path = temp.name

        # Export based on format
        if format_type == "json":
            with open(temp_path, "w") as f:
                json.dump({"insights": insights}, f, indent=2)

        elif format_type == "markdown" or format_type == "txt":
            with open(temp_path, "w") as f:
                f.write(insights)

        elif format_type == "html":
            with open(temp_path, "w") as f:
                f.write(
                    f"<!DOCTYPE html>\n<html>\n<head>\n<title>Financial Insights</title>\n"
                )
                f.write("<style>\n")
                f.write(
                    "body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }\n"
                )
                f.write("h1, h2, h3 { color: #333; }\n")
                f.write("</style>\n</head>\n<body>\n")
                f.write("<h1>Financial Insights</h1>\n")

                # Convert markdown to HTML
                html_content = controller.markdown_to_html(insights)
                f.write(html_content)

                f.write("</body>\n</html>")

        elif format_type == "pdf":
            # This would require a PDF generation library like reportlab or weasyprint
            # For simplicity, we'll return an error for now
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "PDF export is not supported in this version",
                    }
                ),
                400,
            )

        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Unsupported export format: {format_type}",
                    }
                ),
                400,
            )

        # Send the file
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=f"financial_insights.{format_type}",
            mimetype="application/octet-stream",
        )

    except Exception as e:
        return (
            jsonify(
                {"status": "error", "message": f"Error exporting insights: {str(e)}"}
            ),
            500,
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    # Initialise controller on startup
    try:
        initialise_controller()
    except Exception as e:
        print(f"Warning: Failed to initialise controller at startup: {e}")
        print(
            "The system will attempt to initialise when the first request is received."
        )

    app.run(host="0.0.0.0", port=port, debug=debug)
