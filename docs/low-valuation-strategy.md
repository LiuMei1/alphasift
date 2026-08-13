# Low valuation host strategy

`low_valuation` is a CN-only host-candidate strategy. The host must provide a non-empty candidate pool that has already enforced `0 < PE <= 20`, `0 < PB <= 1.5`, dividend yield at least `1%`, debt ratio at most `30%`, and the Shanghai/Shenzhen main-board exclusions.

AlphaSift does not fetch or reconstruct these candidates from its normal snapshot providers. A missing, unavailable, failed, or empty host pool is an explicit error. Within the valid pool, `low_float_market_cap` gives higher scores to smaller positive `float_market_cap_cny` values; missing or invalid values score zero. Value, stability and liquidity remain secondary ranking factors. Risk coverage and LLM ranking may reorder candidates but must not relax the host hard gates.

The stable DSA adapter and LLM context retain `pe_ratio`, `pb_ratio`, `dividend_yield_pct`, `debt_ratio_pct`, `float_market_cap_cny`, `financial_report_period`, `trade_date`, source/status/audit fields, and completeness diagnostics.
