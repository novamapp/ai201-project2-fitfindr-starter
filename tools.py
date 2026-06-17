"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import datetime

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.
    """
    # 1. Load all listings
    # (Assuming load_listings() is imported or defined elsewhere in your module)
    listings = load_listings()

    # Normalize description input into a set of lowercased keywords for matching
    desc_keywords = set(description.lower().split())
    if not desc_keywords:
        return []

    scored_listings = []

    for listing in listings:
        # 2. Filter by max_price (inclusive)
        if max_price is not None and listing.get("price", 0.0) > max_price:
            continue

        # 2. Filter by size (case-insensitive substring match)
        if size is not None:
            listing_size = str(listing.get("size", "")).lower()
            target_size = size.lower()
            if target_size not in listing_size:
                continue

        # 3. Score each remaining listing by keyword overlap with `description`
        # We check both the title and the description fields for matches
        title_words = set(str(listing.get("title", "")).lower().split())
        # body_words = set(str(listing.get("description", "")).lower().split())
        listing_words = title_words #.union(body_words)

        # print("overlapping words:", desc_keywords.intersection(listing_words))
        # Calculate overlap score
        score = len(desc_keywords.intersection(listing_words))

        # 4. Drop any listings with a score of 0
        if score > 0:
            scored_listings.append((score, listing))

    # 5. Sort by score, highest first, and extract the listing dicts
    # Python's sort is stable, so order is preserved for identical scores
    scored_listings.sort(key=lambda item: item[0], reverse=True)

    return [listing for score, listing in scored_listings]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """Given a thrifted item and the user's wardrobe, suggest 1–2 complete
    outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
          wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, return an appropriate error message.
        If there is an error with the LLM, return the appropriate error message
    """
    try:
        # 1. Initialize the Groq client inside the try block to catch init errors
        client = _get_groq_client()

        # Extract the list of items from the wardrobe dictionary safely
        wardrobe_items = wardrobe.get("items", [])

        # 2. Build the system and user prompts based on wardrobe availability
        system_prompt = (
            "You are an expert personal stylist and fashion consultant. "
            "Your goal is to help users style their clothing items into cohesive, fashionable outfits."
        )

        if not wardrobe_items:
            # Step 2: Empty wardrobe logic
            user_prompt = f"""
            The user is considering buying this thrifted item:
            {new_item}

            The user's digital wardrobe is currently empty. 
            Please provide general styling ideas for this item. Mention what kinds of items, 
            colors, and silhouettes pair well with it, and what overall vibe or occasions it suits.
            """
        else:
            # Step 3: Wardrobe is not empty logic
            user_prompt = f"""
            The user is considering buying this thrifted item:
            {new_item}

            Here is a list of items currently in the user's wardrobe:
            {wardrobe_items}

            Please suggest 1–2 complete outfit combinations using the new thrifted item 
            and specific, named pieces from their existing wardrobe. Explain why these combinations work.
            """

        # 3. Call the LLM
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )

        # 4. Return the LLM's response
        return completion.choices[0].message.content

    except Exception as e:
        # Catches client init failures, network dropouts, API errors, or bad dict schemas
        return f"An error occurred while generating outfit suggestions: {str(e)}"


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, then returned "no fit "+[insert day of
        the week]
    """
    # 1. Guard against an empty or whitespace-only outfit string
    if not outfit or not outfit.strip():
        current_day = datetime.datetime.now().strftime("%A")
        return f"no fit {current_day}"

    # Extract required details from the new_item dictionary
    # Using .get() with fallback defaults to prevent KeyErrors
    item_name = new_item.get("title") or new_item.get("name", "thrifted find")
    price = new_item.get("price", "steal")
    platform = new_item.get("platform") or new_item.get(
        "source", "online thrift"
    )

    # 2. Build the prompt matching the style guidelines
    prompt = f"""
    You are a trendy fashion influencer writing an OOTD (Outfit of the Day) caption for Instagram/TikTok.

    Here is the thrifted item you just scored:
    - Item: {item_name}
    - Price: {price}
    - Platform: {platform}

    Here is the outfit idea built around it:
    "{outfit}"

    Write a short, shareable caption based on this info.
    Guidelines:
    - Length: Exactly 2 to 4 sentences.
    - Tone: Casual, authentic, and enthusiastic (like a real social media post, NOT a boring product description).
    - Requirements: Naturally mention the item name, price, and platform exactly once each. Capture the overall vibe of the outfit.
    - Do not include hashtags, emojis, or introductory text (like "Here is your caption:"). Just return the caption itself.
    """

    # 3. Call the LLM with a higher temperature for variety
    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            # Using a standard fast model, adjust model name if needed
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative social media copywriter.",
                },
                {"role": "user", "content": prompt},
            ],
            # Higher temperature ensures unique variations every time
            temperature=0.85,
            max_tokens=150,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        # Fallback or error handling depending on how you want to manage API failures
        print(f"Error generating fit card: {e}")
        return f"Obsessed with this {item_name} I found on {platform} for just {price}."
