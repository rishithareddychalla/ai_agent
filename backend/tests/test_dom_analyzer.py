"""
Unit tests for DOMAnalyzer
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agent.dom.dom_analyzer import DOMAnalyzer


@pytest.mark.asyncio
async def test_generate_candidates():
    analyzer = DOMAnalyzer()
    
    # Test candidate generation for a search box
    candidates = await analyzer._generate_candidates(
        page=None,
        description="search box",
        element_type="input"
    )
    
    strategies = [c.strategy for c in candidates]
    
    # Assert primary strategies are included
    assert "aria-label" in strategies
    assert "aria-labelledby" in strategies
    assert "placeholder" in strategies
    assert "search-input-type" in strategies
    assert "search-name-attr" in strategies

    # Test candidate generation for a button
    btn_candidates = await analyzer._generate_candidates(
        page=None,
        description="Submit",
        element_type="button"
    )
    
    btn_strategies = [c.strategy for c in btn_candidates]
    assert "button-text" in btn_strategies
    assert "role-button" in btn_strategies


@pytest.mark.asyncio
async def test_find_element_fallback():
    analyzer = DOMAnalyzer()
    
    mock_page = MagicMock()
    
    # We mock page.locator() to raise an exception or return a mock locator
    # that fails visibility check, so we can test the fallback loop.
    mock_locator = MagicMock()
    mock_locator.first = mock_locator
    mock_locator.wait_for = AsyncMock(side_effect=Exception("Element not visible"))
    mock_page.locator.return_value = mock_locator
    
    locator = await analyzer.find_element(
        page=mock_page,
        description="non-existent button",
        element_type="button",
        timeout_ms=100
    )
    
    # Should return None since all strategies failed wait_for
    assert locator is None
    assert mock_page.locator.call_count > 0


@pytest.mark.asyncio
async def test_extract_page_data_schema():
    analyzer = DOMAnalyzer()
    
    mock_page = MagicMock()
    mock_page.url = "https://example.com"
    mock_page.title = AsyncMock(return_value="Example Page")
    
    mock_el1 = MagicMock()
    mock_el1.inner_text = AsyncMock(return_value="Item 1")
    mock_el2 = MagicMock()
    mock_el2.inner_text = AsyncMock(return_value="Item 2")
    
    mock_locator = MagicMock()
    mock_locator.all = AsyncMock(return_value=[mock_el1, mock_el2])
    mock_page.locator.return_value = mock_locator
    
    schema = {
        "items": ".item-class"
    }
    
    data = await analyzer.extract_page_data(mock_page, schema)
    
    assert data["url"] == "https://example.com"
    assert data["title"] == "Example Page"
    assert data["items"] == ["Item 1", "Item 2"]
    mock_page.locator.assert_called_with(".item-class")
