from Calculator import Calculator
import pandas as pd
import time
import psutil
import os
import math

#--- 1. Benchmark Execution Loop ---

def run_benchmark_method_1(input_file, output_file):
    try:
        df = pd.read_csv(input_file)
        # Access the current process for resource tracking
        process = psutil.Process(os.getpid())

        print(f"Executing Method 1 (Local Fn) for {len(df)} problems")
        for index, row in df.iterrows():
            expression = row['Expression']
            expected = row['Expected_Answer']
            # --- Performance Tracking: START ---
            # Capture baseline CPU and Memory
            start_cpu_times = process.cpu_times()
            start_mem = process.memory_info().rss
            start_time = time.perf_counter()

            #Call the local Calculator function
            actual = Calculator(expression)

            # Capture end metrics
            end_time = time.perf_counter()
            end_mem = process.memory_info().rss
            end_cpu_times = process.cpu_times()

            # --- Performance Tracking: END ---
            # --- Calculation of Metrics: START ---
            latency_ms = (end_time - start_time) * 1000
            # CPU Cycles: User + System time delta (in seconds)
            cpu_delta = (end_cpu_times.user - start_cpu_times.user) + (end_cpu_times.system - start_cpu_times.system)
            # RAM Usage: Peak change in MB (max 0 to handle Garbage Collection drops)
            ram_delta_mb = max(0, (end_mem - start_mem) / (1024 * 1024))

            # Accuracy Check (Float comparison)
            try:
                is_correct = 1 if (actual is not None and abs(float(actual) - float(expected)) < 1e-7) else 0
                
            except:
                is_correct = 0

            # --- Calculation of Metrics: END ---
            # Update existing columns in the dataframe directly
            df.at[index, 'Method_Used'] = "Local_Fn"
            df.at[index, 'Actual_Answer'] = actual
            df.at[index, 'Is_Correct'] = is_correct
            df.at[index, 'Latency_ms'] = latency_ms
            df.at[index, 'Invocations'] = 1
            df.at[index, 'Token_Count'] = 0
            df.at[index, 'CPU_Cycles'] = cpu_delta
            df.at[index, 'RAM_Peak_MB'] = ram_delta_mb
            df.at[index, 'Env_Status'] = "Library_Available"
            df.at[index, 'Decision_Logic_Time'] = 0  # Baseline: Direct execution
            
            # Update Network_Bytes_Sent/Received column if it exists
            if 'Network_Bytes_Sent/Received' in df.columns:
                df.at[index, 'Network_Bytes_Sent/Received'] = 0

        # Remove any unnamed columns that may exist
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        # Save the Method 1 Dataset
        df.to_csv(output_file, index=False)
        print(f"Finished! Results saved to {output_file}")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    input_csv = "Mathematical_Expressions.csv" 
    output_csv = "results_method_1_local_fn.csv"
    run_benchmark_method_1(input_csv, output_csv)