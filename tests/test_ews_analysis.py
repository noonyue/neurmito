import numpy as np

from scripts.source_audit.run_r021_ews_cohort import build_conditions, event_time


def test_r021_builds_complete_grouped_cohort():
    conditions = build_conditions()
    assert len(conditions) == 441
    assert {row["split"] for row in conditions} == {"train", "validation", "test"}
    assert len({row["group_key"] for row in conditions}) == len(conditions)


def test_event_time_requires_persistent_140_mv_crossing():
    t = np.arange(5.0)
    assert np.isnan(event_time(t, np.array([150.0, 139.0, 141.0, 138.0, 141.0])))
    assert event_time(t, np.array([150.0, 139.0, 138.0, 137.0, 136.0])) == 1.0
