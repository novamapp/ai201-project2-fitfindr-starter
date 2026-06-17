import datetime
from unittest.mock import MagicMock, patch
import pytest

from tools import create_fit_card, search_listings, suggest_outfit


# ──────────────────────────────────────────────────────────────────────────────
# 1. FIXTURES & MOCKS
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_listings():
    """Provides a controlled dataset for testing search_listings."""
    return [
        {"title": "Vintage Graphic Tee", "description": "Cool 90s band shirt", "size": "M", "price": 25.0},
        {"title": "Modern Hoodie", "description": "Plain black hoodie", "size": "L", "price": 45.0},
        {"title": "Vintage Denim Jacket", "description": "Classic blue jean jacket", "size": "S/M", "price": 15.0},
    ]

@pytest.fixture
def sample_item():
    """A sample thrifted item dict."""
    return {
        "title": "Vintage Denim Jacket",
        "price": "$15",
        "platform": "Depop"
    }

@pytest.fixture
def sample_wardrobe():
    """A sample wardrobe with items."""
    return {
        "items": [
            {"title": "White Sneakers"},
            {"title": "Black Slim Jeans"}
        ]
    }


# ──────────────────────────────────────────────────────────────────────────────
# 2. TESTS FOR search_listings
# ──────────────────────────────────────────────────────────────────────────────

def test_search_returns_results(mock_listings):
    with patch('tools.load_listings', return_value=mock_listings):
        results = search_listings("vintage graphic tee", size=None, max_price=50)
        assert isinstance(results, list)
        assert len(results) == 2
        assert results[0]["title"] == "Vintage Graphic Tee"

def test_search_empty_results(mock_listings):
    with patch('tools.load_listings', return_value=mock_listings):
        results = search_listings("designer ballgown", size="XXS", max_price=5)
        assert results == []

def test_search_price_filter(mock_listings):
    with patch('tools.load_listings', return_value=mock_listings):
        results = search_listings("vintage", size=None, max_price=20)
        assert len(results) == 1
        assert all(item["price"] <= 20 for item in results)

def test_search_size_case_insensitive_substring(mock_listings):
    with patch('tools.load_listings', return_value=mock_listings):
        # "m" should match "S/M" and "M"
        results = search_listings("vintage", size="m", max_price=None)
        assert len(results) == 2

def test_search_empty_description(mock_listings):
    with patch('tools.load_listings', return_value=mock_listings):
        results = search_listings("   ", size=None, max_price=None)
        assert results == []


# ──────────────────────────────────────────────────────────────────────────────
# 3. TESTS FOR suggest_outfit
# ──────────────────────────────────────────────────────────────────────────────

@patch('tools._get_groq_client')
def test_suggest_outfit_with_wardrobe(mock_get_client, sample_item, sample_wardrobe):
    # Setup mock LLM response
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_choice = MagicMock()
    mock_choice.message.content = "Pair the Denim Jacket with your Black Slim Jeans and White Sneakers."
    mock_client.chat.completions.create.return_value.choices = [mock_choice]

    result = suggest_outfit(sample_item, sample_wardrobe)
    
    assert "Black Slim Jeans" in result
    mock_client.chat.completions.create.assert_called_once()
    # Verify it pulled the correct user prompt variant
    _, kwargs = mock_client.chat.completions.create.call_args
    assert "list of items currently in the user's wardrobe" in kwargs['messages'][1]['content']

@patch('tools._get_groq_client')
def test_suggest_outfit_empty_wardrobe(mock_get_client, sample_item):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_choice = MagicMock()
    mock_choice.message.content = "Since your wardrobe is empty, try pairing this with basic neutrals."
    mock_client.chat.completions.create.return_value.choices = [mock_choice]

    result = suggest_outfit(sample_item, {"items": []})
    
    assert "empty" in result.lower()
    _, kwargs = mock_client.chat.completions.create.call_args
    assert "digital wardrobe is currently empty" in kwargs['messages'][1]['content']

@patch('tools._get_groq_client')
def test_suggest_outfit_api_failure(mock_get_client, sample_item, sample_wardrobe):
    mock_get_client.side_effect = Exception("API Key Invalid")
    
    result = suggest_outfit(sample_item, sample_wardrobe)
    assert "An error occurred while generating outfit suggestions" in result


# ──────────────────────────────────────────────────────────────────────────────
# 4. TESTS FOR create_fit_card
# ──────────────────────────────────────────────────────────────────────────────

def test_create_fit_card_empty_outfit():
    current_day = datetime.datetime.now().strftime("%A")
    expected_fallback = f"no fit {current_day}"
    
    assert create_fit_card("", {"title": "Tee"}) == expected_fallback
    assert create_fit_card("   ", {"title": "Tee"}) == expected_fallback
    assert create_fit_card(None, {"title": "Tee"}) == expected_fallback

@patch('tools._get_groq_client')
def test_create_fit_card_success(mock_get_client, sample_item):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_choice = MagicMock()
    mock_choice.message.content = "Obsessed with this Vintage Denim Jacket I found on Depop for just $15. It pairs perfectly with casual streetwear."
    mock_client.chat.completions.create.return_value.choices = [mock_choice]

    caption = create_fit_card("Pair with black jeans", sample_item)
    
    assert "Vintage Denim Jacket" in caption
    assert "Depop" in caption
    assert "$15" in caption

@patch('tools._get_groq_client')
def test_create_fit_card_api_fallback(mock_get_client, sample_item):
    mock_get_client.side_effect = Exception("Rate limit reached")
    
    # Capture print statement if necessary, or just check the return value fallback
    caption = create_fit_card("Pair with black jeans", sample_item)
    
    assert caption == "Obsessed with this Vintage Denim Jacket I found on Depop for just $15."