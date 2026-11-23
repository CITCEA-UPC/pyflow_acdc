"""Market_Coeff tests using synthetic order-book data (no EPEX / ENTSO-E files)."""

import pandas as pd
import plotly.graph_objects as go
import pytest

import pyflow_acdc as pyf


def _minimal_coef_hour_dict():
    return {
        "Hour": 1,
        "poly": {
            "a_BC": 1.0,
            "b_BC": 2.0,
            "c_BC": 3.0,
            "a_CG": 4.0,
            "b_CG": 5.0,
            "c_CG": 6.0,
            "P_min": -10.0,
            "P_max": 100.0,
        },
        "Market_price": 55.0,
        "Volume_eq": 100.0,
    }


def _minimal_epex_order_book_df():
    """Synthetic EPEX-shaped order book for one hour on a non-leap year."""
    rows = []
    base = {"Date": "01/01/2023", "Hour": 1, "C3": 0, "C4": 0}
    sell_curve = [(10, 10), (50, 30), (100, 50), (150, 70), (200, 90)]
    purchase_curve = [(10, 100), (50, 80), (100, 60), (150, 40), (200, 20)]
    for volume, price in sell_curve:
        rows.append({**base, "Volume": volume, "Price": price, "Sale/Purchase": "Sell"})
    for volume, price in purchase_curve:
        rows.append({**base, "Volume": volume, "Price": price, "Sale/Purchase": "Purchase"})
    return pd.DataFrame(rows)


def test_price_zone_data_pd_from_dict():
    coef_df = pyf.price_zone_data_pd([_minimal_coef_hour_dict()])

    assert len(coef_df) == 1
    assert coef_df.index.tolist() == [1]
    assert coef_df.loc[1, "a_BC"] == 1.0
    assert coef_df.loc[1, "price"] == 55.0
    assert coef_df.loc[1, "volume"] == 100.0


def test_market_coeff_synthetic_epex_pipeline(tmp_path, monkeypatch):
    order_book = _minimal_epex_order_book_df()
    small_data, timing_info = pyf.price_zone_coef_data(order_book, start=1, end=1)

    assert len(small_data) == 1
    entry = small_data[0]
    assert not entry["Sell"].empty
    assert not entry["Purchase"].empty
    assert "Integrated_sets" in entry
    assert "prediction_BC" in entry
    assert "prediction_CG" in entry
    assert set(entry["poly"]) >= {"a_BC", "b_BC", "c_BC", "a_CG", "b_CG", "c_CG", "P_min", "P_max"}
    assert timing_info["tot process"] >= 0

    coef_df = pyf.price_zone_data_pd(small_data)
    assert len(coef_df) == 1

    csv_path = tmp_path / "market_coef"
    pyf.price_zone_data_pd(small_data, save_csv=str(csv_path))
    assert csv_path.with_suffix(".csv").is_file()

    shown = {}

    def _fake_show(fig, renderer=None):
        shown["fig"] = fig

    monkeypatch.setattr("pyflow_acdc.Market_Coeff.pio.show", _fake_show)
    fig = pyf.plot_curves(small_data, hour=1, name="Synthetic")

    assert isinstance(fig, go.Figure)
    assert shown["fig"] is fig


def run_test():
    pytest.main([__file__, "-q"])


if __name__ == "__main__":
    run_test()
