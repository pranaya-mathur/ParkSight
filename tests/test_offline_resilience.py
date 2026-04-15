"""Future: edge scene buffering when cloud is unreachable (sync on reconnect)."""

import pytest


@pytest.mark.skip(reason="Local edge queue + replay sync not implemented yet")
def test_edge_buffers_scenes_when_api_down():
    assert False
