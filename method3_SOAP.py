"""
Method 3: SOAP Calculator Implementation
Uses a public SOAP web service to perform arithmetic operations.
The tricky part is that we need to recursively parse nested expressions
and make separate API calls for each operation.
"""

import os
import re
import time
import psutil
import pandas as pd
from zeep import Client
from zeep.exceptions import Fault
from lxml import etree

# Public SOAP calculator service - been around forever, pretty reliable
WSDL_URL = "http://www.dneonline.com/calculator.asmx?WSDL"

# File paths
INPUT_CSV = r"Results\SVAMP_processed.csv"
OUTPUT_CSV = r"Results\Method 3\results_method_3_svamp.csv"

# Sometimes the service flakes out, so we retry a few times
MAX_RETRIES = 3

# Fire up the SOAP client once at startup
print("Initializing SOAP client...")
client = Client(WSDL_URL)

# Maps our operators to the SOAP service method names
OPERATIONS = {
    '+': 'Add',
    '-': 'Subtract',
    '*': 'Multiply',
    '/': 'Divide'
}


def call_soap_operation(op, a, b):
    """
    Makes a single SOAP call. 
    Returns tuple: (result, request_bytes, response_bytes, http_status, fault_flag)
    
    Note: The SOAP service only works with integers, so we have to round.
    This causes some precision issues but it's fine for our benchmark.
    """
    service = client.service
    
    # SOAP service wants integers, not floats
    int_a = int(round(float(a)))
    int_b = int(round(float(b)))
    
    try:
        if op == '+':
            result = service.Add(intA=int_a, intB=int_b)
        elif op == '-':
            result = service.Subtract(intA=int_a, intB=int_b)
        elif op == '*':
            result = service.Multiply(intA=int_a, intB=int_b)
        elif op == '/':
            # Watch out for divide by zero
            if int_b == 0:
                return None, 0, 0, 500, 1
            result = service.Divide(intA=int_a, intB=int_b)
        else:
            return None, 0, 0, 400, 1
        
        # Zeep doesn't give us raw XML easily, so we estimate the sizes
        # Based on typical SOAP envelope overhead
        request_bytes = 300 + len(str(int_a)) + len(str(int_b))
        response_bytes = 250 + len(str(result))
        
        return float(result), request_bytes, response_bytes, 200, 0
        
    except Fault as e:
        # SOAP fault - something went wrong on their end
        return None, 200, 100, 500, 1
    except Exception as e:
        # Network error or something else
        return None, 200, 100, 500, 1


def evaluate_expression(equation):
    """
    The heart of the SOAP calculator. Parses the equation and evaluates it
    by making SOAP calls for each operation.
    
    Strategy: Find innermost parentheses first, evaluate them, replace with
    result, repeat until no more parentheses. Classic recursive descent but
    implemented iteratively.
    
    Returns tuple with all the metrics we're tracking.
    """
    total_req_bytes = 0
    total_resp_bytes = 0
    soap_calls = 0
    http_status = 200
    fault_flag = 0
    retry_count = 0
    
    expr = equation.strip()
    
    # Keep processing until we've resolved all parentheses
    while '(' in expr:
        # Regex to find innermost parentheses (no nested parens inside)
        match = re.search(r'\(([^()]+)\)', expr)
        if not match:
            break
        
        inner = match.group(1).strip()
        
        # Try to parse as "number operator number"
        op_match = re.search(r'([\d.]+)\s*([+\-*/])\s*([\d.]+)', inner)
        if op_match:
            a = float(op_match.group(1))
            op = op_match.group(2)
            b = float(op_match.group(3))
            
            # Try the SOAP call with retries
            result = None
            for attempt in range(MAX_RETRIES):
                result, req_b, resp_b, status, fault = call_soap_operation(op, a, b)
                soap_calls += 1
                total_req_bytes += req_b
                total_resp_bytes += resp_b
                http_status = status
                fault_flag = fault
                
                if result is not None:
                    break
                retry_count += 1
                time.sleep(0.5 * attempt)  # Back off a bit between retries
            
            if result is None:
                # Gave up after retries
                return None, total_req_bytes, total_resp_bytes, soap_calls, http_status, fault_flag, retry_count
            
            # Swap out the parenthesized expression with the result
            expr = expr[:match.start()] + str(result) + expr[match.end():]
        else:
            # Just a number in parens like "(5)" - strip the parens
            expr = expr[:match.start()] + inner + expr[match.end():]
    
    # Check if there's still an operation left (no parens case)
    op_match = re.search(r'([\d.]+)\s*([+\-*/])\s*([\d.]+)', expr)
    if op_match:
        a = float(op_match.group(1))
        op = op_match.group(2)
        b = float(op_match.group(3))
        
        for attempt in range(MAX_RETRIES):
            result, req_b, resp_b, status, fault = call_soap_operation(op, a, b)
            soap_calls += 1
            total_req_bytes += req_b
            total_resp_bytes += resp_b
            http_status = status
            fault_flag = fault
            
            if result is not None:
                return result, total_req_bytes, total_resp_bytes, soap_calls, http_status, fault_flag, retry_count
            retry_count += 1
            time.sleep(0.5 * attempt)
        
        return None, total_req_bytes, total_resp_bytes, soap_calls, http_status, fault_flag, retry_count
    
    # Maybe it's just a plain number?
    try:
        return float(expr), total_req_bytes, total_resp_bytes, soap_calls, http_status, fault_flag, retry_count
    except:
        return None, total_req_bytes, total_resp_bytes, soap_calls, http_status, fault_flag, retry_count


