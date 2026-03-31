import joblib
import time
import torch
import redis
import numpy as np


# =======
# Device
# =======
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =============
# Prepare Redis
# =============
pool = redis.ConnectionPool(host="localhost", port=6379, db=0, decode_responses=True)
r = redis.Redis(connection_pool=pool)

# =======================
# Load Mapping Items Vecs
# =======================
items_to_vec = joblib.load("Tools/item_vec_mapping.pkl")
genres = joblib.load("Tools/genres_to_idx.pkl")


# ====================================
# Prepare Interacted Items Merger
# ====================================
def item_vector_integrator(
    user_idx: int, last_interacted_items_num: int = 6, decay_rate: float = 0.1
):
    # ===== Extract Interacted Items =====
    interaction_key = f"interaction:{user_idx}"
    redis_item_idx = []
    redis_timestamps = []

    # ====== Prepare Vectors ======
    redis_items_interacted = r.zrevrange(interaction_key, 0, 9, withscores = True)
    if not redis_items_interacted:
        return None
    # ======= Retrieve Items Vectors =======
    for item_idx, timestamp in redis_items_interacted:
        redis_item_idx.append(int(item_idx))
        redis_timestamps.append(int(timestamp))

    vectors = [items_to_vec[int(i)] for i in redis_item_idx]

    # === Convert List Vectors to Tensors ===
    tensor_vectors = torch.tensor(vectors, dtype=torch.float32, device=device)

    # ====== Prepare Vectors Weights ======
    click_times = [
        int(t) for t in redis_timestamps
    ]

    # === Calculate Weights ===
    curr_hour = time.time() // 60
    weights = []
    for t in click_times:
            age = curr_hour - t
            weight = np.exp(-decay_rate * age)
            weights.append(weight)

    # === Convert List Weights to Tensors ===
    tensor_weights = torch.tensor(weights, dtype=torch.float32, device=device)

    # ====== Multiplying the Two matrices ======
    weighted_vecs = tensor_vectors * tensor_weights.unsqueeze(1)

    items_vec_tens = torch.sum(weighted_vecs, dim=0).to(device)
    return items_vec_tens

