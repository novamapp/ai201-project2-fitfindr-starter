"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import datetime
from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
    """
    # 1. Initialize the single source of truth session state
    try:
        session = _new_session(query, wardrobe)
    except Exception:
        # If initial setup fails, terminate immediately with the generic error
        print("Unable to process request")
        return {"error": "Unable to process request"}
    
    print("query:", session["query"])

    # 2. Execute search_listings
    try:
        # Extract parsed fields if they were populated during initialization,
        # otherwise fallback to safe defaults or empty strings.
        parsed_args = session.get("parsed", {})
        description = parsed_args.get("description", query)
        size = parsed_args.get("size", None)
        max_price = parsed_args.get("max_price", None)
        
        results = search_listings(description=description, size=size, max_price=max_price)
        session["search_results"] = results
        
        if not results:
            error_msg = "No items found matching your request. Try broadening your description or removing size/price constraints."
            session["error"] = error_msg
            print(error_msg)
            return session
            
    except Exception as e:
        error_msg = f"No items found due to a search error. Please try updating your query. (Error: {str(e)})"
        session["error"] = error_msg
        print(error_msg)
        return session

    # 3. Process the top result and generate an outfit suggestion
    session["selected_item"] = results[0]
    print("selected_item:", session["selected_item"])
    
    try:
        outfit_suggestion = suggest_outfit(session["selected_item"], session["wardrobe"])
        if not outfit_suggestion:
            raise ValueError("No suggestions generated")
            
        session["outfit_suggestion"] = outfit_suggestion
        print("outfit_suggestion:", session["outfit_suggestion"])
        
    except Exception:
        error_msg = "An outfit cannot be suggested at this time."
        session["error"] = error_msg
        print(error_msg)
        return session

    # 4. Generate the social-media-style fit card
    try:
        fit_card = create_fit_card(session["outfit_suggestion"], session["selected_item"])
        if not fit_card:
            raise ValueError("Failed to create fit card")
            
        session["fit_card"] = fit_card
        
    except Exception:
        # Dynamically determine the day of the week for the specific error requirement
        day_of_week = datetime.datetime.now().strftime("%A").lower()
        error_msg = f"no fit {day_of_week}"
        session["error"] = error_msg
        print(error_msg)
        return session

    # 5. Return successfully completed session
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
