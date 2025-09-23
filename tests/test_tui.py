import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from lep.tui.tui import TUI


@pytest.mark.asyncio
async def test_tui_fetch_status():
    tui = TUI([1], {1: 8081})
    with patch('aiohttp.ClientSession') as mock_session:
        mock_resp = AsyncMock()
        mock_resp.json = AsyncMock(return_value={"node_id": 1, "role": "leader"})
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_resp

        status = await tui.fetch_status(1)
        assert status["role"] == "leader"


@pytest.mark.asyncio
async def test_tui_fetch_status_error():
    tui = TUI([1], {1: 8081})
    with patch('aiohttp.ClientSession', side_effect=Exception("Connection error")):
        status = await tui.fetch_status(1)
        assert status["role"] == "unknown"