from alphasift import dsa_adapter
from alphasift.models import Pick, ScreenResult, StrategyInfo


def test_list_strategies_returns_stable_shape(monkeypatch):
    monkeypatch.setattr(
        dsa_adapter,
        "load_strategies",
        lambda: [
            StrategyInfo(
                name="dual_low",
                display_name="Dual Low",
                description="Low valuation strategy",
                version="1",
                category="value",
                tags=["value"],
                market_scope=["cn"],
            )
        ],
    )

    assert dsa_adapter.list_strategies() == [
        {
            "id": "dual_low",
            "name": "Dual Low",
            "description": "Low valuation strategy",
            "version": "1",
            "category": "value",
            "tags": ["value"],
            "market_scope": ["cn"],
        }
    ]


def test_screen_returns_stable_dsa_contract(monkeypatch):
    calls = []

    monkeypatch.setattr(
        dsa_adapter,
        "run_screen",
        lambda *args, **kwargs: calls.append((args, kwargs)) or ScreenResult(
            strategy="dual_low",
            market="cn",
            strategy_version="1",
            strategy_category="value",
            snapshot_count=100,
            after_filter_count=3,
            run_id="run123",
            llm_ranked=True,
            llm_coverage=1.0,
            llm_market_view="market ok",
            picks=[
                Pick(
                    rank=1,
                    code="600519",
                    name="Kweichow Moutai",
                    final_score=88.5,
                    screen_score=80.0,
                    llm_score=90.0,
                    llm_thesis="LLM likes the setup",
                    ranking_reason="",
                    risk_level="medium",
                    risk_flags=["valuation"],
                    price=1688.0,
                    pe_ratio=10.0,
                    pb_ratio=1.0,
                    revenue_yoy=18.6,
                    net_profit_yoy=125.3,
                    dividend_yield_pct=1.2,
                    debt_ratio_pct=28.5,
                    float_market_cap_cny=3_200_000_000,
                    report_period="2026-03-31",
                    revenue_report_period="2026-03-31",
                    net_profit_report_period="2025-12-31",
                    financial_report_period="2026-03-31",
                    source="iwencai",
                    source_status="partial",
                    source_observed_at="2026-08-12T06:00:00+00:00",
                    trade_date="2026-08-12",
                    market="SZ",
                    board="main",
                    source_fields={"net_profit_yoy": {"column": "净利润同比增长率[20260331]", "raw": 125.3}},
                    data_complete=False,
                    missing_optional_fields=["industry"],
                    industry="Baijiu",
                    factor_scores={"value": 88.0, "liquidity": 72.0},
                    dsa_context={
                        "enriched": True,
                        "quote": {"price": 1688.0},
                        "news": {"results": [{"title": "贵州茅台公告"}]},
                    },
                    dsa_news=[{"title": "贵州茅台公告"}],
                    dsa_analysis_summary="DSA新闻: 贵州茅台公告",
                    post_analysis_summaries={"scorecard": "Local scorecard: value_quality"},
                )
            ],
            degradation=["fallback used"],
            source_errors=["source timeout"],
        ),
    )

    context = {"dsa": {"contract_version": "1"}}
    payload = dsa_adapter.screen("dual_low", market="cn", max_results=5, context=context)

    assert calls[0][1]["use_llm"] is True
    assert calls[0][1]["context"] is context
    assert payload["contract_version"] == "1"
    assert payload["run_id"] == "run123"
    assert payload["llm_ranked"] is True
    assert payload["llm_coverage"] == 1.0
    assert payload["candidate_count"] == 1
    assert payload["warnings"] == ["fallback used"]
    assert payload["source_errors"] == ["source timeout"]
    assert payload["candidates"][0]["code"] == "600519"
    assert payload["candidates"][0]["score"] == 88.5
    assert payload["candidates"][0]["risk_flags"] == ["valuation"]
    assert payload["candidates"][0]["llm_score"] == 90.0
    assert payload["candidates"][0]["llm_thesis"] == "LLM likes the setup"
    assert payload["candidates"][0]["reason"] == "LLM likes the setup"
    assert payload["candidates"][0]["price"] == 1688.0
    assert payload["candidates"][0]["pe_ratio"] == 10.0
    assert payload["candidates"][0]["pb_ratio"] == 1.0
    assert payload["candidates"][0]["revenue_yoy"] == 18.6
    assert payload["candidates"][0]["net_profit_yoy"] == 125.3
    assert payload["candidates"][0]["dividend_yield_pct"] == 1.2
    assert payload["candidates"][0]["debt_ratio_pct"] == 28.5
    assert payload["candidates"][0]["float_market_cap_cny"] == 3_200_000_000
    assert payload["candidates"][0]["report_period"] == "2026-03-31"
    assert payload["candidates"][0]["revenue_report_period"] == "2026-03-31"
    assert payload["candidates"][0]["net_profit_report_period"] == "2025-12-31"
    assert payload["candidates"][0]["financial_report_period"] == "2026-03-31"
    assert payload["candidates"][0]["source"] == "iwencai"
    assert payload["candidates"][0]["source_status"] == "partial"
    assert payload["candidates"][0]["trade_date"] == "2026-08-12"
    assert payload["candidates"][0]["market"] == "SZ"
    assert payload["candidates"][0]["board"] == "main"
    assert payload["candidates"][0]["source_fields"]["net_profit_yoy"]["raw"] == 125.3
    assert payload["candidates"][0]["data_complete"] is False
    assert payload["candidates"][0]["missing_optional_fields"] == ["industry"]
    assert payload["candidates"][0]["industry"] == "Baijiu"
    assert payload["candidates"][0]["dsa_context"]["enriched"] is True
    assert payload["candidates"][0]["dsa_news"][0]["title"] == "贵州茅台公告"
    assert payload["candidates"][0]["dsa_analysis_summary"] == "DSA新闻: 贵州茅台公告"


def test_status_is_fail_open(monkeypatch):
    monkeypatch.setattr(dsa_adapter, "list_strategies", lambda context=None: (_ for _ in ()).throw(RuntimeError("boom")))

    payload = dsa_adapter.get_status()

    assert payload["available"] is False
    assert payload["contract_version"] == "1"
    assert "boom" in payload["error"]
