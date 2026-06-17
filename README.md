# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

## Submission
- Tool inventory: 
    - name: **search_listings**
        - inputs (parameter names and types, e.g. description (str)): 
            - `description` (str): a description of what the user wants; should be used as a guide to match for relevant results
            - `size` (str): the size of outfit that the user would like for the suggested item to be
            - `max_price` (float): the max price allowed from the list of available items that can be matched for the user 
        - outputs:
            - `list[dict]`: a list of relevant matching listings items
        - purpose: 
            >The tool search_listings will search through the listings.json dataset in the data folder and return items that match the arguments: description, size, and a max price. It will either return these matches, sorted by relevance, as an array or it will return an empty array. 
    - name: **suggest_outfit**
        - inputs (parameter names and types, e.g. description (str)):
            - `new_item` (dict): the new item that can be paired with the users current wardrobe
            - `wardrobe` (list): the user's current wardrobe
        - outputs:
            - `str`: a statement that suggests how the new item can go with the users current wardrobe
        - purpose: 
            >The suggest_object tool will be given a new item to add to the current wardrobe and generate the description of the new outfit as a suggestion
    - name: **create_fit_card**
        - inputs (parameter names and types, e.g. description (str)): 
            - `outfit_suggestion` (str): a suggested outfit
            - `new_item` (dict): the new item that was added to the user's wardrobe
        - outputs:
            - `str`: a social-media-shareable description of an outfit
        - purpose:
            >The create_fit_card tool will, given an outfit, generate a short casual, social-media-esque description of a complete outfit suggestion.
- How the planning loop works (describe the conditional logic, not just "it decides what to do"):
    >The planning loop acts as a sequential pipeline governed by fail-fast conditional logic to coordinate three tool calls. Wrapped in distinct try-except blocks, the control flow halts immediately if any tool fails or returns empty data, preventing cascading errors by logging a specific message and exiting early.
    
    >First, the function initializes the session, exiting immediately if setup fails. It then calls search_listings; the conditional logic checks for an empty result or an exception, returning early if either occurs. If successful, the top item is passed to suggest_outfit. The flow validates this output, triggering an early return if the suggestion is missing or fails. Finally, the outfit is passed to create_fit_card. If this final tool fails, the catch block dynamically appends the current day of the week to the error and exits. The final success path is only reached if all three tools execute flawlessly.
- State management approach: what is stored, when, and how it's passed between tools
    - **Initialization:** Created as a centralized dictionary by _new_session(query, wardrobe), capturing the raw user query and the wardrobe object. (If this initial setup throws an exception, it is replaced by a static dictionary containing only {"error": "Unable to process request"}).
    - **Search Results Storage:** Updated to store the complete list of matching items under the session["search_results"] key.
    - **Search Failure/Empty Check:** If the results list is empty or search_listings throws an exception, a descriptive message is injected into session["error"] before an early return.
    - **Item Selection:** The first element of the search results array is isolated and saved under the session["selected_item"] key.
    - **Outfit Suggestion Storage:** Updated to include the text recommendation under session["outfit_suggestion"] after processing by the tool.
    - **Outfit Failure Check:** If the suggestion tool returns a blank result or errors out, session["error"] is overwritten with "An outfit cannot be suggested at this time." before halting.
    - **Fit Card Storage:** Updated with the final social-media-ready asset under the session["fit_card"] key.
    - **Fit Card Failure Check:** If card creation fails, a dynamic error message string matching the current weekday (e.g., "no fit tuesday") is written to `session["error"]` right before exiting.
- Error handling strategy for each tool, with at least one concrete example from your testing
    - If any step fails validation or throws an exception, the function immediately halts further execution, writes a specific error message to `session["error"]`, and performs an early return of the current session state. This prevents invalid data from cascading into subsequent tool calls.
    - Example: I used the `No results path` listed in agent.py: `"designer ballgown size XXS under $5"` and verified that I was given an error message to update the query once I received an empty items list from from the `search_listings` tool; no other tool was called.
- Spec reflection: one way the spec helped you, one way implementation diverged from it and why
    - Writing out specs was a great way to get more familiar with the requirements of the project and to provide guidance on implementation. I diverged when it came to implementation because some of the function (tool) definitions had to change to better align with the LLM used as well as the flow that needed to run in the planning loop.
- AI usage section: at least 2 specific instances describing what you directed the AI to do and what you revised or overrode
    - Given the search_listings's specifications, Gemini implemented the search_listings function to filter the dataset based on price, size, and description keyword overlap to rank the selected items by relevance. An empty list was returned if there were no matching items. I had to change that the description from of the items was being used towards relevance. I updated to only use an items title.
    - Given the tool's specifications, Gemini implemented the suggest_outfit tool to interact with the LLM, generating a suggested outfit using the suggested item and the user's wardrobe. Gemini also implemented the parsing logic to return the generated suggestion or fail gracefully with the appropriate error. I had to update the version of the LLM being used.