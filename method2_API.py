import os
import time
import math
import json
import requests
import pandas as pd
import psutil
from xml.etree import ElementTree as ET

WOLFRAM_APPID = os.getenv("WOLFRAM_APPID")

def parse_wolfram_result_json(j):
    #Attempt to extract the result from the JSON response
    try:
        # Many Wolfram responses have 'pods' list with 'subpods' and plaintext
        pods = j.get("queryresult", {}).get("pods", [])
        # Prioritize pods with primary='true' or title 'Result' / 'Decimal approximation' etc.
        primary_pods = [p for p in pods if p.get("primary")]
        candidate_pods = primary_pods or pods
        for p in candidate_pods:
            # Each pod may have 'subpods' with plaintext
            for sp in p.get("subpods", []):
                txt = sp.get("plaintext", "")
                if not txt:
                    continue
                # Try to sanitize and parse the first numeric token
                # Remove commas, parentheses and explanatory text after '=' or '≈'
                txt_clean = txt.split('=')[-1].split('≈')[-1].strip()
                # Replace common unicode characters
                txt_clean = txt_clean.replace(',', '')
                # try to parse as float
                try:
                    val = float(txt_clean.strip().split()[0])
                    return val
                except:
                    # attempt to find first numeric substring
                    import re
                    m = re.search(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', txt_clean)
                    if m:
                        try:
                            return float(m.group(0))
                        except:
                            pass
        return None
    except Exception:
        return None

def parse_wolfram_result_xml(xml_text):
    
    #Fallback parser for XML formatted Full Results API.
    
    try:
        root = ET.fromstring(xml_text)
        # Look for pod elements with primary="true" or title == "Result"
        for pod in root.findall(".//pod"):
            if pod.attrib.get("primary") == "true" or pod.attrib.get("title","").lower().startswith("result"):
                sub = pod.find(".//subpod/plaintext")
                if sub is not None and sub.text:
                    txt = sub.text.strip().replace(',', '')
                    import re
                    m = re.search(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', txt)
                    if m:
                        return float(m.group(0))
        # Otherwise try any plaintext in a subpod
        for sub in root.findall(".//subpod/plaintext"):
            if sub is not None and sub.text:
                txt = sub.text.strip().replace(',', '')
                import re
                m = re.search(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', txt)
                if m:
                    return float(m.group(0))
        return None
    except Exception:
        return None

# Energy heuristic — tunable constants
# These are heuristic coefficients for a coarse energy proxy (joules).
CPU_JOULES_PER_SEC = 10.0 #per process estimate
NETWORK_JOULES_PER_BYTE = 1e-7 # rough energy cost per byte transferred on network (joules/byte)
def estimate_energy_joules(latency_seconds, cpu_seconds, bytes_sent, bytes_received):
    cpu_energy = cpu_seconds * CPU_JOULES_PER_SEC
    net_energy = (bytes_sent + bytes_received) * NETWORK_JOULES_PER_BYTE
    # Combine with weighting on latency as proxy for idle network power usage
    latency_energy = latency_seconds * 1.0  # 1 watt baseline * seconds => joules (tunable)
    return cpu_energy + net_energy + latency_energy


def run_benchmark_method_2(input_file, output_file, appid=WOLFRAM_APPID, use_json=True):
    if not appid:
        raise ValueError("WOLFRAM_APPID environment variable not set. Obtain AppID from developer.wolframalpha.com and set it.")
    df = pd.read_csv(input_file)
    process = psutil.Process(os.getpid())
    session = requests.Session()
    base_url = "https://api.wolframalpha.com/v2/query"
    print(f"Executing Method 2 (Wolfram REST) for {len(df)} problems")
    for idx, row in df.iterrows():
        expr = row['Expression']
        expected = row['Expected_Answer']
        params = {
            "appid": appid,
            "input": f"{expr} assuming radians",
            "output": "json" if use_json else "xml"
        }
        # --- Performance Tracking: START ---
        start_cpu = process.cpu_times()
        start_mem = process.memory_info().rss
        start_time = time.perf_counter()
        bytes_sent = 0
        bytes_received = 0
        http_status = None
        response_text = None
        actual = None
        num_attempts = 0
        error_msg = ""
        max_retries = 3

        # Perform request with simple retry/backoff for transient errors
        for attempt in range(1, max_retries + 1):
            num_attempts += 1
            try:
                req_url = base_url + "?" + "&".join([f"{k}={requests.utils.requote_uri(str(v))}" for k, v in params.items()])
                approximate_request_bytes = len(req_url.encode('utf-8'))
                bytes_sent += approximate_request_bytes
                r = session.get(base_url, params=params, timeout=10)
                http_status = r.status_code
                response_text = r.text
                bytes_received += len(r.content)
                if r.status_code == 200:
                    if use_json:
                        try:
                            j = r.json()
                            actual = parse_wolfram_result_json(j)
                        except Exception:
                            actual = parse_wolfram_result_xml(r.text)
                    else:
                        actual = parse_wolfram_result_xml(r.text)
                    break
                else:
                    error_msg = f"HTTP {r.status_code}"
                    # for rate limiting (429) or server errors, backoff and retry
                    if r.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                        time.sleep(1.0 * attempt)
                        continue
                    else:
                        break
            except requests.RequestException as e:
                error_msg = str(e)
                if attempt < max_retries:
                    time.sleep(1.0 * attempt)
                    continue
                else:
                    break
        
        end_time = time.perf_counter()
        end_mem = process.memory_info().rss
        end_cpu = process.cpu_times()
        latency_ms = (end_time - start_time) * 1000.0
        cpu_delta = (end_cpu.user - start_cpu.user) + (end_cpu.system - start_cpu.system)
        ram_delta_mb = max(0, (end_mem - start_mem) / (1024 * 1024.0))
        # --- Performance Tracking: END ---
        # --- Calculation of Metrics: START ---
        try:
            is_correct = 1 if (actual is not None and abs(float(actual) - float(expected)) < 1e-7) else 0
        except:
            is_correct = 0
        energy_j = estimate_energy_joules((end_time - start_time), cpu_delta, bytes_sent, bytes_received)
        
        # Update existing columns in the dataframe directly
        df.at[idx, 'Method_Used'] = "API_REST_Wolfram"
        df.at[idx, 'Actual_Answer'] = actual
        df.at[idx, 'Is_Correct'] = is_correct
        df.at[idx, 'Latency_ms'] = latency_ms
        df.at[idx, 'Invocations'] = num_attempts
        df.at[idx, 'Token_Count'] = 0
        df.at[idx, 'CPU_Cycles'] = cpu_delta
        df.at[idx, 'RAM_Peak_MB'] = ram_delta_mb
        df.at[idx, 'Env_Status'] = "API_OK" if http_status == 200 else f"API_Error_{http_status}"
        df.at[idx, 'Decision_Logic_Time'] = 0
        
        
        # Update Network_Bytes_Sent/Received column if it exists, otherwise use separate columns
        if 'Network_Bytes_Sent/Received' in df.columns:
            df.at[idx, 'Network_Bytes_Sent/Received'] = f"{bytes_sent}/{bytes_received}"
        
    # --- Calculation of Metrics: END ---
    # --- Save Results: START ---
    # Remove any unnamed columns that may exist
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.to_csv(output_file, index=False)
    print(f"Method 2 results written to {output_file}")

if __name__ == "__main__":
    input_csv = "Mathematical_Expressions.csv"
    output_csv = "results_method_2_wolfram_rest.csv"
    run_benchmark_method_2(input_csv, output_csv, use_json=True)


        

