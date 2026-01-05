"""
Benchmark Runner - Multi-Epoch Testing for Method 3

This script runs the SOAP calculator benchmark multiple times (epochs) to get
statistically meaningful metrics. Running once isn't enough because network
latency varies, so we do 15 runs and aggregate the results.

Outputs two files:
- Raw data: every single run for each equation
- Summary: aggregated stats (mean, std, percentiles) per equation
"""

from method3_SOAP import evaluate_expression, client
import pandas as pd
import numpy as np
import psutil
import time
import os

# How many times we run through the entire dataset
EPOCHS = 15

# File paths
INPUT_CSV = r"Results\SVAMP_processed.csv"
OUTPUT_RAW = r"Results\Method 3\benchmark_method_3_raw.csv"
OUTPUT_SUMMARY = r"Results\Method 3\benchmark_method_3_summary.csv"


def run_method3_epochs():
    """
    Main function that runs the benchmark.
    Goes through all equations 15 times, collecting metrics each run.
    Then aggregates everything into useful statistics.
    """
    df = pd.read_csv(INPUT_CSV)
    
    # Fix a typo in the dataset - some rows have "Common-Divison" instead of "Division"
    df['Type'] = df['Type'].replace({'Common-Divison': 'Division', 'Common-Division': 'Division'})
    
    process = psutil.Process(os.getpid())
    results = []
    total = len(df)
    
    print(f"Running Method 3: {EPOCHS} epochs × {total} equations = {EPOCHS * total} rows")
    
    # Run through each epoch
    for epoch in range(EPOCHS):
        print(f"\n--- Epoch {epoch + 1}/{EPOCHS} ---")
        
        for idx, row in df.iterrows():
            # Capture performance before
            start_cpu = process.cpu_times()
            start_mem = process.memory_info().rss
            start_time = time.perf_counter()
            
            # Run the SOAP evaluation
            result, req_bytes, resp_bytes, soap_calls, _, _, _ = evaluate_expression(row['Equation'])
            
            # Capture performance after
            end_time = time.perf_counter()
            end_mem = process.memory_info().rss
            end_cpu = process.cpu_times()
            
            # Calculate metrics
            latency_ms = (end_time - start_time) * 1000
            cpu_time_ms = ((end_cpu.user - start_cpu.user) + (end_cpu.system - start_cpu.system)) * 1000
            ram_mb = max(0, (end_mem - start_mem) / (1024 * 1024))
            
            # Check correctness - allow small difference due to rounding
            try:
                is_correct = 1 if (result is not None and abs(float(result) - float(row['Answer'])) < 1.0) else 0
            except:
                is_correct = 0
            
            # Store this run's data
            results.append({
                'ID': row['ID'],
                'Epoch': epoch + 1,
                'Equation': row['Equation'],
                'Answer': row['Answer'],
                'Type': row['Type'],
                'Complexity': row['Complexity'],
                'Method_Used': 'SOAP_Calculator',
                'Output_Answer': result,
                'IsCorrect': is_correct,
                'Latency_ms': latency_ms,
                'CPU_Time_ms': cpu_time_ms,
                'RAM_Peak_MB': ram_mb,
                'Request_Size_Bytes': req_bytes,
                'Response_Size_Bytes': resp_bytes,
                'SOAP_Calls_Count': soap_calls
            })
        
        print(f"Epoch {epoch + 1} complete")
    
    # Save the raw data (every single run)
    raw_df = pd.DataFrame(results).sort_values(['ID', 'Epoch'])
    raw_df.to_csv(OUTPUT_RAW, index=False)
    print(f"\nSaved raw: {OUTPUT_RAW} ({len(raw_df)} rows)")
    
    # Now aggregate the results by equation ID
    # This gives us mean, std, percentiles etc for each equation
    summary = raw_df.groupby('ID').agg(
        Equation=('Equation', 'first'),
        Answer=('Answer', 'first'),
        Type=('Type', 'first'),
        Complexity=('Complexity', 'first'),
        Method_Used=('Method_Used', 'first'),
        Output_Answer=('Output_Answer', 'first'),
        
        # IsCorrect as mean gives us the "success rate" across epochs
        IsCorrect=('IsCorrect', 'mean'),
        
        # Latency - multiple ways to look at it
        Latency_Mean_ms=('Latency_ms', 'mean'),
        Latency_Std_ms=('Latency_ms', 'std'),
        Latency_P95_ms=('Latency_ms', lambda x: np.percentile(x, 95)),
        Latency_P99_ms=('Latency_ms', lambda x: np.percentile(x, 99)),
        
        # CPU time stats
        CPU_Time_Mean_ms=('CPU_Time_ms', 'mean'),
        CPU_Time_Std_ms=('CPU_Time_ms', 'std'),
        CPU_Time_Peak_ms=('CPU_Time_ms', 'max'),
        
        # Memory - just care about the peak
        RAM_Peak_Max_MB=('RAM_Peak_MB', 'max'),
        
        # These don't change between runs, but include for completeness
        Request_Size_Bytes=('Request_Size_Bytes', 'first'),
        Response_Size_Bytes=('Response_Size_Bytes', 'first'),
        SOAP_Calls_Count=('SOAP_Calls_Count', 'first')
    ).reset_index()
    
    summary.to_csv(OUTPUT_SUMMARY, index=False)
    print(f"Saved summary: {OUTPUT_SUMMARY} ({len(summary)} rows)")
    
    # Quick stats
    print(f"\nAccuracy: {summary['IsCorrect'].mean() * 100:.2f}%")
    print(f"Mean Latency: {summary['Latency_Mean_ms'].mean():.2f}ms")


if __name__ == "__main__":
    run_method3_epochs()
