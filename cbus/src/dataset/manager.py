"""
Dataset Management module for Financial Analysis System.
Handles uploading, validation, and switching between datasets.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


class DatasetManager:
    """
    Manages different financial datasets for the system.
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialise the DatasetManager.

        Args:
            data_dir: Directory to store datasets
        """
        self.data_dir = data_dir
        self.datasets_index_file = os.path.join(data_dir, "datasets_index.json")
        self.datasets_index = self._load_datasets_index()

        # Create data directory if it doesn't exist
        Path(data_dir).mkdir(parents=True, exist_ok=True)

    def _load_datasets_index(self) -> Dict[str, Any]:
        """
        Load the datasets index file.

        Returns:
            Dictionary with dataset information
        """
        if os.path.exists(self.datasets_index_file):
            with open(self.datasets_index_file, "r") as f:
                return json.load(f)
        else:
            # Initialise with empty index
            index = {"datasets": [], "current_dataset": None}
            self._save_datasets_index(index)
            return index

    def _save_datasets_index(self, index: Dict[str, Any]) -> None:
        """
        Save the datasets index file.

        Args:
            index: Dictionary with dataset information
        """
        with open(self.datasets_index_file, "w") as f:
            json.dump(index, f, indent=2)

    def get_datasets_list(self) -> List[Dict[str, Any]]:
        """
        Get the list of available datasets.

        Returns:
            List of dictionaries with dataset information
        """
        return self.datasets_index["datasets"]

    def get_current_dataset(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active dataset.

        Returns:
            Dictionary with current dataset information or None if no dataset is active
        """
        current_id = self.datasets_index.get("current_dataset")

        if current_id is None:
            return None

        # Find the dataset with the matching ID
        for dataset in self.datasets_index["datasets"]:
            if dataset["id"] == current_id:
                return dataset

        return None

    def validate_dataset(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if the file is a valid financial dataset.

        Args:
            file_path: Path to the Excel file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to read the Excel file
            df = pd.read_excel(file_path)

            # Check if dataframe is empty
            if df.empty:
                return False, "The file contains no data."

            # Check for required columns
            required_columns = ["Segment", "Country", "Product", "Sales", "Profit"]
            for col in required_columns:
                matching_cols = [
                    c
                    for c in df.columns
                    if col.lower() == c.lower() or col.lower() in c.lower()
                ]
                if not matching_cols:
                    return False, f"Required column '{col}' not found in the dataset."

            return True, "Dataset is valid."

        except Exception as e:
            return False, f"Error validating dataset: {str(e)}"

    def add_dataset(
        self, file_path: str, name: str, description: str = ""
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Add a new dataset to the system.

        Args:
            file_path: Path to the Excel file
            name: Name for the dataset
            description: Description of the dataset

        Returns:
            Tuple of (success, message, dataset_id if successful)
        """
        # Validate the dataset
        is_valid, error_message = self.validate_dataset(file_path)

        if not is_valid:
            return False, error_message, None

        # Generate a unique ID for the dataset
        dataset_id = f"dataset_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Create a copy of the file in the data directory
        file_name = os.path.basename(file_path)
        extension = os.path.splitext(file_name)[1]
        new_file_name = f"{dataset_id}{extension}"
        new_file_path = os.path.join(self.data_dir, new_file_name)

        try:
            shutil.copy2(file_path, new_file_path)
        except Exception as e:
            return False, f"Error copying file: {str(e)}", None

        # Add the dataset to the index
        dataset_info = {
            "id": dataset_id,
            "name": name,
            "description": description,
            "file_name": new_file_name,
            "file_path": new_file_path,
            "date_added": datetime.now().isoformat(),
            "last_used": None,
        }

        self.datasets_index["datasets"].append(dataset_info)

        # If this is the first dataset, set it as current
        if len(self.datasets_index["datasets"]) == 1:
            self.datasets_index["current_dataset"] = dataset_id

        # Save the updated index
        self._save_datasets_index(self.datasets_index)

        return True, "Dataset added successfully.", dataset_id

    def set_current_dataset(self, dataset_id: str) -> Tuple[bool, str]:
        """
        Set the currently active dataset.

        Args:
            dataset_id: ID of the dataset to set as current

        Returns:
            Tuple of (success, message)
        """
        # Check if the dataset exists
        dataset_exists = False
        for dataset in self.datasets_index["datasets"]:
            if dataset["id"] == dataset_id:
                dataset_exists = True
                # Update last used timestamp
                dataset["last_used"] = datetime.now().isoformat()
                break

        if not dataset_exists:
            return False, f"Dataset with ID '{dataset_id}' not found."

        # Set as current dataset
        self.datasets_index["current_dataset"] = dataset_id

        # Save the updated index
        self._save_datasets_index(self.datasets_index)

        return True, f"Dataset '{dataset_id}' set as current."

    def remove_dataset(self, dataset_id: str) -> Tuple[bool, str]:
        """
        Remove a dataset from the system.

        Args:
            dataset_id: ID of the dataset to remove

        Returns:
            Tuple of (success, message)
        """
        # Find the dataset
        dataset_to_remove = None
        for dataset in self.datasets_index["datasets"]:
            if dataset["id"] == dataset_id:
                dataset_to_remove = dataset
                break

        if dataset_to_remove is None:
            return False, f"Dataset with ID '{dataset_id}' not found."

        # Remove the file
        try:
            os.remove(dataset_to_remove["file_path"])
        except Exception as e:
            return False, f"Error removing file: {str(e)}"

        # Remove from the index
        self.datasets_index["datasets"].remove(dataset_to_remove)

        # If this was the current dataset, update the current dataset
        if self.datasets_index["current_dataset"] == dataset_id:
            if self.datasets_index["datasets"]:
                self.datasets_index["current_dataset"] = self.datasets_index[
                    "datasets"
                ][0]["id"]
            else:
                self.datasets_index["current_dataset"] = None

        # Save the updated index
        self._save_datasets_index(self.datasets_index)

        return True, f"Dataset '{dataset_id}' removed successfully."

    def get_dataset_file_path(self, dataset_id: Optional[str] = None) -> Optional[str]:
        """
        Get the file path for a dataset.

        Args:
            dataset_id: ID of the dataset or None for current dataset

        Returns:
            File path or None if not found
        """
        if dataset_id is None:
            current_dataset = self.get_current_dataset()
            if current_dataset is None:
                return None
            return current_dataset["file_path"]

        # Find the dataset with the specified ID
        for dataset in self.datasets_index["datasets"]:
            if dataset["id"] == dataset_id:
                return dataset["file_path"]

        return None
