import joblib
import redis
import time
from fastapi import HTTPException

# =============
# Prepare Redis
# =============
pool = redis.ConnectionPool(host="localhost", port=6379, db=0, decode_responses=True)
r = redis.Redis(connection_pool=pool)

# ========================
# Load Mapping: id and idx
# ========================
item_id_to_idx = joblib.load("Tools/movies_to_idx.pkl")
user_id_to_idx = joblib.load("Tools/user_id_to_idx.pkl")


# ==================================
# Create Saver Interactions Function
# ==================================
def element_preserver(user_id: int, item_id: int):
    # ===== Config =====
    curr_time_minute = int(time.time() / 60)

    user_idx = user_id_to_idx.get(user_id, None)
    user_idx = user_idx or user_id

    key_click = f"click_items:{curr_time_minute}"
    interaction_key = f"interaction:{user_idx}"

    try:
        item_idx = item_id_to_idx.get(item_id, None)
        if item_idx is None:
            return {"msg": "Unknown Item ID"}
        pipe = r.pipeline()

        # === Saving Common Items ===
        common_items_key = f"common_items"
        pipe.zincrby(common_items_key, 1, item_idx)
        pipe.zremrangebyrank(common_items_key, 0, -255)

        # ====== Save Interactions ======

        pipe.incr(key_click)
        pipe.expire(key_click, 2 * 3600)

        pipe.zadd(interaction_key, {item_idx: curr_time_minute})
        pipe.zremrangebyrank(interaction_key, 0, -101)

        pipe.execute()

    except Exception as e:
        key_error_saving = f"error:saver_interactions:{curr_time_minute}"

        pipe = r.pipeline()
        pipe.incr(key_error_saving)

        pipe.expire(key_error_saving, 3600 * 4)
        pipe.execute()

        raise HTTPException(status_code=500, detail=f"Failed to Save Interactions: {e}")
