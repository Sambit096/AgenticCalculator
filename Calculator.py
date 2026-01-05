import math

# Dictionary of allowed names for safe evaluation
ALLOWED_NAMES = {
    # constants
    "pi": math.pi,
    "e": math.e,
    
    # math functions
    "sqrt": math.sqrt,
    "log": math.log10,  # log base 10
    "ln": math.log,     # natural log
}
def Calculator(expression):
    try:
        # Your ^ to ** conversion so python calculator understands it
        safe_expr = expression.replace('^', '**')
        
        # Evaluate with ALLOWED_NAMES
        return eval(safe_expr, {"__builtins__": None}, ALLOWED_NAMES)
    except Exception:
        return None