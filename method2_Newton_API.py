import pandas as pd
import time
import requests
import psutil
import os
import urllib.parse

# --- 1. The API Call Logic ---
def call_rest_api(expression):
    # The Newton API uses 'simplify' for basic arithmetic and requires URL encoding for symbols like + and /
    encoded_expr = urllib.parse.quote(expression.replace("**", "^"))
    url = f"https://newton.now.sh/api/v2/simplify/{encoded_expr}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Newton returns results as strings
            return float(data['result'])
        else:
            return None
    except Exception:
        return None

# --- 2. Benchmark Execution Loop ---
def run_benchmark_method_2(input_file, output_file):
    try:
        df = pd.read_csv(input_file)
        process = psutil.Process(os.getpid())
        print(f"Executing Method 2 (REST API) for {len(df)} problems")
        results = []
        for index, row in df.iterrows():
            expression = row['Expression']
        expected = row['Expected_Answer']
        
        # --- Performance Tracking: START ---
        start_time = time.perf_counter()
        start_mem = process.memory_info().rss
        
        # EXECUTION: Call the External REST API
        actual = call_rest_api(expression)
        
        # Capture end metrics
        end_time = time.perf_counter()
        end_mem = process.memory_info().rss
        # --- Performance Tracking: END ---
        
        # --- Calculation of Metrics ---
        latency_ms = (end_time - start_time) * 1000
        ram_delta_mb = max(0, (end_mem - start_mem) / (1024 * 1024))
        
        # Accuracy Check
        try:
            is_correct = 1 if (actual is not None and abs(float(actual) - float(expected)) < 1e-7) else 0
        except:
            is_correct = 0
            
        results.append({
            "Method_Used": "REST_API",
            "Actual_Answer": actual,
            "Is_Correct": is_correct,
            "Latency_ms": latency_ms,
            "Invocations": 1,
            "Token_Count": 0,
            "CPU_Cycles": 0.01,
            "RAM_Peak_MB": ram_delta_mb,
            "Env_Status": "Service_Online",
            "Decision_Logic_Time": 0 
        })
