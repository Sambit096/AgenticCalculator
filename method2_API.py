import os
import time
import re
import requests
import pandas as pd
import psutil

WOLFRAM_APPID = os.getenv("WOLFRAM_APPID")

def parse_wolfram_result_json(j):
    """Extract numeric result from Wolfram JSON response"""
    try:
        pods = j.get("queryresult", {}).get("pods", [])
        primary_pods = [p for p in pods if p.get("primary")]
        candidate_pods = primary_pods or pods
        for p in candidate_pods:
            for sp in p.get("subpods", []):
                txt = sp.get("plaintext", "")
                if not txt:
                    continue
                txt_clean = txt.split('=')[-1].split('≈')[-1].strip()
                txt_clean = txt_clean.replace(',', '')
                try:
                    val = float(txt_clean.strip().split()[0])
                    return val
                except:
                    m = re.search(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', txt_clean)
                    if m:
                        try:
                            return float(m.group(0))
                        except:
                            pass
        return None
    except Exception:
        return None


def run_benchmark_method_2(input_file, output_file, appid=WOLFRAM_APPID):
    if not appid:
        raise ValueError("WOLFRAM_APPID environment variable not set.")
    
    df = pd.read_csv(input_file)
    process = psutil.Process(os.getpid())
    session = requests.Session()
    base_url = "https://api.wolframalpha.com/v2/query"
    
    print(f"Executing Method 2 (Wolfram REST) for {len(df)} problems")
    
    # Initialize output columns
    df['Method_Used'] = None
    df['Output_Answer'] = None
    df['IsCorrect'] = None
    df['Latency_ms'] = None
    df['Invocations'] = None
    df['CPU_Cycles'] = None
    df['RAM_Peak_MB'] = None
    df['Env_Status'] = None
    df['Network_Bytes_Sent/Received'] = None
    
    for idx, row in df.iterrows():
        equation = row['Equation']
        expected = row['Answer']
        
        params = {
            "appid": appid,
            "input": equation,
            "output": "json"
        }
        
        # --- Performance Tracking: START ---
        start_cpu = process.cpu_times()
        start_mem = process.memory_info().rss
        start_time = time.perf_counter()
        bytes_sent = 0
        bytes_received = 0
        http_status = None
        actual = None
        num_attempts = 0
        max_retries = 3

        for attempt in range(1, max_retries + 1):
            num_attempts += 1
            try:
                req_url = base_url + "?" + "&".join([f"{k}={requests.utils.requote_uri(str(v))}" for k, v in params.items()])
                bytes_sent += len(req_url.encode('utf-8'))
                r = session.get(base_url, params=params, timeout=10)
                http_status = r.status_code
                bytes_received += len(r.content)
                if r.status_code == 200:
                    try:
                        j = r.json()
                        actual = parse_wolfram_result_json(j)
                    except Exception:
                        actual = None
                    break
                else:
                    if r.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                        time.sleep(1.0 * attempt)
                        continue
                    else:
                        break
            except requests.RequestException as e:
                if attempt < max_retries:
                    time.sleep(1.0 * attempt)
                    continue
                else:
                    break
        
        end_time = time.perf_counter()
        end_mem = process.memory_info().rss
        end_cpu = process.cpu_times()
        # --- Performance Tracking: END ---
        
        latency_ms = (end_time - start_time) * 1000.0
        cpu_delta = (end_cpu.user - start_cpu.user) + (end_cpu.system - start_cpu.system)
        ram_delta_mb = max(0, (end_mem - start_mem) / (1024 * 1024.0))
        
        # Accuracy check
        try:
            is_correct = 1 if (actual is not None and abs(float(actual) - float(expected)) < 1e-7) else 0
        except:
            is_correct = 0
        
        # Update columns
        df.at[idx, 'Method_Used'] = "API_REST_Wolfram"
        df.at[idx, 'Output_Answer'] = actual
        df.at[idx, 'IsCorrect'] = is_correct
        df.at[idx, 'Latency_ms'] = latency_ms
        df.at[idx, 'Invocations'] = num_attempts
        df.at[idx, 'CPU_Cycles'] = cpu_delta
        df.at[idx, 'RAM_Peak_MB'] = ram_delta_mb
        df.at[idx, 'Env_Status'] = "API_OK" if http_status == 200 else f"API_Error_{http_status}"
        df.at[idx, 'Network_Bytes_Sent/Received'] = f"{bytes_sent}/{bytes_received}"

    # Remove unnamed columns and save
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.to_csv(output_file, index=False)
    print(f"Method 2 results written to {output_file}")
    
    # Print summary
    accuracy = df['IsCorrect'].sum() / len(df) * 100
    print(f"Accuracy: {accuracy:.2f}%")


if __name__ == "__main__":
    input_csv = r"Results\SVAMP_processed.csv"
    output_csv = r"Results\Method 2\results_method_2_svamp.csv"
    run_benchmark_method_2(input_csv, output_csv)
