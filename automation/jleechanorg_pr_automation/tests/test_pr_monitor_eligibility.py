from automation.jleechanorg_pr_automation import jleechanorg_pr_monitor as mon


def test_list_actionable_prs_conflicts_and_failing(monkeypatch, capsys):
    monitor = mon.JleechanorgPRMonitor()

    sample_prs = [
        {"repository": "repo/a", "number": 1, "title": "conflict", "mergeable": "CONFLICTING"},
        {"repository": "repo/b", "number": 2, "title": "failing", "mergeable": "MERGEABLE"},
        {"repository": "repo/c", "number": 3, "title": "passing", "mergeable": "MERGEABLE"},
    ]

    monkeypatch.setattr(monitor, "discover_open_prs", lambda: sample_prs)

    def fake_has_failing_checks(repo, pr_number):
        return pr_number == 2

    monkeypatch.setattr(mon, "has_failing_checks", fake_has_failing_checks)

    actionable = monitor.list_actionable_prs(max_prs=10)

    assert len(actionable) == 2
    assert {pr["number"] for pr in actionable} == {1, 2}

    captured = capsys.readouterr().out
    assert "Eligible for fixpr: 2" in captured
