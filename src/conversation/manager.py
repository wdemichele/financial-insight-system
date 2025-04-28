"""
Conversation Manager module for Financial Analysis System.
Handles storing, retrieving, and exporting conversations.
"""

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConversationManager:
    """
    Manages conversation history, export, and suggestion features.
    """

    def __init__(self, conversations_dir: str = "conversations"):
        """
        Initialise the ConversationManager.

        Args:
            conversations_dir: Directory to store conversation history
        """
        self.conversations_dir = conversations_dir

        # Create conversations directory if it doesn't exist
        Path(conversations_dir).mkdir(parents=True, exist_ok=True)

        # Initialise conversations index
        self.conversations_index_file = os.path.join(
            conversations_dir, "conversations_index.json"
        )
        self.conversations_index = self._load_conversations_index()

    def _load_conversations_index(self) -> Dict[str, Any]:
        """
        Load the conversations index file.

        Returns:
            Dictionary with conversation index information
        """
        if os.path.exists(self.conversations_index_file):
            with open(self.conversations_index_file, "r") as f:
                return json.load(f)
        else:
            # Initialise with empty index
            index = {"conversations": [], "current_conversation": None}
            self._save_conversations_index(index)
            return index

    def _save_conversations_index(self, index: Dict[str, Any]) -> None:
        """
        Save the conversations index file.

        Args:
            index: Dictionary with conversation index information
        """
        with open(self.conversations_index_file, "w") as f:
            json.dump(index, f, indent=2)

    def create_conversation(self, title: str = None, dataset_id: str = None) -> str:
        """
        Create a new conversation.

        Args:
            title: Title for the conversation
            dataset_id: ID of the dataset used for the conversation

        Returns:
            ID of the created conversation
        """
        # Generate ID and timestamp
        conversation_id = f"conversation_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        timestamp = datetime.now().isoformat()

        # Generate title if not provided
        if title is None:
            title = f"Conversation {timestamp}"

        # Create conversation object
        conversation = {
            "id": conversation_id,
            "title": title,
            "dataset_id": dataset_id,
            "created_at": timestamp,
            "updated_at": timestamp,
            "messages": [],
        }

        # Save to file
        self._save_conversation(conversation)

        # Add to index
        self.conversations_index["conversations"].append(
            {
                "id": conversation_id,
                "title": title,
                "dataset_id": dataset_id,
                "created_at": timestamp,
                "updated_at": timestamp,
                "message_count": 0,
            }
        )

        # Set as current conversation
        self.conversations_index["current_conversation"] = conversation_id

        # Save index
        self._save_conversations_index(self.conversations_index)

        return conversation_id

    def _save_conversation(self, conversation: Dict[str, Any]) -> None:
        """
        Save a conversation to file.

        Args:
            conversation: Conversation object to save
        """
        conversation_file = os.path.join(
            self.conversations_dir, f"{conversation['id']}.json"
        )
        with open(conversation_file, "w") as f:
            json.dump(conversation, f, indent=2)

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        processing_time: float = None,
        chart_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Add a message to a conversation.

        Args:
            conversation_id: ID of the conversation
            role: Role of the sender (user/assistant/system)
            content: Content of the message
            processing_time: Processing time in seconds (for assistant messages)
            chart_data: Chart data if any

        Returns:
            The added message
        """
        # Load conversation
        conversation = self.get_conversation(conversation_id)

        if conversation is None:
            raise ValueError(f"Conversation with ID '{conversation_id}' not found.")

        # Create message
        timestamp = datetime.now().isoformat()
        message = {
            "id": f"msg_{len(conversation['messages']) + 1}",
            "role": role,
            "content": content,
            "timestamp": timestamp,
        }

        # Add optional fields
        if processing_time is not None:
            message["processing_time"] = processing_time

        if chart_data is not None:
            message["chart_data"] = chart_data

        # Add to conversation
        conversation["messages"].append(message)
        conversation["updated_at"] = timestamp

        # Save conversation
        self._save_conversation(conversation)

        # Update index
        for conv in self.conversations_index["conversations"]:
            if conv["id"] == conversation_id:
                conv["updated_at"] = timestamp
                conv["message_count"] = len(conversation["messages"])
                break

        self._save_conversations_index(self.conversations_index)

        return message

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Conversation object or None if not found
        """
        conversation_file = os.path.join(
            self.conversations_dir, f"{conversation_id}.json"
        )

        if not os.path.exists(conversation_file):
            return None

        with open(conversation_file, "r") as f:
            return json.load(f)

    def get_conversations_list(self) -> List[Dict[str, Any]]:
        """
        Get the list of all conversations.

        Returns:
            List of conversation metadata
        """
        return sorted(
            self.conversations_index["conversations"],
            key=lambda x: x["updated_at"],
            reverse=True,
        )

    def get_current_conversation(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active conversation.

        Returns:
            Current conversation object or None if no active conversation
        """
        current_id = self.conversations_index.get("current_conversation")

        if current_id is None:
            return None

        return self.get_conversation(current_id)

    def set_current_conversation(self, conversation_id: str) -> bool:
        """
        Set the current active conversation.

        Args:
            conversation_id: ID of the conversation to set as current

        Returns:
            True if successful, False otherwise
        """
        # Check if conversation exists
        if not os.path.exists(
            os.path.join(self.conversations_dir, f"{conversation_id}.json")
        ):
            return False

        # Set as current
        self.conversations_index["current_conversation"] = conversation_id

        # Save index
        self._save_conversations_index(self.conversations_index)

        return True

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: ID of the conversation to delete

        Returns:
            True if successful, False otherwise
        """
        conversation_file = os.path.join(
            self.conversations_dir, f"{conversation_id}.json"
        )

        if not os.path.exists(conversation_file):
            return False

        # Delete file
        os.remove(conversation_file)

        # Update index
        self.conversations_index["conversations"] = [
            conv
            for conv in self.conversations_index["conversations"]
            if conv["id"] != conversation_id
        ]

        # If this was the current conversation, update current conversation
        if self.conversations_index["current_conversation"] == conversation_id:
            if self.conversations_index["conversations"]:
                self.conversations_index["current_conversation"] = (
                    self.conversations_index["conversations"][0]["id"]
                )
            else:
                self.conversations_index["current_conversation"] = None

        # Save index
        self._save_conversations_index(self.conversations_index)

        return True

    def export_conversation(
        self, conversation_id: str, format: str = "json", file_path: str = None
    ) -> str:
        """
        Export a conversation to a file.

        Args:
            conversation_id: ID of the conversation to export
            format: Export format (json, markdown, csv, html)
            file_path: Path where to save the file (optional)

        Returns:
            Path to the exported file
        """
        conversation = self.get_conversation(conversation_id)

        if conversation is None:
            raise ValueError(f"Conversation with ID '{conversation_id}' not found.")

        # Generate default file path if not provided
        if file_path is None:
            export_dir = os.path.join(self.conversations_dir, "exports")
            Path(export_dir).mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_path = os.path.join(
                export_dir, f"{conversation['title']}_{timestamp}.{format}"
            )

        # Export based on format
        if format == "json":
            with open(file_path, "w") as f:
                json.dump(conversation, f, indent=2)

        elif format == "markdown":
            with open(file_path, "w") as f:
                f.write(f"# {conversation['title']}\n\n")
                f.write(f"Created: {conversation['created_at']}\n\n")

                for msg in conversation["messages"]:
                    role_display = {
                        "user": "User",
                        "assistant": "Assistant",
                        "system": "System",
                    }
                    f.write(f"## {role_display.get(msg['role'], msg['role'])}\n\n")
                    f.write(f"{msg['content']}\n\n")

                    if "processing_time" in msg:
                        f.write(f"*Processed in {msg['processing_time']} seconds*\n\n")

                    if "chart_data" in msg and msg["chart_data"]:
                        f.write(
                            f"*This message includes a chart that cannot be displayed in markdown*\n\n"
                        )

        elif format == "csv":
            with open(file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["ID", "Role", "Content", "Timestamp", "Processing Time"]
                )

                for msg in conversation["messages"]:
                    writer.writerow(
                        [
                            msg["id"],
                            msg["role"],
                            msg["content"],
                            msg["timestamp"],
                            msg.get("processing_time", ""),
                        ]
                    )

        elif format == "html":
            with open(file_path, "w") as f:
                f.write(
                    f"<!DOCTYPE html>\n<html>\n<head>\n<title>{conversation['title']}</title>\n"
                )
                f.write("<style>\n")
                f.write("body { font-family: Arial, sans-serif; margin: 20px; }\n")
                f.write(
                    ".user { background-color: #e8f4ff; padding: 10px; margin: 10px 0; border-radius: 5px; }\n"
                )
                f.write(
                    ".assistant { background-color: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; }\n"
                )
                f.write(
                    ".system { background-color: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }\n"
                )
                f.write("</style>\n</head>\n<body>\n")

                f.write(f"<h1>{conversation['title']}</h1>\n")
                f.write(f"<p>Created: {conversation['created_at']}</p>\n")

                for msg in conversation["messages"]:
                    f.write(f"<div class='{msg['role']}'>\n")
                    f.write(f"<h3>{msg['role'].capitalize()}</h3>\n")

                    # Convert markdown to HTML
                    content_html = self.markdown_to_html(msg["content"])
                    f.write(f"<div>{content_html}</div>\n")

                    if "processing_time" in msg:
                        f.write(
                            f"<p><em>Processed in {msg['processing_time']} seconds</em></p>\n"
                        )

                    if (
                        "chart_data" in msg
                        and msg["chart_data"]
                        and msg["chart_data"]["chart_type"] == "base64_image"
                    ):
                        img_data = msg["chart_data"]["image_data"]
                        f.write(
                            f"<img src='data:image/png;base64,{img_data}' alt='Chart' style='max-width: 100%;' />\n"
                        )

                    f.write("</div>\n")

                f.write("</body>\n</html>")

        else:
            raise ValueError(f"Unsupported export format: {format}")

        return file_path

    def markdown_to_html(self, markdown_text: str) -> str:
        """
        Convert markdown text to HTML (simple implementation).

        Args:
            markdown_text: Markdown text to convert

        Returns:
            HTML representation of the markdown
        """
        html = markdown_text

        # Convert headers
        html = re.sub(r"^# (.*?)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.*?)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)

        # Convert bold
        html = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html)

        # Convert italic
        html = re.sub(r"\*(.*?)\*", r"<em>\1</em>", html)

        # Convert code blocks
        html = re.sub(
            r"```(.*?)```", r"<pre><code>\1</code></pre>", html, flags=re.DOTALL
        )

        # Convert inline code
        html = re.sub(r"`(.*?)`", r"<code>\1</code>", html)

        # Convert paragraphs
        html = re.sub(r"\n\n", r"</p><p>", html)
        html = f"<p>{html}</p>"

        return html

    def generate_follow_up_questions(
        self, conversation_id: str, num_questions: int = 3
    ) -> List[str]:
        """
        Generate follow-up question suggestions based on conversation history.

        Args:
            conversation_id: ID of the conversation
            num_questions: Number of follow-up questions to generate

        Returns:
            List of follow-up question suggestions
        """
        # This is a simplified implementation with predefined follow-up questions
        # In a real implementation, this would use the agent to generate contextual follow-up questions

        conversation = self.get_conversation(conversation_id)

        if conversation is None or not conversation["messages"]:
            return []

        # Get the last few messages to provide context
        last_messages = conversation["messages"][-3:]

        # Get the most recent question from the user
        last_user_message = None
        for msg in reversed(conversation["messages"]):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break

        if not last_user_message:
            return []

        # Simple keyword-based approach for demonstration
        follow_ups = []

        # Questions based on common themes
        if "segment" in last_user_message.lower():
            follow_ups.append(
                "Can you compare the profit margins across different segments?"
            )
            follow_ups.append(
                "What factors are driving the performance in this segment?"
            )
            follow_ups.append("How does the discount strategy vary across segments?")

        elif "country" in last_user_message.lower():
            follow_ups.append("Which products perform best in this country?")
            follow_ups.append(
                "How does the profit margin in this country compare to others?"
            )
            follow_ups.append("Are there seasonal trends specific to this country?")

        elif "product" in last_user_message.lower():
            follow_ups.append("Which segment has the highest sales for this product?")
            follow_ups.append(
                "How does the pricing strategy affect this product's performance?"
            )
            follow_ups.append(
                "Is this product's performance consistent across different countries?"
            )

        elif "discount" in last_user_message.lower():
            follow_ups.append("Which segment is most sensitive to discounts?")
            follow_ups.append(
                "What is the optimal discount level for maximizing profit?"
            )
            follow_ups.append(
                "How do discount strategies vary across different products?"
            )

        elif (
            "trend" in last_user_message.lower() or "time" in last_user_message.lower()
        ):
            follow_ups.append("Are there any seasonal patterns in the data?")
            follow_ups.append("Which segment shows the most growth over time?")
            follow_ups.append("How stable are profit margins throughout the year?")

        # Default follow-up questions if none of the above keywords match
        if not follow_ups:
            follow_ups = [
                "What are the top factors driving profitability in this dataset?",
                "Can you identify any anomalies or outliers in the data?",
                "How do discount strategies impact overall profitability?",
                "Which segments show the most potential for improvement?",
                "What insights can you provide about the relationship between sales volume and profit margin?",
            ]

        # Return up to the requested number of questions
        return follow_ups[:num_questions]
