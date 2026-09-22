from swarm import should_use_swarm


def test_swarm_requires_independent_read_only_domains():
    assert should_use_swarm("research the latest quantum news and check backend server status")
    assert not should_use_swarm("open the browser and search for quantum news")
    assert not should_use_swarm("tell me a joke")