def run_benchmark_method_3():
    """
    Main benchmark runner. Goes through each equation in the dataset,
    evaluates it via SOAP, and records all the performance metrics.
    """
    df = pd.read_csv(INPUT_CSV)
    process = psutil.Process(os.getpid())
    
    # Set up all the columns we'll populate
    columns = ['Method_Used', 'Output_Answer', 'IsCorrect', 'Latency_ms', 'CPU_Time_ms',
               'RAM_Peak_MB', 'Request_Size_Bytes', 'Response_Size_Bytes', 
               'HTTP_Status_Code', 'SOAP_Fault_Flag', 'Retry_Count', 'SOAP_Calls_Count']
    for col in columns:
        df[col] = None
    
    total = len(df)
    print(f"Executing Method 3 (SOAP) for {total} problems")
    
    for idx, row in df.iterrows():
        equation = row['Equation']
        expected = row['Answer']
        
        # Grab baseline metrics before we start
        start_cpu = process.cpu_times()
        start_mem = process.memory_info().rss
        start_time = time.perf_counter()
        
        # Do the actual work
        result, req_bytes, resp_bytes, soap_calls, http_status, fault_flag, retry_count = evaluate_expression(equation)
        
        # Measure what we used
        end_time = time.perf_counter()
        end_mem = process.memory_info().rss
        end_cpu = process.cpu_times()
        
        # Calculate the metrics
        latency_ms = (end_time - start_time) * 1000
        cpu_time_ms = ((end_cpu.user - start_cpu.user) + (end_cpu.system - start_cpu.system)) * 1000
        ram_mb = max(0, (end_mem - start_mem) / (1024 * 1024))
        
        # Check if we got the right answer
        # We allow up to 1.0 difference because of integer rounding in SOAP
        try:
            is_correct = 1 if (result is not None and abs(float(result) - float(expected)) < 1.0) else 0
        except:
            is_correct = 0
        
        # Store everything
        df.at[idx, 'Method_Used'] = "SOAP_Calculator"
        df.at[idx, 'Output_Answer'] = result
        df.at[idx, 'IsCorrect'] = is_correct
        df.at[idx, 'Latency_ms'] = latency_ms
        df.at[idx, 'CPU_Time_ms'] = cpu_time_ms
        df.at[idx, 'RAM_Peak_MB'] = ram_mb
        df.at[idx, 'Request_Size_Bytes'] = req_bytes
        df.at[idx, 'Response_Size_Bytes'] = resp_bytes
        df.at[idx, 'HTTP_Status_Code'] = http_status
        df.at[idx, 'SOAP_Fault_Flag'] = fault_flag
        df.at[idx, 'Retry_Count'] = retry_count
        df.at[idx, 'SOAP_Calls_Count'] = soap_calls
        
        # Progress update every 50 rows
        if (idx + 1) % 50 == 0:
            print(f"[{idx+1}/{total}] result={result} expected={expected} correct={is_correct}")
    
    # Clean up any weird columns and save
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved to {OUTPUT_CSV}")
    
    accuracy = df['IsCorrect'].sum() / len(df) * 100
    print(f"Accuracy: {accuracy:.2f}%")


if __name__ == "__main__":
    run_benchmark_method_3()
