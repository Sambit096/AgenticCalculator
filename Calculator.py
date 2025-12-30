import math

# Dictionary of allowed names for safe evaluation - all trig functions use RADIANS
ALLOWED_NAMES = {
    # constants
    "pi": math.pi,
    "e": math.e,
    
    # trig functions (input in RADIANS)
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    
    # inverse trig functions (output in RADIANS)
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    
    # other functions that we may require
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