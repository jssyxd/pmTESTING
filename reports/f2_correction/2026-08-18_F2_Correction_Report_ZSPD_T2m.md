# 2026-08-18 F2 Correction Report — ZSPD 2m Temperature

## Reasoning Process & Basis (Detailed)

### 1. Data Agent Output Cited
- Lineage as declared in Structured Report.
- Clean data limited to shared conversation tables (WU, TAF TX/TN, IFS, AIFS up to ~2026-08-18 23:00 UTC+8).
- QC: no fill of missing hours; integer vs 0.1 °C noted.

### 2. Hour-Layer Bias Calculation Attempt
**mode = max** (highest temp prediction)
- Required layer: past 72 h, only 12:00–16:00 UTC+8 errors.
- Available concurrent pairs from conversation: sparse. WU 12–16 h on 17th/18th around 30–31 °C; IFS/AIFS around 28.4–30.2 °C range in samples.
- Sample size inside strict layer insufficient for stable EWMA (α=0.35). Rolling mean not computable without exact paired series.

**mode = min**
- Layer 00:00–05:00 UTC+8: nighttime obs ~25–27 °C; models similar.
- Same sample-size limitation.

### 3. Bias Estimates
Because paired sample_size = 0 (or < minimum reliable threshold) under strict hour-layer filter relative to prediction time, bias left as null. No EWMA applied. No hallucinated values.

### 4. Corrected Forecast
Cannot produce corrected max_or_min_c. Integer_c_for_wu not generated.

### 5. Weights
None used (no valid bias).

### 6. F2 Reasoning
Judge Agent checks:
- Data leakage: none (historical shared data only).
- Homologous source: WU/METAR risk flagged, no double weight applied.
- Hour-layer error: rule followed by refusing to use non-layer hours.
- Conclusion: F2 = 0 because no actionable bias correction possible with available data at cutoff.

## Warnings
- Shared conversation ends before 2026-08-19 prediction cycle.
- Fresh Data Agent pull of METAR + current IFS/AIFS required for any non-zero F2.