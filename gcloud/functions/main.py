import functions_framework
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from cloudevents.http import from_json
import numpy as np
import logging
import base64

db = firestore.Client(database='homiehubdb')

LOCATION_COORDS = {
    # Core Boston neighborhoods
    "Boston": (42.3601, -71.0589),
    "Downtown Boston": (42.3551, -71.0603),
    "Back Bay": (42.3505, -71.0763),
    "South End": (42.3414, -71.0742),
    "North End": (42.3647, -71.0542),
    "Beacon Hill": (42.3588, -71.0707),
    "Fenway": (42.3467, -71.0972),
    "South Boston": (42.3334, -71.0495),
    "East Boston": (42.3713, -71.0395),
    "Charlestown": (42.3782, -71.0602),
    "Roxbury": (42.3318, -71.0828),
    "Jamaica Plain": (42.3099, -71.1206),
    "Mission Hill": (42.3331, -71.1008),
    
    # Cambridge (nearby areas)
    "Cambridge": (42.3736, -71.1097),
    "Central Square": (42.3657, -71.1040),
    "Kendall Square": (42.3656, -71.0857),
    "Harvard Square": (42.3736, -71.1190),
    
    # Somerville (nearby areas)
    "Somerville": (42.3876, -71.0995),
    "Union Square": (42.3793, -71.0936),
    "Davis Square": (42.3967, -71.1226),
    
    # Brookline
    "Brookline": (42.3318, -71.1212),
    "Coolidge Corner": (42.3421, -71.1211),
    
    # Allston/Brighton
    "Allston": (42.3543, -71.1312),
    "Brighton": (42.3481, -71.1509),
}

## Vector weights
WEIGHTS = np.array([
    3.0,  # index 0: latitude (location - high priority)
    3.0,  # index 1: longitude (location - high priority)
    4.0,  # index 2: gender (STRICT - highest priority)
    3.0,  # index 3: budget (high priority)
    4.0,  # index 4: lease_duration (STRICT - highest priority)
    2.0,  # index 5: room_type (medium priority)
    1.0,  # index 6: bathroom (low priority)
    1.0,  # index 7: food (low priority)
    1.0,  # index 8: alcohol (low priority)
    1.0,  # index 9: smoke (low priority)
    2.0   # index 10: utilities (medium priority)
], dtype=np.float32)

GENDER_MAP = {"Male": 0.0, "Female": 1.0, "Mixed": 0.5}

FOOD_MAP = {"Vegan": 0.0, "Vegetarian": 0.5, "Everything": 1.0}

ALCOHOL_MAP = {
    "Never": 0.0,
    "Rarely": 0.25,
    "Occasionally": 0.5,
    "Regularly": 0.75,
    "Frequently": 1.0
}
SMOKE_MAP = {"No": 0.0, "Outside Only": 0.5, "Yes": 1.0}

LAT_MIN, LAT_MAX = 42.25, 42.45
LON_MIN, LON_MAX = -71.20, -71.00
BUDGET_MIN, BUDGET_MAX = 500, 3000
LEASE_MIN, LEASE_MAX = 1, 24

def vectorize_room(room_data: dict) -> np.ndarray:
    """Vectorize room preferences for similarity matching."""
    location = room_data.get('location', 'Boston')
    lat, lon = LOCATION_COORDS.get(location, (42.3601, -71.0589))
    lat_normalized = max(0.0, min(1.0, (lat - LAT_MIN) / (LAT_MAX - LAT_MIN)))
    lon_normalized = max(0.0, min(1.0, (lon - LON_MIN) / (LON_MAX - LON_MIN)))
    gender = GENDER_MAP.get(room_data.get('flatmate_gender', 'Mixed'), 0.5)
    rent = room_data.get('rent', 1500)
    rent_normalized = max(0.0, min(1.0, (rent - BUDGET_MIN) / (BUDGET_MAX - BUDGET_MIN)))
    lease_duration = room_data.get('lease_duration_months', 12)
    lease_normalized = max(0.0, min(1.0, (lease_duration - LEASE_MIN) / (LEASE_MAX - LEASE_MIN)))
    room_type_val = room_data.get('room_type', 'Shared')
    room_type = 0.0 if room_type_val == 'Shared' else (1.0 if room_type_val == 'Private' else 0.5)
    bathroom_val = room_data.get('attached_bathroom', 'No')
    bathroom = 0.0 if bathroom_val == 'No' else 1.0
    food = FOOD_MAP.get(room_data.get('lifestyle_food', 'Everything'), 1.0)
    alcohol = ALCOHOL_MAP.get(room_data.get('lifestyle_alcohol', 'Occasionally'), 0.5)
    smoke = SMOKE_MAP.get(room_data.get('lifestyle_smoke', 'No'), 0.0)
    utilities = min(1.0, len(room_data.get('utilities_included', [])) / 4.0)
    normalized_vector = np.array([
        lat_normalized, lon_normalized, gender, rent_normalized, lease_normalized,
        room_type, bathroom, food, alcohol, smoke, utilities
    ], dtype=np.float32)
    weighted_vector = normalized_vector * WEIGHTS
    if np.any(np.isnan(weighted_vector)) or np.any(np.isinf(weighted_vector)):
        raise ValueError("Invalid vector computed")
    return weighted_vector


