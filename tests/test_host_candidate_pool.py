from pathlib import Path

import pandas as pd
import pytest

from alphasift.config import Config
from alphasift.pipeline import screen


# 构造不访问外部数据和模型的主力策略测试配置。
def _config() -> Config:
    config = Config(
        llm_api_key="",
        llm_model="",
        strategies_dir=Path("strategies"),
    )
    config.post_analyzers = []
    config.daily_enrich_enabled = False
    config.risk_enabled = False
    config.portfolio_diversity_enabled = False
    return config


# 验证宿主候选池替换初始快照并保留主力字段和排序。
def test_screen_consumes_host_initial_candidate_pool(monkeypatch):
    monkeypatch.setattr(
        "alphasift.pipeline.fetch_snapshot_with_fallback",
        lambda *_args, **_kwargs: pytest.fail("snapshot provider must not run"),
    )

    def get_initial_candidates(*, strategy: str, market: str):
        assert strategy == "main_force"
        assert market == "cn"
        return {
            "status": "partial",
            "source": "iwencai",
            "warnings": ["optional_fields_missing:pb"],
            "candidates": [
                {
                    "code": "000001",
                    "name": "平安银行",
                    "main_fund_inflow_cny": 2_000_000_000,
                    "range_change_pct": 8.0,
                    "total_mv": 300_000_000_000,
                    "pe_ratio": 6.0,
                    "data_complete": False,
                    "missing_optional_fields": ["pb"],
                },
                {
                    "code": "600000",
                    "name": "浦发银行",
                    "main_fund_inflow_cny": 1_000_000_000,
                    "range_change_pct": 5.0,
                    "total_mv": 250_000_000_000,
                    "pe_ratio": 7.0,
                },
            ],
        }

    result = screen(
        "main_force",
        max_output=2,
        use_llm=False,
        context={
            "host": {
                "contract_version": "1",
                "get_initial_candidates": get_initial_candidates,
            }
        },
        config=_config(),
    )

    assert result.snapshot_source == "iwencai"
    assert result.snapshot_count == 2
    assert result.picks[0].code == "000001"
    assert result.picks[0].main_fund_inflow_cny == 2_000_000_000
    assert result.picks[0].missing_optional_fields == ["pb"]
    assert "optional_fields_missing:pb" in result.degradation


# 验证宿主显式不可用不会静默回退到 AlphaSift 普通快照。
def test_screen_fails_when_host_candidate_pool_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        "alphasift.pipeline.fetch_snapshot_with_fallback",
        lambda *_args, **_kwargs: pytest.fail("snapshot fallback must not run"),
    )

    with pytest.raises(RuntimeError, match="Host initial candidate pool unavailable"):
        screen(
            "main_force",
            use_llm=False,
            context={
                "host": {
                    "contract_version": "1",
                    "get_initial_candidates": lambda **_kwargs: {
                        "status": "unavailable",
                        "message": "iwencai direct call failed",
                    },
                }
            },
            config=_config(),
        )
