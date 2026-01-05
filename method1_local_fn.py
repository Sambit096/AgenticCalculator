from Calculator import Calculator
import pandas as pd
import time
import psutil
import os

#--- Method 1: Local Function Calculator ---

def run_benchmark_method_1(input_file, output_file):
    try:
        df = pd.read_csv(input_file)
        process = psutil.Process(os.getpid())

        print(f"Executing Method 1 (Local Fn) for {len(df)} problems")
        
        # Initialize output columns
        df['Method_Used'] = None
        df['Output_Answer'] = None
        df['IsCorrect'] = None
        df['Latency_ms'] = None
        df['CPU_Cycles'] = None
        df['RAM_Peak_MB'] = None
        
        for index, row in df.iterrows():
            equation = row['Equation']
            expected = row['Answer']
            
            # --- Performance Tracking: START ---
            start_cpu_times = process.cpu_times()
            start_mem = process.memory_info().rss
            start_time = time.perf_counter()

            # Call the local Calculator function
            actual = Calculator(equation)

            # Capture end metrics
            end_time = time.perf_counter()
            end_mem = process.memory_info().rss
            end_cpu_times = process.cpu_times()
            # --- Performance Tracking: END ---

            # --- Calculation of Metrics ---
            latency_ms = (end_time - start_time) * 1000
            cpu_delta = (end_cpu_times.user - start_cpu_times.user) + (end_cpu_times.system - start_cpu_times.system)
            ram_delta_mb = max(0, (end_mem - start_mem) / (1024 * 1024))

            # Accuracy Check
            try:
                is_correct = 1 if (actual is not None and abs(float(actual) - float(expected)) < 1e-7) else 0
            except:
                is_correct = 0

            # Update columns
            df.at[index, 'Method_Used'] = "Local_Fn"
            df.at[index, 'Output_Answer'] = actual
            df.at[index, 'IsCorrect'] = is_correct
            df.at[index, 'Latency_ms'] = latency_ms
            df.at[index, 'CPU_Cycles'] = cpu_delta
            df.at[index, 'RAM_Peak_MB'] = ram_delta_mb

        # Remove any unnamed columns
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Save results
        df.to_csv(output_file, index=False)
        print(f"Finished! Results saved to {output_file}")
        
        # Print summary
        accuracy = df['IsCorrect'].sum() / len(df) * 100
        print(f"Accuracy: {accuracy:.2f}%")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    input_csv = r"Results\SVAMP_processed.csv" 
    output_csv = r"Results\Method 1\results_method_1_svamp.csv"
    run_benchmark_method_1(input_csv, output_csv)