import os
import time
import re
import math
import json
import psutil
import pandas as pd
from groq import Groq
from requests import RequestException

MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
API_KEY = os.getenv("GROQ_API_KEY")

INPUT_CSV = r"Results\SVAMP_processed.csv"
OUTPUT_CSV = r"Results\Method 4\results_method_4_svamp.csv"

MAX_RETRIES = 2
RETRY_BACKOFF_BASE = 0.6

PROMPT_TEMPLATE = (
    "Compute the numeric value of the following mathematical expression and RETURN ONLY THE NUMERIC RESULT.\n"
    "Do not include any explanation or units.\n\nExpression: {expr}\n\nResult:"
)

if not API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable is not set.")

client = Groq(api_key=API_KEY)

# Regex helpers
RE_NUMBER = re.compile(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?')

def normalize_text(t):
    if t is None:
        return None
    s = str(t).strip()
    s = s.replace(',', '')        
    s = s.replace('−','-')        
    return s.strip()

def parse_numeric_from_text(txt):
    """Parse the last numeric value from LLM response"""
    if not txt:
        return None
    s = normalize_text(txt)
    all_numbers = RE_NUMBER.findall(s)
    if all_numbers:
        try:
            return float(all_numbers[-1])
        except:
            pass
    return None

def is_close(a, b, rel_tol=1e-9, abs_tol=1e-7):
    try:
        return abs(float(a) - float(b)) <= max(abs_tol, rel_tol * abs(float(b)))
    except Exception:
        return False

def build_messages(expression):
    system = {"role": "system", "content": "You are a calculator. Return only the numeric result."}
    user = {"role": "user", "content": PROMPT_TEMPLATE.format(expr=expression)}
    return [system, user]

def call_groq_with_retries(messages, model=MODEL, max_retries=MAX_RETRIES):
    attempt = 0
    last_exception = None
    while attempt <= max_retries:
        attempt += 1
        t0 = time.perf_counter()
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0,
                max_completion_tokens=64
            )
            latency_ms = (time.perf_counter() - t0) * 1000.0
            return True, resp, latency_ms
        except RequestException as e:
            last_exception = str(e)
        except Exception as e:
            last_exception = str(e)
        if attempt <= max_retries:
            time.sleep(RETRY_BACKOFF_BASE * attempt)
    return False, last_exception, None


def run_benchmark_method_4():
    df = pd.read_csv(INPUT_CSV)
    
    # Initialize output columns
    df['Method_Used'] = None
    df['Output_Answer'] = None
    df['IsCorrect'] = None
    df['Latency_ms'] = None
    df['Invocations'] = None
    df['Token_Count'] = None
    df['CPU_Cycles'] = None
    df['RAM_Peak_MB'] = None
    df['Env_Status'] = None
    df['Network_Bytes_Sent/Received'] = None
    df['Raw_LLM_Response'] = None
    
    proc = psutil.Process(os.getpid())
    total = len(df)
    
    for idx, row in df.iterrows():
        equation = row.get("Equation")
        expected = row.get("Answer", None)

        # Resource capture start
        start_cpu = proc.cpu_times()
        start_mem = proc.memory_info().rss
        start_time = time.perf_counter()
        messages = build_messages(equation)

        # Call Groq
        ok, resp, latency_ms = call_groq_with_retries(messages)
        
        end_time = time.perf_counter()
        end_mem = proc.memory_info().rss
        end_cpu = proc.cpu_times()

        cpu_delta = (end_cpu.user - start_cpu.user) + (end_cpu.system - start_cpu.system)
        ram_delta_mb = max(0.0, (end_mem - start_mem) / (1024.0*1024.0))
        latency_ms = latency_ms if latency_ms is not None else (end_time - start_time) * 1000.0

        parsed = None
        token_count = None
        raw_text = None
        env_status = "Groq_API_Error"

        if ok:
            try:
                choice = getattr(resp, "choices", None)
                if choice:
                    first = choice[0] if isinstance(choice, (list, tuple)) else choice
                    msg = None
                    if hasattr(first, "message") and hasattr(first.message, "content"):
                        msg = first.message.content
                    elif isinstance(first, dict) and "message" in first:
                        msg = first["message"].get("content", "")
                    else:
                        msg = str(first)
                    raw_text = msg
                else:
                    raw_text = str(resp)
                
                usage = getattr(resp, "usage", None)
                if usage and hasattr(usage, "total_tokens"):
                    token_count = int(usage.total_tokens)
                elif isinstance(usage, dict) and "total_tokens" in usage:
                    token_count = int(usage["total_tokens"])
                
                parsed = parse_numeric_from_text(raw_text)
                env_status = "Groq_API_OK"
            except Exception as e:
                raw_text = str(resp)
                env_status = f"Groq_Parse_Error:{str(e)[:100]}"
        else:
            raw_text = str(resp)
            env_status = f"Groq_Call_Error:{raw_text[:100]}"

        # Correctness check
        is_corr = 0
        try:
            if parsed is not None and expected is not None and is_close(parsed, float(expected)):
                is_corr = 1
        except Exception:
            is_corr = 0

        bytes_sent = len(json.dumps(messages).encode("utf-8"))
        bytes_received = len(str(raw_text).encode("utf-8")) if raw_text else 0

        # Update columns
        df.at[idx, "Method_Used"] = "LLM_Groq"
        df.at[idx, "Output_Answer"] = parsed
        df.at[idx, "IsCorrect"] = is_corr
        df.at[idx, "Latency_ms"] = float(latency_ms)
        df.at[idx, "Invocations"] = 1
        df.at[idx, "Token_Count"] = int(token_count) if token_count is not None else None
        df.at[idx, "CPU_Cycles"] = float(cpu_delta)
        df.at[idx, "RAM_Peak_MB"] = float(ram_delta_mb)
        df.at[idx, "Env_Status"] = env_status
        df.at[idx, "Network_Bytes_Sent/Received"] = f"{bytes_sent}/{bytes_received}"
        df.at[idx, "Raw_LLM_Response"] = (raw_text[:500] if raw_text else "")

        print(f"[{idx+1}/{total}] parsed={parsed} expected={expected} correct={is_corr} latency={latency_ms:.2f}ms")

    # Save results
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved results to {OUTPUT_CSV}")
    
    accuracy = df['IsCorrect'].sum() / len(df) * 100
    print(f"Accuracy: {accuracy:.2f}%")


if __name__ == "__main__":
    run_benchmark_method_4()
