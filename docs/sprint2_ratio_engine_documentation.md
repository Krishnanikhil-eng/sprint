# Sprint 2 — Financial Ratio Engine Architecture & Methodology Documentation

## 1. Executive Summary
The **Financial Ratio Engine** systematically computes 50+ Key Performance Indicators (KPIs), growth rates, and capital allocation patterns across 92 Nifty 100 companies (plus supplementary historical universe companies) for all available financial years (2011–2024). The computed output is persisted directly into the `financial_ratios` table in `nifty100.db`.

---

## 2. Core Profitability & Efficiency Ratios

### 2.1 Net Profit Margin (NPM)
$$\text{NPM} = \frac{\text{Net Profit}}{\text{Sales}} \times 100$$
- **Edge Case**: If $\text{Sales} \le 0$ or is `None`, NPM evaluates to `None`.

### 2.2 Operating Profit Margin (OPM)
$$\text{OPM} = \frac{\text{Operating Profit}}{\text{Sales}} \times 100$$
- **Edge Case**: If $\text{Sales} \le 0$ or is `None`, OPM evaluates to `None`.
- **Cross-Check**: Discrepancies $> 1.0\%$ relative to source metadata are logged for audit.

### 2.3 Return on Equity (ROE)
$$\text{ROE} = \frac{\text{Net Profit}}{\text{Equity Capital} + \text{Reserves}} \times 100$$
- **Edge Case**: If Total Equity ($\text{Equity Capital} + \text{Reserves}$) $\le 0$, ROE evaluates to `None`.

### 2.4 Return on Capital Employed (ROCE)
$$\text{ROCE} = \frac{\text{EBIT}}{\text{Equity Capital} + \text{Reserves} + \text{Borrowings}} \times 100$$
- **Bank Carve-Out Rule**: Suppressed (`None`) for Banking and Financial Institutions.

### 2.5 Return on Assets (ROA)
$$\text{ROA} = \frac{\text{Net Profit}}{\text{Total Assets}} \times 100$$
- **Edge Case**: If $\text{Total Assets} \le 0$, ROA evaluates to `None`.

---

## 3. Leverage & Debt Servicing Metrics

### 3.1 Debt-to-Equity (D/E)
$$\text{D/E} = \frac{\text{Borrowings}}{\text{Equity Capital} + \text{Reserves}}$$
- **Zero Debt Rule**: If $\text{Borrowings} = 0$, D/E evaluates to `0.0` (NOT `None`).
- **High Leverage Flag**: Triggered when $\text{D/E} > 5.0$, except for Financial entities.

### 3.2 Interest Coverage Ratio (ICR)
$$\text{ICR} = \frac{\text{Operating Profit} + \text{Other Income}}{\text{Interest Expense}}$$
- **Debt-Free Rule**: If $\text{Interest Expense} = 0$, ICR is `None`, label is `"Debt Free"`, warning flag is `False`.
- **Warning Threshold**: If $\text{ICR} < 1.5$, warning flag is `True`, label is `"Low Coverage"`.

---

## 4. CAGR Engine & 6-State Edge Classifier

$$\text{CAGR} = \left(\left(\frac{\text{End Value}}{\text{Start Value}}\right)^{\frac{1}{n}} - 1\right) \times 100$$

| State # | Condition | CAGR Value | Status Flag |
| :--- | :--- | :--- | :--- |
| 1 | $\text{Start} > 0$ and $\text{End} > 0$ | Computed Value | `NORMAL` |
| 2 | $\text{Start} > 0$ and $\text{End} < 0$ | `None` | `DECLINE_TO_LOSS` |
| 3 | $\text{Start} < 0$ and $\text{End} > 0$ | `None` | `TURNAROUND` |
| 4 | $\text{Start} < 0$ and $\text{End} < 0$ | `None` | `BOTH_NEGATIVE` |
| 5 | $\text{Start} = 0$ | `None` | `ZERO_BASE` |
| 6 | Missing / Insufficient Data ($n \le 0$) | `None` | `INSUFFICIENT` |

---

## 5. Cash Flow KPIs & 8-Pattern Capital Allocation Matrix

### 5.1 Free Cash Flow (FCF)
$$\text{FCF} = \text{CFO} + \text{CFI}$$

### 5.2 8-Pattern Capital Allocation Matrix
Based on the signs $(+ / -)$ of Operating (CFO), Investing (CFI), and Financing (CFF) cash flows:

1. **$(+, -, -)$**: `Shareholder Returns` (if $\text{CFO}/\text{PAT} > 1.0$) else `Reinvestor`
2. **$(+, +, -)$**: `Liquidating Assets`
3. **$(-, +, +)$**: `Distress Signal`
4. **$(-, -, +)$**: `Growth Funded by Debt`
5. **$(+, +, +)$**: `Cash Accumulator`
6. **$(-, -, -)$**: `Pre-Revenue`
7. **$(+, -, +)$**: `Mixed`
