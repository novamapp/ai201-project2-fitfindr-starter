# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---
## A Complete Interaction

FitFindr is an agent that will use at least three tools generate the description of an outfit which can be shared publicly. The agent will select the tools to apply in the necessary order and will either generate the description of an outfit or, on error, respond to the user with an appropriate message.

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
The tool search_listings will search through the listings.json dataset in the data folder and return at most three items that match the arguments: description, size, and a max price. It will either return these matches, sorted by relevance, as an array or it will return an empty array. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): a description of what the user wants; should be used as a guide to match for relevant results
- `size` (str): the size of outfit that the user would like for the suggested item to be
- `max_price` (float): the max price allowed from the list of available items that can be matched for the user 

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
- at most three relevant matching listings items

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
- if search_listings returns an empty array or any other falsey value then do not call any other tools; let the user know that there are no matching search listings and make a suggest on how the user can improve their request

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
The suggest_object tool will be given a new item to add to the current wardrobe and generate the description of the new outfit as a suggestion

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (str): the new item that can be paired with the users current wardrobe
- `wardrobe` (list): the user's current wardrobe

**What it returns:**
<!-- Describe the return value -->
- a statement that suggests how the new item can go with the users current wardrobe

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
- if the new item cannot be paired with current wardrobe, then do not call any other tools; let the user know that there are no suggested ways to pair the new item to the wardrobe

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
The create_fit_card tool will, given an outfit, generate a short casual, social-media-esque description of a complete outfit suggestion.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit_suggestion` (str): a suggested outfit
- `selected_item` (str): the new item that was added to the user's wardrobe

**What it returns:**
<!-- Describe the return value -->
- a social-media-shareable description of an outfit

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
- if an outfit cannot be described then returned "no fit "+[insert day of the week]

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

- The tool search_listings will be used to return an array of items relevant to the user's query from listings.
- If search_listings returns an empty array or if it encounters an error, then an error message will be delivered to the user, and, if possible, recommend a way for the user to update their query for better searching. There will be no more tools called.
- If search_listings returns a popluated array, the first item, the most relevant item, will be added to Session as selected_item.
- The selected_item stored in Session will be used with the suggest_outfit tool along with the user's wardrobe.
- If suggest_outfit encounters an error or cannot perform successfully, then an error message will be delivered to the user that an outfit cannot be suggested. No more tools will be called.
- If  suggest_outfit is sucessfully able to return the description of a suggested outfit, that description will be stored in Session as outfit_suggestion.
- The outfit_suggestion stored in Session will be used by the tool create_fit_card along with the selected_item, also stored in Session.
- If the create_fit_card tool encounters an error or cannot perform successfully, then an error message will be returned to the user in the format: "no fit "+[day of the week].
- If the create_fit_card is able to sucessfully generate a social-media-style message describing outfit_suggestion, this description will be returned by this tool.



---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

- Session will be used to store state and update the user's wardrobe through the lifecycle of the application
- Session will be used to store the selected_item from the items returned from the tool search_listings
- Session will be used to store the outfit_suggestion generated from the tool suggest_outfit

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | an error message and a recommend to improve the user's query |
| suggest_outfit | Wardrobe is empty |  an error message that an outfit cannot be suggested |
| create_fit_card | Outfit input is missing or incomplete | an error message in the format: "no fit "+[day of the week] |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

                                        user query
                                             │
                                             ▼
                                        Planning Loop
                                             │
                                             ▼
                                   /─────────────────\
                                   < runs successfully >
                                   \─────────────────/
                                   /               \
                                   /                 \ No ──► Error ~= "Unable to process request"
                                   /                        │
                                   ▼ Yes                    │   
                         Session: user_query                │
                                   │                        │
                                   ▼                        │
                         search_listings(                   │
                         description, size, max_price)      │
                                   │                        │
                                   ▼                        │
                         /───────────────\                  │
                         <runs successfully>                │
                         \───────────────/                  │
                              /           \                 │
                         / no          \ yes                │
                         ▼               ▼                  │
                         results=[]   results=[item,...]    │
                         Error ~=     Session:              │
                         "No items"   selected_item =       │
                         │          results[0]              │
                         │                │                 │
                         │                ▼                 │
                         │          suggest_outfit(         │
                         │            selected_item,        │
                         │            wardrobe)             │
                         │                │                 │
                         │                ▼                 │
                         │         /───────────────\        │
                         │        <runs successfully>       │
                         │         \───────────────/        │
                         │           /           \          │
                         │          / no          \ yes     │
                         │         ▼               ▼        │
                         │      Error ~=    Session:        │
                         │  "No suggestions" outfit_        │
                         │                  suggestion      │
                         │                  = "..."         │
                         │                     │            │
                         │                     ▼            │
                         │               create_fit_        │
                         │               card(outfit_       │
                         │               suggestion,        │
                         │               selected_item)     │
                         │                     │            │
                         │                     ▼            │
                         │              /─────────────\     │
                         │             <runs succesful>     │
                         │              \─────────────/     │
                         │                /         \       │
                         │               / no        \      │
                         │              ▼             ▼     │
                         │      Error ~= "No fit"    yes    │
                         │              │             │     │
                         ▼              ▼             ▼     ▼
                         ┌────────────────────────┐   Session: fit_card = "..."
                         │ print the appropriate  │       │
                         │     error message      │       ▼
                         └────────────────────────┘    ┌────────────────────────┐
                                                       │     return session     │
                                                       └────────────────────────┘

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

- Implementing search_listings:
     - Given the tool's specifications, Gemini will implement the search_listings function to filter out from the dataset based on the price, size, and an overlap of keywords from the description to rank selected items for relevance. An empty list will be returned if there are no matching items.
- Implementing suggest_outfit:
     - Given the tool's specifications, Gemini will implement the suggest_outfit tool to interact with the LLM, generating a suggested outfit using the suggested item and the user's wardrobe. Gemini will implement the parsing logic to return the generated suggestion or fail gracefully with the appropriate error.
- Implementing create_fit_card:
     - Given the tool's specifications, Gemini will implement the create_fit_card tool such that it will interact with the LLM to generate a social-media-like post or fail gracefully with the pre-configured error message.
- Testing:
     - Given the tools that need to be tested, Gemini will assist with padding out the necessary pytest unit tests for expected outputs and to catch edge cases.
- Running the Agent and Handling UI:
     - Using the notes and architecture defined in planning.md along with method specifications, Gemini will be used to generate the bodies of the run_agent and handle_query methods.

**Milestone 4 — Planning loop and state management:**

Planning Loop
- The tool search_listings will be used to return an array of items relevant to the user's query from listings.
- If search_listings returns an empty array or if it encounters an error, then an error message will be delivered to the user, and, if possible, recommend a way for the user to update their query for better searching. There will be no more tools called.
- If search_listings returns a popluated array, the first item, the most relevant item, will be added to Session as selected_item.
- The selected_item stored in Session will be used with the suggest_outfit tool along with the user's wardrobe.
- If suggest_outfit encounters an error or cannot perform successfully, then an error message will be delivered to the user that an outfit cannot be suggested. No more tools will be called.
- If  suggest_outfit is sucessfully able to return the description of a suggested outfit, that description will be stored in Session as outfit_suggestion.
- The outfit_suggestion stored in Session will be used by the tool create_fit_card along with the selected_item, also stored in Session.
- If the create_fit_card tool encounters an error or cannot perform successfully, then an error message will be returned to the user in the format: "no fit "+[day of the week].
- If the create_fit_card is able to sucessfully generate a social-media-style message describing outfit_suggestion, this description will be returned by this tool.

State Management
- Session will be used to store state and update the user's wardrobe through the lifecycle of the application
- Session will be used to store the selected_item from the items returned from the tool search_listings
- Session will be used to store the outfit_suggestion generated from the tool suggest_outfit

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent will use the search_listings tool with the description, size, max_price to return a list of matching results to the user's query, sorted by relevance.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
The first item from the returned items list will be used as the selected item, stored in session.
The suggest_outfit tool will used the selected_item as well as the user's warddrobe to generate a description, stored in session.

**Step 3:**
<!-- Continue until the full interaction is complete -->
The create_fit_card will use the suggestion with the selected_item to generate a social media post.

**Final output to user:**
<!-- What does the user actually see at the end? -->
The end user will see the generated post.
