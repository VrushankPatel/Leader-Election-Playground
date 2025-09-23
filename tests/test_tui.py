from unittest.mock import MagicMock, patch

import pytest

from lep.tui.tui import TUI


class MockResponse:
    def __init__(self, json_data):
        self.json_data = json_data

    async def json(self):
        return self.json_data


class MockContextManager:
    def __init__(self, resp):
        self.resp = resp

    async def __aenter__(self):
        return self.resp

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
async def test_tui_fetch_status():
    tui = TUI([1], {1: 8081})
    with patch("lep.tui.tui.aiohttp.ClientSession") as mock_session_class:
        mock_session = MagicMock()
        mock_resp = MockResponse({"node_id": 1, "role": "leader"})
        mock_get_cm = MockContextManager(mock_resp)
        mock_session.get.return_value = mock_get_cm
        mock_session_cm = MockContextManager(mock_session)
        mock_session_class.return_value = mock_session_cm

        status = await tui.fetch_status(1)
        assert status["role"] == "leader"


@pytest.mark.asyncio
async def test_tui_fetch_status_error():
    tui = TUI([1], {1: 8081})
    with patch("aiohttp.ClientSession", side_effect=Exception("Connection error")):
        status = await tui.fetch_status(1)
        assert status["role"] == "unknown"
