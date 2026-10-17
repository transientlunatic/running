"""
Plotting utilities for race results visualization.

This module provides the KentigernPlot style and various race-specific
plotting functions based on the style used in the analysis notebooks.
"""

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.ticker as mtick
from matplotlib.mlab import GaussianKDE
import numpy as np
import pandas as pd
from typing import Optional, List, Tuple, Dict, Any


class KentigernPlot:
    """
    Context manager for creating plots with consistent Kentigern styling.

    This style features:
    - Custom color palette (blues and earth tones)
    - Dark blue background (#003B6B)
    - White text with outline effects
    - Consolas font
    - Minimal grid and spines

    Example:
        >>> with KentigernPlot(1, 1) as fig:
        ...     fig.axes[0].plot([1, 2, 3], [1, 4, 9])
        ...     fig.axes[0].set_xlabel("X values")
    """

    # Default color palette
    COLORS = ["#79C4F2", "#3BBCD9", "#038C8C", "#BDBF7E", "#8C3D20"]
    BACKGROUND_COLOR = "#003B6B"
    GRID_COLOR = "#00111F"

    def __init__(
        self,
        *plotlayout,
        figsize: Optional[Tuple[float, float]] = None,
        dpi: int = 300,
        colors: Optional[List[str]] = None,
    ):
        """
        Initialize a Kentigern-styled plot.

        Args:
            *plotlayout: Arguments passed to plt.subplots (e.g., 1, 1 for single plot)
            figsize: Figure size in inches (width, height). Defaults to golden ratio.
            dpi: Dots per inch for the figure
            colors: Custom color palette (uses default if None)
        """
        if figsize is None:
            figsize = (3 * 1.618, 3)  # Golden ratio

        self.colors = colors or self.COLORS
        self.f, self.ax = plt.subplots(*plotlayout, dpi=dpi, figsize=figsize)

        # Set color cycle for all axes
        for ax in self._get_all_axes():
            ax.set_prop_cycle("color", self.colors)

        # Store colors on figure for easy access
        self.f.colors = self.colors

    def _get_all_axes(self) -> List:
        """Get list of all axes (handles single or multiple axes)."""
        if isinstance(self.ax, np.ndarray):
            return self.ax.flatten()
        else:
            return [self.ax]

    def __enter__(self):
        """Enter context manager."""
        return self.f

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Exit context manager and apply styling."""
        for ax in self._get_all_axes():
            # Style axis labels
            ax.set_xlabel(
                ax.get_xlabel(),
                fontdict={"fontsize": 7, "fontfamily": "Consolas"},
                path_effects=[pe.Stroke(linewidth=1, foreground="w"), pe.Normal()],
            )
            ax.set_ylabel(
                ax.get_ylabel(),
                fontdict={"fontsize": 7, "fontfamily": "Consolas"},
                path_effects=[pe.Stroke(linewidth=1, foreground="w"), pe.Normal()],
            )

            # Hide spines
            for spine in ["top", "right", "bottom", "left"]:
                ax.spines[spine].set_visible(False)

            # Style tick labels
            for label in ax.get_xticklabels():
                label.set_fontproperties({"size": 6, "family": "Consolas"})
                label.set_path_effects(
                    [pe.Stroke(linewidth=1, foreground="w"), pe.Normal()]
                )

            for label in ax.get_yticklabels():
                label.set_fontproperties({"size": 6, "family": "Consolas"})
                label.set_path_effects(
                    [pe.Stroke(linewidth=1, foreground="w"), pe.Normal()]
                )

            # Set background and grid
            ax.grid(color="white", linewidth=0.15)
            ax.set_facecolor(self.BACKGROUND_COLOR)

        return self.f


class RacePlotter:
    """
    High-level plotting functions for race result analysis.

    Provides ready-to-use plotting methods for common race visualizations.
    """

    def __init__(self, use_kentigern_style: bool = True):
        """
        Initialize race plotter.

        Args:
            use_kentigern_style: Whether to use Kentigern styling by default
        """
        self.use_kentigern_style = use_kentigern_style

    def plot_finish_time_distribution(
        self,
        data: pd.DataFrame,
        time_column: str = "FinishTime (minutes)",
        bins: Optional[range] = None,
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        figsize: Optional[Tuple[float, float]] = None,
    ) -> plt.Figure:
        """
        Plot finish time distribution with KDE.

        Args:
            data: DataFrame with race results
            time_column: Column name containing finish times in minutes
            bins: Range for x-axis (default: 60-300 minutes)
            title: Plot title
            save_path: Path to save figure (if provided)
            figsize: Figure size override

        Returns:
            Matplotlib figure object
        """
        if bins is None:
            bins = range(60, 300, 1)

        if self.use_kentigern_style:
            with KentigernPlot(1, 1, figsize=figsize) as fig:
                ax = fig.axes[0]

                # Plot KDE
                kde = GaussianKDE(data[time_column].dropna())
                ax.fill_between(bins, 100 * kde(bins), alpha=0.3, color="#00111f")
                ax.plot(
                    bins,
                    100 * kde(bins),
                    color="black",
                    linewidth=1,
                    path_effects=[
                        pe.Stroke(linewidth=1.5, foreground="w"),
                        pe.Normal(),
                    ],
                )

                ax.set(yticklabels=[])
                ax.tick_params(left=False)
                ax.set_xlabel("Finish Time (minutes)")

                if title:
                    ax.set_title(title)

                fig.tight_layout()

                if save_path:
                    fig.savefig(save_path)

                return fig
        else:
            fig, ax = plt.subplots(1, 1, figsize=figsize or (8, 4))
            kde = GaussianKDE(data[time_column].dropna())
            ax.fill_between(bins, 100 * kde(bins), alpha=0.5)
            ax.set_xlabel("Finish Time (minutes)")
            ax.set_ylabel("Density")
            if title:
                ax.set_title(title)
            fig.tight_layout()
            if save_path:
                fig.savefig(save_path)
            return fig

    def plot_gender_comparison(
        self,
        data: pd.DataFrame,
        time_column: str = "FinishTime (minutes)",
        gender_column: str = "Gender",
        male_value: str = "M",
        female_value: str = "F",
        bins: Optional[range] = None,
        save_path: Optional[str] = None,
        figsize: Optional[Tuple[float, float]] = None,
    ) -> plt.Figure:
        """
        Plot finish time distributions by gender.

        Args:
            data: DataFrame with race results
            time_column: Column with finish times in minutes
            gender_column: Column with gender data
            male_value: Value representing male in gender column
            female_value: Value representing female in gender column
            bins: Range for x-axis
            save_path: Path to save figure
            figsize: Figure size override

        Returns:
            Matplotlib figure object
        """
        if bins is None:
            bins = range(120, 420, 1)

        # Extract gender-specific data
        # Handle category extraction if needed (e.g., "M40" -> "M")
        if gender_column == "Category":
            male_data = data[
                data[gender_column].apply(
                    lambda x: str(x)[-1] == male_value if pd.notna(x) else False
                )
            ]
            female_data = data[
                data[gender_column].apply(
                    lambda x: str(x)[-1] == female_value if pd.notna(x) else False
                )
            ]
        else:
            male_data = data[data[gender_column] == male_value]
            female_data = data[data[gender_column] == female_value]

        if self.use_kentigern_style:
            with KentigernPlot(1, 1, figsize=figsize or (4, 1)) as fig:
                ax = fig.axes[0]

                # Plot KDEs
                kde_male = GaussianKDE(male_data[time_column].dropna())
                kde_female = GaussianKDE(female_data[time_column].dropna())

                ax.fill_between(
                    bins, 100 * kde_male(bins), alpha=0.3, color="blue", label="Male"
                )
                ax.fill_between(
                    bins, 100 * kde_female(bins), alpha=0.3, color="red", label="Female"
                )

                ax.set(yticklabels=[])
                ax.tick_params(left=False)
                ax.set_xlabel("Finish Time (minutes)")
                ax.legend()

                fig.tight_layout()

                if save_path:
                    fig.savefig(save_path)

                return fig
        else:
            fig, ax = plt.subplots(1, 1, figsize=figsize or (8, 4))
            kde_male = GaussianKDE(male_data[time_column].dropna())
            kde_female = GaussianKDE(female_data[time_column].dropna())
            ax.fill_between(bins, 100 * kde_male(bins), alpha=0.3, label="Male")
            ax.fill_between(bins, 100 * kde_female(bins), alpha=0.3, label="Female")
            ax.set_xlabel("Finish Time (minutes)")
            ax.legend()
            fig.tight_layout()
            if save_path:
                fig.savefig(save_path)
            return fig

    def plot_cumulative_distribution(
        self,
        data: pd.DataFrame,
        time_column: str = "FinishTime (minutes)",
        bins: Optional[range] = None,
        labels: Optional[List[str]] = None,
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        figsize: Optional[Tuple[float, float]] = None,
    ) -> plt.Figure:
        """
        Plot cumulative finish time distribution.

        Args:
            data: DataFrame or list of DataFrames
            time_column: Column with finish times
            bins: Range for histogram bins
            labels: Labels for multiple datasets
            title: Plot title
            save_path: Path to save figure
            figsize: Figure size override

        Returns:
            Matplotlib figure object
        """
        if bins is None:
            bins = range(60, 240, 1)

        # Handle single or multiple datasets
        if isinstance(data, pd.DataFrame):
            datasets = [data]
            labels = labels or ["Data"]
        else:
            datasets = data
            labels = labels or [f"Dataset {i+1}" for i in range(len(datasets))]

        if self.use_kentigern_style:
            with KentigernPlot(1, 1, figsize=figsize or (4, 2)) as fig:
                ax = fig.axes[0]

                for dataset, label in zip(datasets, labels):
                    ax.hist(
                        dataset[time_column].dropna(),
                        bins=bins,
                        cumulative=True,
                        density=True,
                        histtype="step",
                        linewidth=1,
                        path_effects=[
                            pe.Stroke(linewidth=1.5, foreground="w"),
                            pe.Normal(),
                        ],
                        label=label,
                    )

                ax.set_xlim(bins[0], bins[-1])
                ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
                ax.set_xlabel("Finish Time (minutes)")
                ax.set_ylabel("Percentage finished")

                if len(datasets) > 1:
                    ax.legend(
                        loc="center right", prop={"size": 6, "family": "Consolas"}
                    )

                if title:
                    ax.set_title(title)

                fig.tight_layout()

                if save_path:
                    fig.savefig(save_path)

                return fig
        else:
            fig, ax = plt.subplots(1, 1, figsize=figsize or (8, 4))
            for dataset, label in zip(datasets, labels):
                ax.hist(
                    dataset[time_column].dropna(),
                    bins=bins,
                    cumulative=True,
                    density=True,
                    histtype="step",
                    label=label,
                )
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
            ax.set_xlabel("Finish Time (minutes)")
            ax.set_ylabel("Percentage finished")
            if len(datasets) > 1:
                ax.legend()
            if title:
                ax.set_title(title)
            fig.tight_layout()
            if save_path:
                fig.savefig(save_path)
            return fig

    def plot_histogram(
        self,
        data: pd.DataFrame,
        time_column: str = "FinishTime (minutes)",
        bins: Optional[range] = None,
        title: Optional[str] = None,
        save_path: Optional[str] = None,
        figsize: Optional[Tuple[float, float]] = None,
    ) -> plt.Figure:
        """
        Plot finish time histogram.

        Args:
            data: DataFrame with race results
            time_column: Column with finish times
            bins: Range for histogram bins
            title: Plot title
            save_path: Path to save figure
            figsize: Figure size override

        Returns:
            Matplotlib figure object
        """
        if bins is None:
            bins = range(60, 240, 1)

        if self.use_kentigern_style:
            with KentigernPlot(1, 1, figsize=figsize or (4, 2)) as fig:
                ax = fig.axes[0]

                ax.hist(
                    data[time_column].dropna(), bins=bins, alpha=0.5, color="#79C4F2"
                )
                ax.set(yticklabels=[])
                ax.tick_params(left=False)
                ax.set_xlabel("Finish Time (minutes)")

                if title:
                    ax.set_title(title)

                fig.tight_layout()

                if save_path:
                    fig.savefig(save_path)

                return fig
        else:
            fig, ax = plt.subplots(1, 1, figsize=figsize or (8, 4))
            ax.hist(data[time_column].dropna(), bins=bins, alpha=0.5)
            ax.set_xlabel("Finish Time (minutes)")
            ax.set_ylabel("Count")
            if title:
                ax.set_title(title)
            fig.tight_layout()
            if save_path:
                fig.savefig(save_path)
            return fig

    def plot_club_comparison(
        self,
        data: pd.DataFrame,
        time_column: str = "FinishTime (minutes)",
        club_column: str = "Club",
        bins: Optional[range] = None,
        save_path: Optional[str] = None,
        figsize: Optional[Tuple[float, float]] = None,
    ) -> plt.Figure:
        """
        Compare finish times between club and non-club runners.

        Args:
            data: DataFrame with race results
            time_column: Column with finish times
            club_column: Column indicating club membership
            bins: Range for x-axis
            save_path: Path to save figure
            figsize: Figure size override

        Returns:
            Matplotlib figure object
        """
        if bins is None:
            bins = range(60, 240, 1)

        club_runners = data[~data[club_column].isna()]
        non_club_runners = data[data[club_column].isna()]

        if self.use_kentigern_style:
            with KentigernPlot(1, 2, figsize=figsize or (8, 2)) as fig:
                # KDE plot
                ax = fig.axes[0]
                kde_club = GaussianKDE(club_runners[time_column].dropna())
                kde_non_club = GaussianKDE(non_club_runners[time_column].dropna())

                ax.fill_between(
                    bins, 100 * kde_club(bins), alpha=0.5, color="red", label="In club"
                )
                ax.fill_between(
                    bins,
                    100 * kde_non_club(bins),
                    alpha=0.5,
                    color="blue",
                    label="No club",
                )
                ax.plot(
                    bins,
                    100 * kde_club(bins),
                    alpha=0.5,
                    color="black",
                    linewidth=1,
                    path_effects=[
                        pe.Stroke(linewidth=1.5, foreground="w"),
                        pe.Normal(),
                    ],
                )
                ax.plot(
                    bins,
                    100 * kde_non_club(bins),
                    alpha=0.5,
                    color="black",
                    linewidth=1,
                    path_effects=[
                        pe.Stroke(linewidth=1.5, foreground="w"),
                        pe.Normal(),
                    ],
                )

                ax.set(yticklabels=[])
                ax.tick_params(left=False)
                ax.set_xlabel("Finish Time (minutes)")

                # Cumulative plot
                ax = fig.axes[1]
                ax.hist(
                    club_runners[time_column].dropna(),
                    bins=bins,
                    cumulative=True,
                    density=True,
                    histtype="step",
                    color="red",
                    linewidth=1,
                    path_effects=[
                        pe.Stroke(linewidth=1.5, foreground="w"),
                        pe.Normal(),
                    ],
                )
                ax.hist(
                    non_club_runners[time_column].dropna(),
                    bins=bins,
                    cumulative=True,
                    density=True,
                    histtype="step",
                    color="blue",
                    linewidth=1,
                    path_effects=[
                        pe.Stroke(linewidth=1.5, foreground="w"),
                        pe.Normal(),
                    ],
                )

                ax.set_xlim(bins[0], bins[-1])
                ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
                ax.set_xlabel("Finish Time (minutes)")
                ax.set_ylabel("Percentage finished")

                fig.legend(loc="center right", prop={"size": 6, "family": "Consolas"})
                fig.tight_layout()

                if save_path:
                    fig.savefig(save_path)

                return fig
        else:
            fig, axes = plt.subplots(1, 2, figsize=figsize or (12, 4))

            # KDE plot
            ax = axes[0]
            kde_club = GaussianKDE(club_runners[time_column].dropna())
            kde_non_club = GaussianKDE(non_club_runners[time_column].dropna())
            ax.fill_between(bins, 100 * kde_club(bins), alpha=0.5, label="In club")
            ax.fill_between(bins, 100 * kde_non_club(bins), alpha=0.5, label="No club")
            ax.set_xlabel("Finish Time (minutes)")
            ax.legend()

            # Cumulative plot
            ax = axes[1]
            ax.hist(
                club_runners[time_column].dropna(),
                bins=bins,
                cumulative=True,
                density=True,
                histtype="step",
                label="In club",
            )
            ax.hist(
                non_club_runners[time_column].dropna(),
                bins=bins,
                cumulative=True,
                density=True,
                histtype="step",
                label="No club",
            )
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))
            ax.set_xlabel("Finish Time (minutes)")
            ax.set_ylabel("Percentage finished")
            ax.legend()

            fig.tight_layout()
            if save_path:
                fig.savefig(save_path)
            return fig
