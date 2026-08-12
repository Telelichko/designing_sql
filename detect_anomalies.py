import pandas as pd

def detect_anomalies(df: pd.DataFrame, source_path: str = None) -> str:
    """Generate a Markdown report of data anomalies.
    
    Args:
        df: DataFrame to analyze.
        source_path: Optional path or URL of the source data (included in report).
    """
    lines = []
    lines.append("# Data Anomalies Report")
    if source_path:
        lines.append(f"**Source:** `{source_path}`")
    lines.append(f"**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Total rows:** {len(df)}")
    lines.append("")

    # Missing values
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        lines.append("## Missing Values")
        for col, count in missing.items():
            pct = count / len(df) * 100
            lines.append(f"- **{col}**: {count} missing ({pct:.1f}%)")
    else:
        lines.append("## Missing Values")
        lines.append("No missing values found.")
    lines.append("")

    # Rating out of 0-5
    if 'rating' in df.columns:
        rating = pd.to_numeric(df['rating'], errors='coerce')
        invalid = rating[(rating < 0) | (rating > 5)].dropna()
        if len(invalid) > 0:
            lines.append("## Rating Out of Range (0–5)")
            lines.append(f"Found {len(invalid)} rows with rating outside 0–5.")
            sample = df.loc[invalid.index, ['id', 'name', 'rating']].head(5)
            for _, row in sample.iterrows():
                lines.append(f"- id: {row['id']}, name: {row['name']}, rating: {row['rating']}")
        else:
            lines.append("## Rating Out of Range")
            lines.append("All ratings are within 0–5.")
        lines.append("")

    # Negative reviews_count
    if 'reviews_count' in df.columns:
        neg = df[df['reviews_count'] < 0]
        if len(neg) > 0:
            lines.append("## Negative Reviews Count")
            lines.append(f"Found {len(neg)} rows with negative reviews_count.")
            sample = neg[['id', 'name', 'reviews_count']].head(5)
            for _, row in sample.iterrows():
                lines.append(f"- id: {row['id']}, name: {row['name']}, reviews_count: {row['reviews_count']}")
        else:
            lines.append("## Negative Reviews Count")
            lines.append("No negative reviews counts.")
        lines.append("")

    # Duplicate IDs (before dedup)
    if 'id' in df.columns:
        dup_mask = df['id'].duplicated()
        if dup_mask.any():
            lines.append("## Duplicate IDs")
            lines.append(f"Found {dup_mask.sum()} duplicate ID entries.")
            dup_examples = df[df['id'].duplicated(keep=False)].sort_values('id')[['id', 'name']].head(10)
            for _, row in dup_examples.iterrows():
                lines.append(f"- id: {row['id']}, name: {row['name']}")
        else:
            lines.append("## Duplicate IDs")
            lines.append("No duplicate IDs found.")
        lines.append("")

    # Missing critical fields (id or name)
    critical = ['id', 'name']
    missing_crit = df[critical].isnull().any(axis=1).sum()
    if missing_crit > 0:
        lines.append("## Missing Critical Fields (id or name)")
        lines.append(f"Found {missing_crit} rows missing either 'id' or 'name'.")
        sample = df[df[critical].isnull().any(axis=1)][['id', 'name']].head(5)
        for _, row in sample.iterrows():
            lines.append(f"- id: {row['id']}, name: {row['name']}")
    else:
        lines.append("## Missing Critical Fields")
        lines.append("All rows have both 'id' and 'name'.")
    lines.append("")

    return "\n".join(lines)