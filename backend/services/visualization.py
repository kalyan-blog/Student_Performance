import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import base64
from io import BytesIO
import os


def set_style():
    plt.style.use("seaborn-v0_8-darkgrid")
    sns.set_palette("husl")


def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_str


def create_bar_chart(data, x_col, y_col, title="Bar Chart", xlabel=None, ylabel=None):
    set_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=data, x=x_col, y=y_col, ax=ax)
    ax.set_title(title, fontsize=16, pad=20)
    ax.set_xlabel(xlabel or x_col)
    ax.set_ylabel(ylabel or y_col)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig_to_base64(fig)


def create_line_chart(data, x_col, y_col, title="Line Chart"):
    set_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(data=data, x=x_col, y=y_col, marker="o", ax=ax)
    ax.set_title(title, fontsize=16, pad=20)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig_to_base64(fig)


def create_pie_chart(data, labels_col, values_col, title="Pie Chart"):
    set_style()
    fig, ax = plt.subplots(figsize=(8, 8))
    colors = sns.color_palette("husl", len(data))
    ax.pie(
        data[values_col], labels=data[labels_col], autopct="%1.1f%%",
        colors=colors, startangle=90
    )
    ax.set_title(title, fontsize=16, pad=20)
    plt.tight_layout()
    return fig_to_base64(fig)


def create_correlation_heatmap(df, title="Correlation Matrix"):
    set_style()
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return None
    fig, ax = plt.subplots(figsize=(12, 8))
    corr = numeric_df.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
        center=0, square=True, ax=ax, linewidths=0.5
    )
    ax.set_title(title, fontsize=16, pad=20)
    plt.tight_layout()
    return fig_to_base64(fig)


def create_scatter_plot(data, x_col, y_col, hue_col=None, title="Scatter Plot"):
    set_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=data, x=x_col, y=y_col, hue=hue_col, ax=ax, s=60)
    ax.set_title(title, fontsize=16, pad=20)
    plt.tight_layout()
    return fig_to_base64(fig)


def create_distribution_plot(data, col, title="Distribution Plot"):
    set_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(data=data, x=col, kde=True, ax=ax, bins=20)
    ax.set_title(title, fontsize=16, pad=20)
    plt.tight_layout()
    return fig_to_base64(fig)


def create_box_plot(data, x_col, y_col, title="Box Plot"):
    set_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=data, x=x_col, y=y_col, ax=ax)
    ax.set_title(title, fontsize=16, pad=20)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig_to_base64(fig)


def generate_all_visualizations(df):
    charts = {}
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()

    if len(numeric_cols) >= 2:
        charts["correlation"] = create_correlation_heatmap(df)

    if cat_cols and numeric_cols:
        for cat in cat_cols[:3]:
            for num in numeric_cols[:3]:
                try:
                    agg = df.groupby(cat)[num].mean().reset_index()
                    charts[f"bar_{cat}_{num}"] = create_bar_chart(
                        agg, cat, num, f"Average {num} by {cat}"
                    )
                except:
                    pass

    if len(numeric_cols) >= 1:
        for col in numeric_cols[:3]:
            charts[f"dist_{col}"] = create_distribution_plot(df, col)

    if len(numeric_cols) >= 2:
        charts["scatter"] = create_scatter_plot(
            df, numeric_cols[0], numeric_cols[1],
            title=f"{numeric_cols[0]} vs {numeric_cols[1]}"
        )

    if cat_cols and numeric_cols:
        charts["box"] = create_box_plot(
            df, cat_cols[0], numeric_cols[0],
            title=f"{numeric_cols[0]} by {cat_cols[0]}"
        )

    return charts


def create_bar_chart(data, x_col, y_col, title):
    return create_bar_chart(data, x_col, y_col, title)