"""
Method 3 Visualizations
Generates charts to analyze SOAP Calculator benchmark results.
Run this after completing the benchmark to get visual insights.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the benchmark summary data
df = pd.read_csv('Results/Method 3/benchmark_method_3_summary.csv')


# ============================================================================
# Plot 1: How does accuracy change with complexity?
# We'll bin complexity into 10 groups and see the accuracy trend
# ============================================================================

df['Complexity_Bin'] = pd.cut(df['Complexity'], bins=10, labels=False)
accuracy_by_complexity = df.groupby('Complexity_Bin').agg(
    Accuracy=('IsCorrect', 'mean'),
    Complexity_Mean=('Complexity', 'mean'),
    Count=('IsCorrect', 'count')
).reset_index()

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(accuracy_by_complexity['Complexity_Mean'], accuracy_by_complexity['Accuracy'], 
        'b-o', linewidth=2, markersize=8, label='Accuracy Rate')

ax.set_xlabel('Complexity')
ax.set_ylabel('Accuracy Rate')
ax.set_title('Complexity vs Accuracy (Method 3 - SOAP)')
ax.set_ylim(0, 1.05)
ax.grid(True, alpha=0.3)
ax.legend()
plt.tight_layout()

plt.savefig('Results/Method 3/Visualizations/complexity_vs_correctness.png', dpi=150)
print("Chart saved to Results/Method 3/Visualizations/complexity_vs_correctness.png")


# ============================================================================
# Plot 2: Correctness breakdown by operation type
# Stacked bar to show how many correct/incorrect per type
# ============================================================================

counts_type = df.groupby(['Type', 'IsCorrect']).size().unstack(fill_value=0)
counts_type.columns = ['Incorrect', 'Correct']

fig2, ax2 = plt.subplots(figsize=(10, 6))
counts_type.plot(kind='bar', stacked=True, ax=ax2, color=['#e74c3c', '#2ecc71'])

ax2.set_xlabel('Type')
ax2.set_ylabel('Count')
ax2.set_title('Type vs Correctness (Method 3 - SOAP)')
ax2.legend(title='Result')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

plt.savefig('Results/Method 3/Visualizations/type_vs_correctness.png', dpi=150)
print("Chart saved to Results/Method 3/Visualizations/type_vs_correctness.png")


# ============================================================================
# Plot 3: Latency analysis - comparing mean vs P95 across complexity
# Blue for mean, orange for P95 - helps spot outliers
# ============================================================================

fig3, ax3 = plt.subplots(figsize=(10, 6))

# Skip zero complexity values to avoid issues
df_plot = df[df['Complexity'] > 0].copy()

# Show both mean and P95 latencies
ax3.scatter(df_plot['Complexity'], df_plot['Latency_Mean_ms'], alpha=0.4, s=25, color='#3498db', label='Mean (points)')
ax3.scatter(df_plot['Complexity'], df_plot['Latency_P95_ms'], alpha=0.4, s=25, color='#e67e22', label='P95 (points)')

# Add trend lines so we can see the pattern more clearly
trend_mean = df_plot.groupby('Complexity')['Latency_Mean_ms'].mean().reset_index()
trend_p95 = df_plot.groupby('Complexity')['Latency_P95_ms'].mean().reset_index()

ax3.plot(trend_mean['Complexity'], trend_mean['Latency_Mean_ms'], 'b-', linewidth=2, marker='o', markersize=6, label='Mean Trend')
ax3.plot(trend_p95['Complexity'], trend_p95['Latency_P95_ms'], color='#e67e22', linestyle='-', linewidth=2, marker='s', markersize=6, label='P95 Trend')

ax3.set_xlabel('Complexity')
ax3.set_ylabel('Latency (ms)')
ax3.set_title('Complexity vs Latency Mean & P95 (Method 3 - SOAP)')
ax3.legend()
ax3.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig('Results/Method 3/Visualizations/complexity_vs_latency.png', dpi=150)
print("Chart saved to Results/Method 3/Visualizations/complexity_vs_latency.png")


# ============================================================================
# Plot 4: CPU time - mean vs peak
# Similar approach to latency, purple for mean, red for peak
# ============================================================================

fig4, ax4 = plt.subplots(figsize=(10, 6))

ax4.scatter(df_plot['Complexity'], df_plot['CPU_Time_Mean_ms'], alpha=0.4, s=25, color='#9b59b6', label='Mean (points)')
ax4.scatter(df_plot['Complexity'], df_plot['CPU_Time_Peak_ms'], alpha=0.4, s=25, color='#e74c3c', label='Peak (points)')

# Trend lines for clarity
trend_cpu_mean = df_plot.groupby('Complexity')['CPU_Time_Mean_ms'].mean().reset_index()
trend_cpu_peak = df_plot.groupby('Complexity')['CPU_Time_Peak_ms'].mean().reset_index()

ax4.plot(trend_cpu_mean['Complexity'], trend_cpu_mean['CPU_Time_Mean_ms'], color='#9b59b6', linestyle='-', linewidth=2, marker='o', markersize=6, label='Mean Trend')
ax4.plot(trend_cpu_peak['Complexity'], trend_cpu_peak['CPU_Time_Peak_ms'], color='#e74c3c', linestyle='-', linewidth=2, marker='s', markersize=6, label='Peak Trend')

ax4.set_xlabel('Complexity')
ax4.set_ylabel('CPU Time (ms)')
ax4.set_title('Complexity vs CPU Time Mean & Peak (Method 3 - SOAP)')
ax4.legend()
ax4.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig('Results/Method 3/Visualizations/complexity_vs_cpu_time.png', dpi=150)
print("Chart saved to Results/Method 3/Visualizations/complexity_vs_cpu_time.png")


# ============================================================================
# Plot 5: Memory usage - RAM peak across complexity levels
# Green theme for memory visualization
# ============================================================================

fig5, ax5 = plt.subplots(figsize=(10, 6))

ax5.scatter(df_plot['Complexity'], df_plot['RAM_Peak_Max_MB'], alpha=0.5, s=30, color='#27ae60', label='RAM Peak (points)')

# Average trend
trend_ram = df_plot.groupby('Complexity')['RAM_Peak_Max_MB'].mean().reset_index()
ax5.plot(trend_ram['Complexity'], trend_ram['RAM_Peak_Max_MB'], color='#27ae60', linestyle='-', linewidth=2, marker='o', markersize=6, label='Mean Trend')

ax5.set_xlabel('Complexity')
ax5.set_ylabel('RAM Peak (MB)')
ax5.set_title('Complexity vs RAM Peak (Method 3 - SOAP)')
ax5.legend()
ax5.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig('Results/Method 3/Visualizations/complexity_vs_ram.png', dpi=150)
print("Chart saved to Results/Method 3/Visualizations/complexity_vs_ram.png")


# ============================================================================
# Plot 6: SOAP calls count - should increase with nesting/complexity
# This one's interesting because more complex equations need more API calls
# ============================================================================

fig6, ax6 = plt.subplots(figsize=(10, 6))

ax6.scatter(df_plot['Complexity'], df_plot['SOAP_Calls_Count'], alpha=0.5, s=40, color='#8e44ad', label='Data Points')

trend_soap = df_plot.groupby('Complexity')['SOAP_Calls_Count'].mean().reset_index()
ax6.plot(trend_soap['Complexity'], trend_soap['SOAP_Calls_Count'], color='#8e44ad', linestyle='-', linewidth=2, marker='o', markersize=6, label='Mean Trend')

ax6.set_xlabel('Complexity')
ax6.set_ylabel('SOAP Calls Count')
ax6.set_title('Complexity vs SOAP Calls (Method 3 - SOAP)')
ax6.legend()
ax6.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig('Results/Method 3/Visualizations/complexity_vs_soap_calls.png', dpi=150)
print("Chart saved to Results/Method 3/Visualizations/complexity_vs_soap_calls.png")


# ============================================================================
# Plot 7: Message sizes - request vs response
# Blue for requests, orange for responses - should correlate with complexity
# ============================================================================

fig7, ax7 = plt.subplots(figsize=(10, 6))

ax7.scatter(df_plot['Complexity'], df_plot['Request_Size_Bytes'], alpha=0.4, s=25, color='#3498db', label='Request (points)')
ax7.scatter(df_plot['Complexity'], df_plot['Response_Size_Bytes'], alpha=0.4, s=25, color='#e67e22', label='Response (points)')

# Trend lines
trend_req = df_plot.groupby('Complexity')['Request_Size_Bytes'].mean().reset_index()
trend_resp = df_plot.groupby('Complexity')['Response_Size_Bytes'].mean().reset_index()

ax7.plot(trend_req['Complexity'], trend_req['Request_Size_Bytes'], color='#3498db', linestyle='-', linewidth=2, marker='o', markersize=6, label='Request Trend')
ax7.plot(trend_resp['Complexity'], trend_resp['Response_Size_Bytes'], color='#e67e22', linestyle='-', linewidth=2, marker='s', markersize=6, label='Response Trend')

ax7.set_xlabel('Complexity')
ax7.set_ylabel('Size (Bytes)')
ax7.set_title('Complexity vs Request/Response Size (Method 3 - SOAP)')
ax7.legend()
ax7.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig('Results/Method 3/Visualizations/complexity_vs_message_size.png', dpi=150)
print("Chart saved to Results/Method 3/Visualizations/complexity_vs_message_size.png")

print("\nAll visualizations generated successfully!")
