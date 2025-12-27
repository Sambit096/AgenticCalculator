import math

# Dictionary to make sure Python’s trig functions understand degrees
ALLOWED_NAMES = {
    # constants
    "pi": math.pi,
    "e": math.e,
    
    # trig in DEGREES
    "sin": lambda x: math.sin(math.radians(x)),
    "cos": lambda x: math.cos(math.radians(x)),
    "tan": lambda x: math.tan(math.radians(x)),
    
    # inverse trig 
    "asin": lambda x: math.degrees(math.asin(x)),
    "acos": lambda x: math.degrees(math.acos(x)),
    "atan": lambda x: math.degrees(math.atan(x)),
    
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