def vectorize_user(user_data: dict) -> np.ndarray:
    """Vectorize user preferences for similarity matching."""
    preferred_locations = user_data.get('preferred_locations', ['Boston'])
    lats, lons = [], []
    for loc in preferred_locations:
        if loc in LOCATION_COORDS:
            lat, lon = LOCATION_COORDS[loc]
            lats.append(lat)
            lons.append(lon)
    if not lats:
        lats, lons = [42.3601], [-71.0589]
    avg_lat = sum(lats) / len(lats)
    avg_lon = sum(lons) / len(lons)
    lat_normalized = max(0.0, min(1.0, (avg_lat - LAT_MIN) / (LAT_MAX - LAT_MIN)))
    lon_normalized = max(0.0, min(1.0, (avg_lon - LON_MIN) / (LON_MAX - LON_MIN)))
    gender = GENDER_MAP.get(user_data.get('gender_preference', 'Any'), 0.5)
    budget = user_data.get('budget_max', 1500)
    budget_normalized = max(0.0, min(1.0, (budget - BUDGET_MIN) / (BUDGET_MAX - BUDGET_MIN)))
    lease_duration = user_data.get('lease_duration_months', 12)
    lease_normalized = max(0.0, min(1.0, (lease_duration - LEASE_MIN) / (LEASE_MAX - LEASE_MIN)))
    room_type_pref = user_data.get('room_type_preference', 'Shared')
    room_type = 0.0 if room_type_pref == 'Shared' else (1.0 if room_type_pref == 'Private' else 0.5)
    bathroom_pref = user_data.get('attached_bathroom', 'No')
    bathroom = 0.0 if bathroom_pref == 'No' else (1.0 if bathroom_pref == 'Yes' else 0.5)
    food = FOOD_MAP.get(user_data.get('lifestyle_food', 'Everything'), 1.0)
    alcohol = ALCOHOL_MAP.get(user_data.get('lifestyle_alcohol', 'Occasionally'), 0.5)
    smoke = SMOKE_MAP.get(user_data.get('lifestyle_smoke', 'No'), 0.0)
    utilities = min(1.0, len(user_data.get('utilities_preference', [])) / 4.0)
    normalized_vector = np.array([
        lat_normalized, lon_normalized, gender, budget_normalized, lease_normalized,
        room_type, bathroom, food, alcohol, smoke, utilities
    ], dtype=np.float32)
    weighted_vector = normalized_vector * WEIGHTS
    if np.any(np.isnan(weighted_vector)) or np.any(np.isinf(weighted_vector)):
        raise ValueError("Invalid vector computed")
    return weighted_vector

@functions_framework.cloud_event
def generate_room_embedding(cloud_event):
    """
    Triggered by a Firestore document write (create, update, delete).
    """
    logging.info("=== Room function triggered ===")
    
    try:
        # Get document path from the cloud event source
        # Format: projects/{project}/databases/{database}/documents/{path}
        source = cloud_event.get('source', '')
        logging.info(f"Event source: {source}")
        
        # Extract collection and document ID from resource
        subject = cloud_event.get('subject', '')
        logging.info(f"Event subject: {subject}")
        
        # The subject contains: documents/{collection}/{docId}
        if 'documents/' in subject:
            doc_path = subject.split('documents/')[-1]
            logging.info(f"Document path: {doc_path}")
            
            # Get the document directly from Firestore
            doc_ref = db.document(doc_path)
            doc_snapshot = doc_ref.get()
            
            if not doc_snapshot.exists:
                logging.info("Document doesn't exist or was deleted")
                return
            
            room_data = doc_snapshot.to_dict()
            
            # Skip if room_vector already exists (prevent infinite loop)
            if 'room_vector' in room_data:
                logging.info("room_vector already exists, skipping")
                return
            
            logging.info(f"Processing room data with keys: {list(room_data.keys())}")
            
            # Generate embedding
            logging.info("Generating embedding...")
            embedding_array = vectorize_room(room_data)
            embedding = embedding_array.tolist()
            logging.info(f"Embedding generated: dimension={len(embedding)}")
            
            # Update document with vector
            doc_ref.update({'room_vector': Vector(embedding)})
            
            logging.info(f"✅ SUCCESS: Room vector stored for {doc_path}")
        else:
            logging.error(f"Could not parse document path from subject: {subject}")
        
    except Exception as e:
        logging.error(f"❌ ERROR: {str(e)}", exc_info=True)


@functions_framework.cloud_event
def generate_user_embedding(cloud_event):
    """
    Triggered by a Firestore document write (create, update, delete).
    """
    logging.info("=== User function triggered ===")
    
    try:
        # Get document path from the cloud event
        subject = cloud_event.get('subject', '')
        logging.info(f"Event subject: {subject}")
        
        # The subject contains: documents/{collection}/{docId}
        if 'documents/' in subject:
            doc_path = subject.split('documents/')[-1]
            logging.info(f"Document path: {doc_path}")
            
            # Get the document directly from Firestore
            doc_ref = db.document(doc_path)
            doc_snapshot = doc_ref.get()
            
            if not doc_snapshot.exists:
                logging.info("Document doesn't exist or was deleted")
                return
            
            user_data = doc_snapshot.to_dict()
            
            # Skip if user_vector already exists (prevent infinite loop)
            if 'user_vector' in user_data:
                logging.info("user_vector already exists, skipping")
                return
            
            logging.info(f"Processing user data with keys: {list(user_data.keys())}")
            
            # Generate embedding
            logging.info("Generating embedding...")
            embedding_array = vectorize_user(user_data)
            embedding = embedding_array.tolist()
            logging.info(f"Embedding generated: dimension={len(embedding)}")
            
            # Update document with vector
            doc_ref.update({'user_vector': Vector(embedding)})
            
            logging.info(f"✅ SUCCESS: User vector stored for {doc_path}")
        else:
            logging.error(f"Could not parse document path from subject: {subject}")
        
    except Exception as e:
        logging.error(f"❌ ERROR: {str(e)}", exc_info=True)