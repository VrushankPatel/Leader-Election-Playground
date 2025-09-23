import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from lep.tui.tui import TUI


@pytest.mark.asyncio
async def test_tui_fetch_status():
    tui = TUI([1], {1: 8081})
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_resp = AsyncMock()
        mock_resp.json = AsyncMock(return_value={"node_id": 1, "role": "leader"})
        mock_get_cm = AsyncMock()
        mock_get_cm.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_get_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session.get.return_value = mock_get_cm
        mock_session_class.return_value = mock_session

        status = await tui.fetch_status(1)
        assert status["role"] == "leader"


@pytest.mark.asyncio
async def test_tui_fetch_status_error():
    tui = TUI([1], {1: 8081})
    with patch('aiohttp.ClientSession', side_effect=Exception("Connection error")):
        status = await tui.fetch_status(1)
        assert status["role"] == "unknown"