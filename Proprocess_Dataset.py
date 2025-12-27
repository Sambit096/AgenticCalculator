import re
import pandas as pd
from Calculator import Calculator

def calculate_complexity_score(expression: str) -> float:
    if not isinstance(expression, str):
        expression = str(expression)

    expr = expression.replace(" ", "")

    # 1. Basic operators
    expr_for_ops = re.sub(r'\*\*', '', expr)
    num_operators = len(re.findall(r'[+\-*/]', expr_for_ops))

    # 2. Max parentheses depth
    max_depth = 0
    current_depth = 0
    for ch in expr:
        if ch == '(':
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif ch == ')':
            current_depth = max(0, current_depth - 1)

    # 3. Exponents
    num_exponents = len(re.findall(r'\^|\*\*', expr))

    # 4. Functions
    functions = re.findall(r'\b(sin|cos|tan|csc|sec|cot|log|ln|sqrt)\b', expr)
    num_functions = len(functions)

    # 5. Weighted sum
    score = (
        num_operators +
        max_depth +
        2 * num_exponents +
        2 * num_functions
    )

    return float(score)

def min_max_normalize(raw_values: pd.Series) -> pd.Series:
    min_val = raw_values.min()
    max_val = raw_values.max()

    if max_val == min_val:
        return pd.Series([1.0] * len(raw_values), index=raw_values.index)

    return 1 + 9 * (raw_values - min_val) / (max_val - min_val)



input_file = "Mathematical_Expressions.csv"
try:
    df = pd.read_csv(input_file)
    
    # Calculate raw complexity scores first
    raw_complexity = df['Expression'].apply(calculate_complexity_score)
    
    # Apply min-max normalization and replace Complexity_Score with normalized values
    df['Complexity_Score'] = min_max_normalize(raw_complexity)
    df['Expected_Answer'] = df['Expression'].apply(Calculator)

    # Save as a new file to preserve your original data
    output_file = input_file
    df.to_csv(output_file, index=False)

except FileNotFoundError:
    print(f"Error: {input_file} not found. Please check the file name.")
    
