from tramalia.core.doctor import Report, diagnose


def test_needs_node_true_when_missing():
    r = Report(stack=[], features=(), statuses=[], node_present=False, node_tools=["rulesync"])
    assert r.needs_node is True


def test_needs_node_false_when_present():
    r = Report(stack=[], features=(), statuses=[], node_present=True, node_tools=["rulesync"])
    assert r.needs_node is False


def test_needs_node_false_when_no_node_tools():
    r = Report(stack=[], features=(), statuses=[], node_present=False, node_tools=[])
    assert r.needs_node is False


def test_diagnose_flags_node_tools(tmp_path):
    (tmp_path / "angular.json").write_text("{}", encoding="utf-8")  # frontend -> ux/sync -> node
    rep = diagnose(tmp_path)
    assert any(t in rep.node_tools for t in ("rulesync", "lhci", "playwright", "repomix"))
