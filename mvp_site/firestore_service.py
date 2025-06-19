from firebase_admin import firestore
from decorators import log_exceptions

# Maximum size for a single text field in Firestore (in bytes).
# Firestore documents have a 1 MiB limit, this is a safe chunk size for text.
MAX_TEXT_BYTES = 1000000

def get_db():
    """Returns the Firestore client."""
    """
    Returns an instance of the Firestore client.

    Returns:
        firestore.Client: The Firestore client.
    """
    return firestore.client()

@log_exceptions
def get_campaigns_for_user(user_id):
    """Retrieves all campaigns for a given user, ordered by most recently played."""
    """
    Retrieves all campaigns for a given user, ordered by the 'last_played' timestamp
    in descending order (most recent first).

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        list: A list of campaign dictionaries, each including 'id', 'created_at' (ISO format),
              and 'last_played' (ISO format). Returns an empty list if no campaigns are found.
    """
    db = get_db()
    campaigns_ref = db.collection('users').document(user_id).collection('campaigns')
    campaigns_query = campaigns_ref.order_by('last_played', direction=firestore.Query.DESCENDING)
    for campaign in campaigns_query.stream():
        campaign_data = campaign.to_dict()
        campaign_data['id'] = campaign.id
        # Convert datetime objects to ISO format strings for JSON serialization.
        campaign_data['created_at'] = campaign_data['created_at'].isoformat()
        campaign_data['last_played'] = campaign_data['last_played'].isoformat()
        campaign_list.append(campaign_data)
@log_exceptions
def get_campaign_by_id(user_id, campaign_id):
    """
    Retrieves a single campaign and its full story using a robust, single query
    and in-memory sort to handle all data types.
    Retrieves a single campaign document and its associated story entries for a given user.

    The story entries are fetched and then sorted in memory by their 'timestamp'
    and then by 'part' number to ensure correct order, especially for chunked entries.

    Args:
        user_id (str): The unique identifier for the user.
        campaign_id (str): The unique identifier for the campaign.

    Returns:
        tuple: A tuple containing:
            - campaign_doc (dict): The campaign document data, or None if not found.
            - story_entries (list): A list of story entry dictionaries, sorted chronologically
                                    and by part number. Timestamps are in ISO format.
                                    Returns None if the campaign is not found.
    """
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    if not campaign_doc.exists:
        return None, None

    # --- SIMPLIFIED FETCH LOGIC ---
    # 1. Fetch ALL documents, ordered only by the field that always exists: timestamp.
    # Fetch all story documents, ordered by timestamp (which always exists).
    story_ref = campaign_ref.collection('story').order_by('timestamp')
    story_docs = story_ref.stream()

    # 2. Convert to a list of dictionaries
    # Convert Firestore documents to a list of dictionaries.
    all_story_entries = [doc.to_dict() for doc in story_docs]

    # 3. Sort the list in Python, which is more powerful than a Firestore query.
    # We sort by timestamp first, and then by the 'part' number.
    # Sort the list in Python. This allows for more complex sorting logic
    # than Firestore queries alone, e.g., sorting by timestamp then by 'part'.
    # If 'part' is missing (for old docs), we treat it as 1.
    all_story_entries.sort(key=lambda x: (x['timestamp'], x.get('part', 1)))


@log_exceptions
def add_story_entry(user_id, campaign_id, actor, text, mode=None):
    """
    Adds a new entry (or multiple chunked entries) to the story subcollection of a campaign.
    If the text exceeds MAX_TEXT_BYTES, it's split into multiple documents ('parts').
    Updates the 'last_played' timestamp of the parent campaign.

    Args:
        user_id (str): The unique identifier for the user.
        campaign_id (str): The unique identifier for the campaign.
        actor (str): The source of the story entry (e.g., 'user', 'gemini').
        text (str): The content of the story entry.
        mode (str, optional): The mode of interaction if the actor is 'user' (e.g., 'character', 'god').
                              Defaults to None.
    """
    db = get_db()
    story_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)

    # Encode text to bytes to accurately measure size for chunking.
    text_bytes = text.encode('utf-8')
    chunks = [text_bytes[i:i + MAX_TEXT_BYTES] for i in range(0, len(text_bytes), MAX_TEXT_BYTES)]

    base_entry_data = {'actor': actor}
    if mode: base_entry_data['mode'] = mode

    timestamp = datetime.datetime.now(datetime.timezone.utc)

    # Iterate through chunks and add each as a separate document if text is too large.
    for i, chunk in enumerate(chunks):
        entry_data = base_entry_data.copy()
        entry_data['text'] = chunk.decode('utf-8')
        entry_data['text'] = chunk.decode('utf-8') # Decode back to string for Firestore.
        entry_data['timestamp'] = timestamp
        entry_data['part'] = i + 1
        entry_data['part'] = i + 1 # Part number for reassembling chunked text.
        story_ref.collection('story').add(entry_data)

    # Update the last_played timestamp on the parent campaign document.
    story_ref.update({'last_played': timestamp})

@log_exceptions
def create_campaign(user_id, title, initial_prompt, opening_story, selected_prompts=None):
    """
    Creates a new campaign document for a user and adds the initial story entry.

    Args:
        user_id (str): The unique identifier for the user.
        title (str): The title of the campaign.
        initial_prompt (str): The initial prompt used to generate the opening story.
        opening_story (str): The first story entry generated by the AI.
        selected_prompts (list, optional): A list of system prompt types selected by the user
                                          (e.g., ['narrative', 'mechanics']). Defaults to an empty list.

    Returns:
        str: The ID of the newly created campaign document.
    """
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document()
    campaign_data = {
        'selected_prompts': selected_prompts or []
    }
    campaign_ref.set(campaign_data)

    # Add the opening story as the first entry in the story subcollection.
    add_story_entry(user_id, campaign_ref.id, 'gemini', opening_story)
    return campaign_ref.id

# --- NEWLY ADDED FUNCTION ---
@log_exceptions
def update_campaign_title(user_id, campaign_id, new_title):
    """Updates the title of a specific campaign."""
    """
    Updates the title of a specific campaign for a given user.

    Args:
        user_id (str): The unique identifier for the user.
        campaign_id (str): The unique identifier for the campaign to be updated.
        new_title (str): The new title for the campaign.

    Returns:
        bool: True if the update was successful (note: Firestore's update doesn't
              return a status, so this assumes success if no exception is raised).
    """
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    campaign_ref.update({'title': new_title})
    return True
