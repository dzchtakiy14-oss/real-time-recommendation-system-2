import joblib
import redis
import random
from fastapi import HTTPException

# =============
# Prepare Redis
# =============
pool = redis.ConnectionPool(host="localhost", port=6379, db=0, decode_responses=False)
r = redis.Redis(connection_pool=pool)

# ========================
# Load Mapping: id and idx
# ========================
item_idx_to_id = joblib.load("Tools/movies_to_idx.pkl")
item_to_vec = joblib.load("Tools/item_vec_mapping.pkl")
titles_mapping = joblib.load("Tools/title_to_idx.pkl")

# Load Popular Items
popular_items = [int(i) for i in joblib.load("Tools/popular_items.pkl")]

# =======================
# Retrieve Common Items
# =======================
def retrieve_common_items(user_idx, k: int):
    try:
        # === Config ===
        key = "common_items"
        key_watched_items = f"saver_interaction:{user_idx}:watched_items"
        print("Common Items Recalled")

        # === Retrieve Common Items === 
        common_items = r.zrevrange(key, 0, 250, withscores=False)

        # === Providing Recommendations ===
        common_items_1 = []
        if common_items:
            common_items_1 = [int(i) for i in common_items]

        # === Retrieve Interacted and watched Items ===
        key_interacted_items = f"item:{user_idx}:interacted_items"
        key_watched_items = f"watched_items:{user_idx}"


        pipe = r.pipeline()

        pipe.lrange(key_interacted_items, 0, -1)
        pipe.lrange(key_watched_items, 0, -1)

        interacted_items, watched_items = pipe.execute()

        # === Filter Common Items ===
        interacted_items_int = []
        if interacted_items:
            interacted_items_int = [int(i) for i in interacted_items ]
        
        if watched_items:
            interacted_items_int = [int(i) for i in watched_items] + interacted_items_int

        interacted_items_int = set(interacted_items_int)
        
        common_items = []
        for common_item in common_items_1:
            if common_item not in interacted_items_int:
                common_items.append(common_item)
                if len(common_items) == k:
                    break

        if len(common_items) < k:
            missing_num = k - len(common_items)
            filtered_items = list(set(popular_items) - interacted_items_int - set(common_items))
            if len(filtered_items) >= missing_num:
                common_items.extend(popular_items[:missing_num])
            else:
                common_items.extend(filtered_items)

        if len(common_items) < k:
            missing_num = k - len(common_items)
            all_items = set(item_idx_to_id.keys()) 
            filtered_items = list(all_items - interacted_items_int - set(common_items))
            if len(filtered_items) >= missing_num:
                common_items.extend(random.sample(filtered_items, k=missing_num))
            else:
                common_items.extend(filtered_items)

        # === Save Recommended Items ===
        pipe = r.pipeline()
        pipe.lpush(key_watched_items, *common_items)
        pipe.execute()

        recommendations = [
            {"item_id": item_idx_to_id.get(r, -1), "title": titles_mapping.get(r, "Untitled")}
            for r in common_items
        ]

        return recommendations
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to Provide Common Items: {e}")