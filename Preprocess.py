"""
Data Preprocessing Script

Loads the SVAMP math word problem dataset from HuggingFace and prepares it
for our calculator benchmark. Main thing we do here is calculate a complexity
score for each equation so we can analyze how performance varies with complexity.
"""

from datasets import load_dataset
import os
import re
import pandas as pd

# Where to save the processed data
output_dir = r"c:\Users\sambit\Desktop\Agentic Calculator\Results"
output_file = os.path.join(output_dir, "SVAMP_processed.csv")


def calculate_raw_complexity(equation):
    """
    Figures out how "complex" an equation is. We look at several factors:
    
    - How many operators (+, -, *, /)
    - How deeply nested the parentheses are
    - How many numbers are involved
    - How big the numbers are (more digits = harder)
    - Overall length of the equation
    
    The weights are somewhat arbitrary but seem to work well in practice.
    Returns a raw score that we'll normalize to 0-1 later.
    """
    if not equation or not isinstance(equation, str):
        return 0
    
    # Count the operators
    operators = len(re.findall(r'[\+\-\*/]', equation))
    
    # Find all the numbers (handles decimals too)
    operand_matches = re.findall(r'\d+\.?\d*', equation)
    operands = len(operand_matches)
    
    # Bigger numbers are arguably harder, so we look at digit count
    avg_magnitude = 0
    if operand_matches:
        magnitudes = [len(n.replace('.', '')) for n in operand_matches]
        avg_magnitude = sum(magnitudes) / len(magnitudes)
    
    # Track how deep the parentheses go
    max_depth = 0
    current_depth = 0
    for char in equation:
        if char == '(':
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif char == ')':
            current_depth -= 1
    
    # Longer equations are generally more complex
    length_factor = len(equation) / 100.0
    
    # Combine everything with some weights
    # These were tuned to give a reasonable spread of values
    raw_score = (operators * 1.5) + (max_depth * 2.5) + (operands * 0.75) + (avg_magnitude * 0.3) + length_factor
    return raw_score


def normalize_complexity(df):
    """
    Takes the raw complexity scores and normalizes them to 0-1 range.
    Uses simple min-max normalization.
    """
    raw_scores = df['Equation'].apply(calculate_raw_complexity)
    min_val = raw_scores.min()
    max_val = raw_scores.max()
    
    # Edge case: if all equations have the same complexity
    if max_val == min_val:
        return [0.5] * len(raw_scores)
    
    normalized = (raw_scores - min_val) / (max_val - min_val)
    return normalized.round(4)


# ============================================================================
# Main execution
# ============================================================================

print("Loading SVAMP dataset from HuggingFace...")
ds = load_dataset("ChilleD/SVAMP")

# We only need the training split
df = ds["train"].to_pandas()
print(f"Loaded {len(df)} rows")

# Keep just the columns we need
columns_to_keep = ['ID', 'Equation', 'Answer', 'Type']
df = df[columns_to_keep]

# Calculate complexity for each equation
print("Calculating complexity scores...")
df['Complexity'] = normalize_complexity(df)

# Nice ordering
df = df[['ID', 'Equation', 'Answer', 'Type', 'Complexity']]

# Save it
df.to_csv(output_file, index=False)

# Print some stats so we know it worked
print(f"Dataset saved to: {output_file}")
print(f"Total rows: {len(df)}")
print(f"Columns: {list(df.columns)}")
print(f"\nComplexity stats:")
print(f"  Min: {df['Complexity'].min()}")
print(f"  Max: {df['Complexity'].max()}")
print(f"  Mean: {df['Complexity'].mean():.4f}")