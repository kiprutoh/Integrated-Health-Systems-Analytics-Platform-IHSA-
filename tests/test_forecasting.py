from forecasting.base import approach_to_target, cagr_project, linear_project

def test_approach_converges_toward_target():
    p = approach_to_target(10, 2, 2023, horizon=6)
    assert p.values[0] == 10
    assert p.values[-1] < p.values[0]
    assert abs(p.values[-1] - 2) < abs(p.values[0] - 2)

def test_cagr_and_linear_lengths():
    assert len(cagr_project(100, 0.05, 2023, horizon=5).values) == 6
    assert len(linear_project(100, -3, 2023, horizon=5).values) == 6
