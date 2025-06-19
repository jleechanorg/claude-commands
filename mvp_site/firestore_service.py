import datetime
from firebase_admin import firestore
from decorators import log_exceptions # Assuming log_exceptions is correctly imported

MAX_TEXT_BYTES = 1000000 # This constant seems to be defined here

def get_db():
    """Returns the Firestore client instance.

    This function provides a way to access the initialized Firestore client.
    It assumes firebase_admin has been initialized elsewhere.

    Returns:
        google.cloud.firestore_v1.client.Client: The Firestore client instance.
    """
    return firestore.client()

@log_exceptions
def get_campaigns_for_user(user_id):
    """Retrieves all campaigns for a given user, ordered by most recently played.

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        list: A list of campaign data dictionaries. Each dictionary includes
              campaign details like 'id', 'title', 'created_at' (ISO format),
              and 'last_played' (ISO format). Returns an empty list if no
              campaigns are found or in case of an error (logged by decorator).
    """
    db = get_db()
    campaigns_ref = db.collection('users').document(user_id).collection('campaigns')
    campaigns_query = campaigns_ref.order_by('last_played', direction=firestore.Query.DESCENDING)
    
    campaign_list = []
    for campaign in campaigns_query.stream():
        campaign_data = campaign.to_dict()
        campaign_data['id'] = campaign.id
        # Ensure created_at and last_played are datetime objects before isoformat()
        if isinstance(campaign_data.get('created_at'), datetime.datetime):
            campaign_data['created_at'] = campaign_data['created_at'].isoformat()
        if isinstance(campaign_data.get('last_played'), datetime.datetime):
            campaign_data['last_played'] = campaign_data['last_played'].isoformat()
        campaign_list.append(campaign_data)
    
    return campaign_list

@log_exceptions
def get_campaign_by_id(user_id, campaign_id):
    """Retrieves a single campaign and its full story context for a given user.

    The story entries are fetched and sorted by timestamp and then by part number
    to ensure correct order, especially for chunked text entries.

    Args:
        user_id (str): The unique identifier for the user.
        campaign_id (str): The unique identifier for the campaign.

    Returns:
        tuple: A tuple containing (campaign_data, story_entries).
               'campaign_data' (dict or None): The campaign document data, or None if not found.
               'story_entries' (list or None): A list of story entry dictionaries sorted
                                               by timestamp and part, or None if campaign not found.
                                               Timestamps are converted to ISO format.
    """
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    
    campaign_doc = campaign_ref.get()
    if not campaign_doc.exists:
        return None, None

    story_ref = campaign_ref.collection('story').order_by('timestamp') # Primary sort by timestamp
    story_docs = story_ref.stream()

    all_story_entries = [doc.to_dict() for doc in story_docs]

    # Secondary sort by 'part' number in Python
    all_story_entries.sort(key=lambda x: (x['timestamp'], x.get('part', 1)))

    for entry in all_story_entries:
        if isinstance(entry.get('timestamp'), datetime.datetime):
            entry['timestamp'] = entry['timestamp'].isoformat()

    return campaign_doc.to_dict(), all_story_entries


@log_exceptions
def add_story_entry(user_id, campaign_id, actor, text, mode=None):
    """Adds a new entry (or chunked entries) to a campaign's story.

    If the text exceeds MAX_TEXT_BYTES, it is split into chunks and stored
    as multiple documents with the same timestamp but incrementing part numbers.
    Updates the 'last_played' timestamp of the campaign.

    Args:
        user_id (str): The unique identifier for the user.
        campaign_id (str): The unique identifier for the campaign.
        actor (str): The actor performing the action (e.g., 'user', 'gemini').
        text (str): The text content of the story entry.
        mode (str, optional): The interaction mode (e.g., 'character', 'god') if the
                              actor is 'user'. Defaults to None.

    Returns:
        None: This function does not return a value but modifies the database.
    """
    db = get_db()
    story_ref_doc = db.collection('users').document(user_id).collection('campaigns').document(campaign_id) # Corrected to document reference for update
    story_collection_ref = story_ref_doc.collection('story') # Collection reference for adding new docs

    text_bytes = text.encode('utf-8')
    chunks = [text_bytes[i:i + MAX_TEXT_BYTES] for i in range(0, len(text_bytes), MAX_TEXT_BYTES)]
    
    base_entry_data = {'actor': actor}
    if mode: 
        base_entry_data['mode'] = mode
    
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    
    for i, chunk in enumerate(chunks):
        entry_data = base_entry_data.copy()
        entry_data['text'] = chunk.decode('utf-8')
        entry_data['timestamp'] = timestamp
        entry_data['part'] = i + 1
        story_collection_ref.add(entry_data) # Add to the 'story' collection
    
    story_ref_doc.update({'last_played': timestamp}) # Update the parent campaign document

@log_exceptions
def create_campaign(user_id, title, initial_prompt, opening_story, selected_prompts=None):
    """Creates a new campaign for a user in Firestore.

    Initializes the campaign with a title, initial prompt, creation/last played
    timestamps, selected system prompts, and the initial opening story entry.

    Args:
        user_id (str): The unique identifier for the user.
        title (str): The title of the new campaign.
        initial_prompt (str): The user's initial prompt for the campaign.
        opening_story (str): The initial story content generated by Gemini.
        selected_prompts (list, optional): A list of strings indicating which system
                                           prompts were selected for this campaign.
                                           Defaults to an empty list if None.

    Returns:
        str: The ID of the newly created campaign document.
    """
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document() # Auto-generate ID
    
    campaign_data = {
        'title': title,
        'initial_prompt': initial_prompt,
        'created_at': datetime.datetime.now(datetime.timezone.utc),
        'last_played': datetime.datetime.now(datetime.timezone.utc),
        'selected_prompts': selected_prompts if selected_prompts is not None else [] # Ensure it's a list
    }
    campaign_ref.set(campaign_data)
    
    # Add the opening story as the first entry in the 'story' subcollection
    add_story_entry(user_id, campaign_ref.id, 'gemini', opening_story)
    
    return campaign_ref.id

@log_exceptions
def update_campaign_title(user_id, campaign_id, new_title):
    """Updates the title of a specific campaign for a given user.

    Args:
        user_id (str): The unique identifier for the user.
        campaign_id (str): The unique identifier for the campaign to be updated.
        new_title (str): The new title for the campaign.

    Returns:
        bool: True if the update was successful (though Firestore update doesn't
              return a value, success is implied if no exception is raised by decorator).
              The function itself does not have an explicit return for success.
    """
    db = get_db()
    campaign_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    campaign_ref.update({'title': new_title})
    return True # Explicitly return True on success
