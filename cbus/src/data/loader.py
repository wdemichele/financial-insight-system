"""
Data Loader Module for Financial Analysis System

This module handles loading and preprocessing the financial dataset.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


class FinancialDataLoader:
    """
    Handles loading and preprocessing financial data for the multi-agent system.
    """

    def __init__(self, file_path: str):
        """
        Initialise the data loader.

        Args:
            file_path: Path to the financial data Excel file
        """
        self.file_path = file_path
        self.data = None
        self.summary_stats = {}

    def load_data(self) -> pd.DataFrame:
        """
        Load the financial data from Excel file and clean column names.

        Returns:
            DataFrame containing the cleaned financial data
        """
        print(f"Loading data from {self.file_path}")

        # Load the Excel file
        self.data = pd.read_excel(self.file_path)

        # Clean column names (strip whitespace)
        self.data.columns = [
            col.strip() if isinstance(col, str) else col for col in self.data.columns
        ]

        print(f"Loaded {len(self.data)} rows with {len(self.data.columns)} columns")
        return self.data

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Calculate summary statistics for the dataset.

        Returns:
            Dictionary containing summary statistics
        """
        if self.data is None:
            self.load_data()

        # Basic dataset information
        self.summary_stats = {
            "row_count": len(self.data),
            "column_count": len(self.data.columns),
            "columns": self.data.columns.tolist(),
            "missing_values": self.data.isnull().sum().to_dict(),
            "total_sales": self.data["Sales"].sum(),
            "total_profit": self.data["Profit"].sum(),
            "overall_profit_margin": (
                self.data["Profit"].sum() / self.data["Sales"].sum()
            )
            * 100,
        }

        # Segment analysis
        segment_stats = (
            self.data.groupby("Segment")
            .agg({"Sales": "sum", "Profit": "sum", "Units Sold": "sum"})
            .reset_index()
        )

        segment_stats["Profit Margin"] = (
            segment_stats["Profit"] / segment_stats["Sales"]
        ) * 100
        self.summary_stats["segment_analysis"] = segment_stats.to_dict(orient="records")

        # Country analysis
        country_stats = (
            self.data.groupby("Country")
            .agg({"Sales": "sum", "Profit": "sum", "Units Sold": "sum"})
            .reset_index()
        )

        country_stats["Profit Margin"] = (
            country_stats["Profit"] / country_stats["Sales"]
        ) * 100
        self.summary_stats["country_analysis"] = country_stats.to_dict(orient="records")

        # Product analysis
        product_stats = (
            self.data.groupby("Product")
            .agg({"Sales": "sum", "Profit": "sum", "Units Sold": "sum"})
            .reset_index()
        )

        product_stats["Profit Margin"] = (
            product_stats["Profit"] / product_stats["Sales"]
        ) * 100
        self.summary_stats["product_analysis"] = product_stats.to_dict(orient="records")

        # Discount band analysis
        discount_stats = (
            self.data.groupby("Discount Band")
            .agg(
                {
                    "Sales": "sum",
                    "Profit": "sum",
                    "Discounts": "mean",
                    "Units Sold": "sum",
                }
            )
            .reset_index()
        )

        discount_stats["Profit Margin"] = (
            discount_stats["Profit"] / discount_stats["Sales"]
        ) * 100
        self.summary_stats["discount_analysis"] = discount_stats.to_dict(
            orient="records"
        )

        # Monthly trends
        # Ensure proper ordering of months
        month_order = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

        self.data["Month Name"] = pd.Categorical(
            self.data["Month Name"], categories=month_order, ordered=True
        )
        monthly_stats = (
            self.data.groupby("Month Name")
            .agg({"Sales": "sum", "Profit": "sum", "Units Sold": "sum"})
            .reset_index()
        )

        self.summary_stats["monthly_analysis"] = monthly_stats.to_dict(orient="records")

        return self.summary_stats

    def get_segment_country_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Create a matrix of Segment x Country for profit analysis.

        Returns:
            Nested dictionary with segment->country->profit mapping
        """
        if self.data is None:
            self.load_data()

        pivot_table = self.data.pivot_table(
            index="Segment", columns="Country", values="Profit", aggfunc="sum"
        )

        # Convert to nested dict for easier consumption by agents
        result = {}
        for segment in pivot_table.index:
            result[segment] = {}
            for country in pivot_table.columns:
                result[segment][country] = float(pivot_table.loc[segment, country])

        return result

    def get_correlation_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix for numerical columns.

        Returns:
            Dictionary containing correlation coefficients
        """
        if self.data is None:
            self.load_data()

        numerical_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
        correlation = self.data[numerical_cols].corr().round(3)

        # Convert to nested dict
        result = {}
        for col1 in correlation.index:
            result[col1] = {}
            for col2 in correlation.columns:
                result[col1][col2] = float(correlation.loc[col1, col2])

        return result

    def save_summary_to_json(self, output_path: str = "data_summary.json") -> str:
        """
        Save the summary statistics to a JSON file.

        Args:
            output_path: Path where to save the JSON file

        Returns:
            Path to the saved JSON file
        """
        if not self.summary_stats:
            self.get_summary_statistics()

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Convert any numpy types to Python native types for JSON serialisation
        def convert_to_serialisable(obj):
            if isinstance(
                obj,
                (
                    np.int_,
                    np.intc,
                    np.intp,
                    np.int8,
                    np.int16,
                    np.int32,
                    np.int64,
                    np.uint8,
                    np.uint16,
                    np.uint32,
                    np.uint64,
                ),
            ):
                return int(obj)
            elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, pd.Series):
                return obj.tolist()
            elif isinstance(obj, pd.DataFrame):
                return obj.to_dict(orient="records")
            return obj

        # Process the summary stats for serialisation
        serialisable_stats = json.loads(
            json.dumps(self.summary_stats, default=convert_to_serialisable)
        )

        # Save to file
        with open(output_path, "w") as f:
            json.dump(serialisable_stats, f, indent=2)

        print(f"Summary statistics saved to {output_path}")
        return output_path

    def analyze_segment(self, segment_name: str) -> Dict[str, Any]:
        """
        Perform detailed analysis for a specific segment.

        Args:
            segment_name: Name of the segment to analyze

        Returns:
            Dictionary with detailed segment analysis
        """
        if self.data is None:
            self.load_data()

        # Filter data for the specified segment
        segment_data = self.data[self.data["Segment"] == segment_name]

        if len(segment_data) == 0:
            return {"error": f"Segment '{segment_name}' not found in the dataset"}

        # Perform analysis
        result = {
            "segment_name": segment_name,
            "record_count": len(segment_data),
            "total_sales": float(segment_data["Sales"].sum()),
            "total_profit": float(segment_data["Profit"].sum()),
            "profit_margin": float(
                (segment_data["Profit"].sum() / segment_data["Sales"].sum()) * 100
            ),
            "avg_sale_price": float(segment_data["Sale Price"].mean()),
            "avg_discount": float(segment_data["Discounts"].mean()),
        }

        # Country breakdown
        country_breakdown = (
            segment_data.groupby("Country")
            .agg({"Sales": "sum", "Profit": "sum"})
            .reset_index()
        )

        country_breakdown["Profit Margin"] = (
            country_breakdown["Profit"] / country_breakdown["Sales"]
        ) * 100
        result["country_breakdown"] = country_breakdown.to_dict(orient="records")

        # Product breakdown
        product_breakdown = (
            segment_data.groupby("Product")
            .agg({"Sales": "sum", "Profit": "sum"})
            .reset_index()
        )

        product_breakdown["Profit Margin"] = (
            product_breakdown["Profit"] / product_breakdown["Sales"]
        ) * 100
        result["product_breakdown"] = product_breakdown.to_dict(orient="records")

        # Monthly trend
        monthly_trend = (
            segment_data.groupby("Month Name")
            .agg({"Sales": "sum", "Profit": "sum"})
            .reset_index()
        )

        result["monthly_trend"] = monthly_trend.to_dict(orient="records")

        return result

    def analyze_product(self, product_name: str) -> Dict[str, Any]:
        """
        Perform detailed analysis for a specific product.

        Args:
            product_name: Name of the product to analyze

        Returns:
            Dictionary with detailed product analysis
        """
        if self.data is None:
            self.load_data()

        # Filter data for the specified product
        product_data = self.data[self.data["Product"] == product_name]

        if len(product_data) == 0:
            return {"error": f"Product '{product_name}' not found in the dataset"}

        # Perform analysis
        result = {
            "product_name": product_name,
            "record_count": len(product_data),
            "total_sales": float(product_data["Sales"].sum()),
            "total_profit": float(product_data["Profit"].sum()),
            "profit_margin": float(
                (product_data["Profit"].sum() / product_data["Sales"].sum()) * 100
            ),
            "avg_sale_price": float(product_data["Sale Price"].mean()),
            "avg_manufacturing_price": float(
                product_data["Manufacturing Price"].mean()
            ),
        }

        # Segment breakdown
        segment_breakdown = (
            product_data.groupby("Segment")
            .agg({"Sales": "sum", "Profit": "sum"})
            .reset_index()
        )

        segment_breakdown["Profit Margin"] = (
            segment_breakdown["Profit"] / segment_breakdown["Sales"]
        ) * 100
        result["segment_breakdown"] = segment_breakdown.to_dict(orient="records")

        # Country breakdown
        country_breakdown = (
            product_data.groupby("Country")
            .agg({"Sales": "sum", "Profit": "sum"})
            .reset_index()
        )

        country_breakdown["Profit Margin"] = (
            country_breakdown["Profit"] / country_breakdown["Sales"]
        ) * 100
        result["country_breakdown"] = country_breakdown.to_dict(orient="records")

        return result

    def analyze_discount_impact(self) -> Dict[str, Any]:
        """
        Analyze the impact of discounts on profit margins.

        Returns:
            Dictionary with discount impact analysis
        """
        if self.data is None:
            self.load_data()

        # Group by discount band
        discount_analysis = (
            self.data.groupby("Discount Band")
            .agg(
                {
                    "Sales": "sum",
                    "Profit": "sum",
                    "Discounts": ["mean", "sum"],
                    "Units Sold": "sum",
                }
            )
            .reset_index()
        )

        # Make column names more accessible
        discount_analysis.columns = [
            "_".join(col).strip() if isinstance(col, tuple) else col
            for col in discount_analysis.columns
        ]

        # Calculate profit margins
        discount_analysis["Profit_Margin"] = (
            discount_analysis["Profit_sum"] / discount_analysis["Sales_sum"]
        ) * 100

        # Calculate discount as percentage of sales
        discount_analysis["Discount_Percentage"] = (
            discount_analysis["Discounts_sum"] / discount_analysis["Sales_sum"]
        ) * 100

        # Convert to dictionary
        result = {
            "discount_band_analysis": discount_analysis.to_dict(orient="records"),
        }

        # Add segment-specific discount analysis
        segment_discount = (
            self.data.groupby(["Segment", "Discount Band"])
            .agg({"Sales": "sum", "Profit": "sum", "Discounts": "sum"})
            .reset_index()
        )

        segment_discount["Profit_Margin"] = (
            segment_discount["Profit"] / segment_discount["Sales"]
        ) * 100
        segment_discount["Discount_Percentage"] = (
            segment_discount["Discounts"] / segment_discount["Sales"]
        ) * 100

        result["segment_discount_analysis"] = segment_discount.to_dict(orient="records")

        return result


if __name__ == "__main__":
    # Test the loader
    loader = FinancialDataLoader("Financial Sample.xlsx")
    df = loader.load_data()
    print(df.head())

    # Get summary statistics
    stats = loader.get_summary_statistics()
    print("Summary statistics generated")

    # Save to JSON
    loader.save_summary_to_json("data/summary_stats.json")
