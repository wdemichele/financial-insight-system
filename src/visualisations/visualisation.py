"""
Visualisation module for Financial Analysis System.
Generates chart data for the web UI.
"""

import base64
import io
import json
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Set style for visualisations
plt.style.use("ggplot")
sns.set_palette("muted")


class VisualisationGenerator:
    """
    Generates visualisation data for the financial dataset.
    """

    def __init__(self, data_loader):
        """
        Initialise the VisualisationGenerator.

        Args:
            data_loader: FinancialDataLoader instance with loaded data
        """
        self.data_loader = data_loader
        self.data = data_loader.data

    def generate_chart_data(self, chart_type: str, **kwargs) -> Dict[str, Any]:
        """
        Generate data for the specified chart type.

        Args:
            chart_type: Type of chart to generate
            **kwargs: Additional parameters for the chart

        Returns:
            Dictionary with chart data and metadata
        """
        chart_generators = {
            "segment_profit": self.segment_profit_chart,
            "segment_profit_margin": self.segment_profit_margin_chart,
            "monthly_trend": self.monthly_trend_chart,
            "country_profit": self.country_profit_chart,
            "product_profit": self.product_profit_chart,
            "discount_impact": self.discount_impact_chart,
            "segment_country_heatmap": self.segment_country_heatmap,
            "correlation_heatmap": self.correlation_heatmap,
        }

        if chart_type not in chart_generators:
            raise ValueError(f"Unknown chart type: {chart_type}")

        return chart_generators[chart_type](**kwargs)

    def create_base64_chart(self, plot_func, **kwargs) -> Dict[str, Any]:
        """
        Create a base64 encoded image from a matplotlib plot function.

        Args:
            plot_func: Function that creates the plot
            **kwargs: Additional parameters for the plot function

        Returns:
            Dictionary with base64 encoded image and metadata
        """
        # Create a new figure
        plt.figure(figsize=(10, 6))

        # Call the plot function
        plot_result = plot_func(**kwargs)

        # Add title and labels if provided
        if "title" in kwargs:
            plt.title(kwargs["title"])
        if "xlabel" in kwargs:
            plt.xlabel(kwargs["xlabel"])
        if "ylabel" in kwargs:
            plt.ylabel(kwargs["ylabel"])

        # Ensure tight layout
        plt.tight_layout()

        # Save to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100)
        buf.seek(0)

        # Convert to base64
        img_str = base64.b64encode(buf.read()).decode("utf-8")

        # Close the figure to free memory
        plt.close()

        # Return the result
        result = {
            "chart_type": "base64_image",
            "image_data": img_str,
            "content_type": "image/png",
        }

        # Add any additional data from the plot result
        if isinstance(plot_result, dict):
            result.update(plot_result)

        return result

    def segment_profit_chart(self, **kwargs) -> Dict[str, Any]:
        """
        Create a chart showing profit by segment.

        Returns:
            Dictionary with chart data
        """

        def plot(**kwargs):
            segment_data = (
                self.data.groupby("Segment")["Profit"]
                .sum()
                .sort_values(ascending=False)
            )
            sns.barplot(x=segment_data.index, y=segment_data.values)
            plt.xticks(rotation=45)
            return {"data": segment_data.to_dict()}

        return self.create_base64_chart(
            plot, title="Total Profit by Segment", ylabel="Profit", **kwargs
        )

    def segment_profit_margin_chart(self, **kwargs) -> Dict[str, Any]:
        """
        Create a chart showing profit margin by segment.

        Returns:
            Dictionary with chart data
        """

        def plot(**kwargs):
            segment_data = self.data.groupby("Segment").agg(
                {"Profit": "sum", "Sales": "sum"}
            )

            segment_data["Profit Margin (%)"] = (
                segment_data["Profit"] / segment_data["Sales"]
            ) * 100
            segment_data = segment_data.sort_values(
                "Profit Margin (%)", ascending=False
            )

            sns.barplot(x=segment_data.index, y=segment_data["Profit Margin (%)"])
            plt.xticks(rotation=45)

            return {"data": segment_data["Profit Margin (%)"].to_dict()}

        return self.create_base64_chart(
            plot, title="Profit Margin by Segment", ylabel="Profit Margin (%)", **kwargs
        )

    def monthly_trend_chart(self, **kwargs) -> Dict[str, Any]:
        """
        Create a chart showing monthly sales and profit trends.

        Returns:
            Dictionary with chart data
        """

        def plot(**kwargs):
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

            # Convert to categorical for proper ordering
            self.data["Month Name"] = pd.Categorical(
                self.data["Month Name"], categories=month_order, ordered=True
            )

            # Group by month
            monthly_data = (
                self.data.groupby("Month Name")
                .agg({"Sales": "sum", "Profit": "sum"})
                .reset_index()
            )

            # Sort by the month order
            monthly_data = monthly_data.sort_values("Month Name")

            # Plot
            plt.plot(
                monthly_data["Month Name"],
                monthly_data["Sales"],
                marker="o",
                label="Sales",
            )
            plt.plot(
                monthly_data["Month Name"],
                monthly_data["Profit"],
                marker="o",
                label="Profit",
            )
            plt.xticks(rotation=45)
            plt.legend()

            return {
                "data": {
                    "months": monthly_data["Month Name"].tolist(),
                    "sales": monthly_data["Sales"].tolist(),
                    "profit": monthly_data["Profit"].tolist(),
                }
            }

        return self.create_base64_chart(
            plot, title="Monthly Sales and Profit Trends", ylabel="Amount", **kwargs
        )

    def country_profit_chart(self, **kwargs) -> Dict[str, Any]:
        """
        Create a chart showing profit by country.

        Returns:
            Dictionary with chart data
        """

        def plot(**kwargs):
            country_data = (
                self.data.groupby("Country")["Profit"]
                .sum()
                .sort_values(ascending=False)
            )
            sns.barplot(x=country_data.index, y=country_data.values)
            plt.xticks(rotation=45)
            return {"data": country_data.to_dict()}

        return self.create_base64_chart(
            plot, title="Total Profit by Country", ylabel="Profit", **kwargs
        )

    def product_profit_chart(self, **kwargs) -> Dict[str, Any]:
        """
        Create a chart showing profit by product.

        Returns:
            Dictionary with chart data
        """

        def plot(**kwargs):
            product_data = (
                self.data.groupby("Product")["Profit"]
                .sum()
                .sort_values(ascending=False)
            )
            sns.barplot(x=product_data.index, y=product_data.values)
            plt.xticks(rotation=45)
            return {"data": product_data.to_dict()}

        return self.create_base64_chart(
            plot, title="Total Profit by Product", ylabel="Profit", **kwargs
        )

    def discount_impact_chart(self, **kwargs) -> Dict[str, Any]:
        """
        Create a chart showing the impact of discounts on profit margin.

        Returns:
            Dictionary with chart data
        """

        def plot(**kwargs):
            discount_data = self.data.groupby("Discount Band").agg(
                {"Profit": "sum", "Sales": "sum", "Discounts": "mean"}
            )

            discount_data["Profit Margin (%)"] = (
                discount_data["Profit"] / discount_data["Sales"]
            ) * 100
            discount_data = discount_data.sort_values("Discounts", ascending=True)

            sns.barplot(x=discount_data.index, y=discount_data["Profit Margin (%)"])

            return {"data": discount_data["Profit Margin (%)"].to_dict()}

        return self.create_base64_chart(
            plot,
            title="Profit Margin by Discount Band",
            ylabel="Profit Margin (%)",
            **kwargs,
        )

    def segment_country_heatmap(self, **kwargs) -> Dict[str, Any]:
        """
        Create a heatmap showing profit by segment and country.

        Returns:
            Dictionary with chart data
        """

        def plot(**kwargs):
            pivot_data = self.data.pivot_table(
                index="Segment", columns="Country", values="Profit", aggfunc="sum"
            )

            sns.heatmap(pivot_data, annot=True, fmt=".0f", cmap="YlGnBu")

            return {
                "data": {
                    "segments": pivot_data.index.tolist(),
                    "countries": pivot_data.columns.tolist(),
                    "values": [
                        [
                            float(pivot_data.iloc[i, j])
                            for j in range(pivot_data.shape[1])
                        ]
                        for i in range(pivot_data.shape[0])
                    ],
                }
            }

        return self.create_base64_chart(
            plot, title="Profit by Segment and Country", **kwargs
        )

    def correlation_heatmap(self, **kwargs) -> Dict[str, Any]:
        """
        Create a correlation heatmap for numerical columns.

        Returns:
            Dictionary with chart data
        """

        def plot(**kwargs):
            numerical_cols = [
                "Sales",
                "Profit",
                "Units Sold",
                "Discounts",
                "COGS",
                "Manufacturing Price",
                "Sale Price",
                "Gross Sales",
            ]

            # Filter columns that actually exist in the dataframe
            available_cols = [col for col in numerical_cols if col in self.data.columns]

            corr_data = self.data[available_cols].corr().round(2)

            # Create a mask for the upper triangle
            mask = np.triu(np.ones_like(corr_data, dtype=bool))

            # Plot the heatmap
            sns.heatmap(
                corr_data,
                annot=True,
                cmap="coolwarm",
                mask=mask,
                fmt=".2f",
                linewidths=0.5,
            )

            return {
                "data": {
                    "columns": corr_data.columns.tolist(),
                    "values": corr_data.values.tolist(),
                }
            }

        return self.create_base64_chart(
            plot, title="Correlation Matrix of Numerical Variables", **kwargs
        )

    def generate_chart_for_question(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Automatically generate a relevant chart based on the question.

        Args:
            question: User's question

        Returns:
            Dictionary with chart data or None if no relevant chart
        """
        question_lower = question.lower()

        # Check for segment-related questions
        if any(keyword in question_lower for keyword in ["segment", "segments"]):
            if any(
                keyword in question_lower
                for keyword in ["margin", "margins", "percentage"]
            ):
                return self.segment_profit_margin_chart()
            else:
                return self.segment_profit_chart()

        # Check for country-related questions
        elif any(
            keyword in question_lower
            for keyword in ["country", "countries", "region", "regions"]
        ):
            if "segment" in question_lower:
                return self.segment_country_heatmap()
            else:
                return self.country_profit_chart()

        # Check for product-related questions
        elif any(keyword in question_lower for keyword in ["product", "products"]):
            return self.product_profit_chart()

        # Check for discount-related questions
        elif any(keyword in question_lower for keyword in ["discount", "discounts"]):
            return self.discount_impact_chart()

        # Check for time-related questions
        elif any(
            keyword in question_lower
            for keyword in ["month", "months", "time", "trend", "trends"]
        ):
            return self.monthly_trend_chart()

        # Check for correlation-related questions
        elif any(
            keyword in question_lower
            for keyword in ["correlation", "relationship", "compare", "comparison"]
        ):
            return self.correlation_heatmap()

        # Return None if no relevant chart
        return None
