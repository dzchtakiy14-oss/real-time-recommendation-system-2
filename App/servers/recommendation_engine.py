import time
import joblib

import faiss
import torch
import redis
import numpy as np
import pandas as pd
from fastapi import HTTPException

from model.model_project import TwoTowerModel
from App.servers.functions.item_aggregator import item_vector_integrator
from App.servers.functions.maximal_marginal_relevance import mmr_ranker_fast
from App.servers.functions.retrieve_old_user_vec import retrieve_old_user_vec
from App.servers.functions.context_features import extract_context_features
from App.servers.functions.identify_unknown_users import identifying_users
from App.servers.functions.cold_start import retrieve_common_items


# =======
# Device
# =======
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =============
# Prepare Redis
# =============
pool = redis.ConnectionPool(host="localhost", port=6379, db=0, decode_responses=False)
r = redis.Redis(connection_pool=pool)

# ========================
# Load Mapping: id and idx
# ========================
item_idx_to_id = joblib.load("Tools/item_idx_to_id.pkl")
item_to_vec = joblib.load("Tools/item_vec_mapping.pkl")

# ===================================
# Load Faiss Index and Titles Mapping
# ===================================
index = faiss.read_index(r"Tools/faiss_index.bin")
titles_mapping = joblib.load(r"Tools/title_to_idx.pkl")

# =============
# Prepare Model
# =============
model_config = joblib.load("model/weights/model_config.pt")
model = TwoTowerModel(model_config["num_users"], model_config["num_genres"])
model.load_state_dict(
    torch.load("model/weights/model_state_dict.pt", map_location=device)
)
model.eval()


# =========================
# Update-User-Vec Function
# =========================
def update_user_vec(user_id: int, k: int = 10):
    try:
        curr_time = int(time.time() / 60)
        pipe = r.pipeline()

        # ====== Extract Old User Vector ======
        # === Encoding user_id ===
        user_key, user_idx_to_model = identifying_users(user_id)

        # === Retrieve Old User Vec ===
        key_old_vec = f"user:{user_key}:old_user_vec"
        user_vec = retrieve_old_user_vec(key_old_vec)
 
        if user_vec is None:
            # ====== Create Interacted Items Vec ======
            item_vec = item_vector_integrator(user_key)
            if item_vec is None:
                recommendations = retrieve_common_items(user_key, k)
                return recommendations

            # ======= Extract Context Features ======
            (
                    hour_cos_tens,
                    hour_sin_tens,
                    day_cos_tens,
                    day_sin_tens,
                    month_cos_tens,
                    month_sin_tens,
            ) = extract_context_features(curr_time)

            # ===== Update User Vector =====
            with torch.no_grad():
                print(f"item_vec: {item_vec}")
                user_vec = (
                    model.user_tower(
                        hour_cos_tens,
                        hour_sin_tens,
                        day_cos_tens,
                        day_sin_tens,
                        month_cos_tens,
                        month_sin_tens,
                        history_vec=item_vec,
                        old_vec=user_vec,
                        user_id=user_idx_to_model,
                    )
                     .cpu()
                     .numpy()
                )
                print(f"user_vec: {user_vec}")
        
            # ===== Save User Vector =====
            pipe.set(key_old_vec, user_vec.tobytes())
            pipe.expire(key_old_vec, 10)

        # ====== Extract Interacted Items ======
        key_it = f"item:{user_key}:interacted_items"
        interacted_items = [int(x) for x in r.lrange(key_it, 0, -1)]

        # === Extract Old Recommended Items ===
        key_items_watched = f"watched_items:{user_key}"
        old_recommended_items = [int(i) for i in r.lrange(key_items_watched, 0, -1)]

        exposed_items = set([*interacted_items, *old_recommended_items])

        # ====== Search ======
        if user_vec.ndim == 1:
            user_vec = np.array([user_vec])
        score, indices = index.search(user_vec, k * 6)

        # ====== Config ======
        candidate_ids = [i for i in indices[0] if i not in exposed_items]
        candidate_vecs = [item_to_vec[i] for i in candidate_ids]
        print(f"candidate_vecs:{candidate_vecs}")

        # ==== Compute Closest Items ====
        recommendatios_indices = mmr_ranker_fast(
            user_vec[0], candidate_vecs, candidate_ids, k
        )
        print("recommendatios_indices")

        # ===== Saving impressions =====
        key_imp = f"impressions:{int(time.time() / 60)}"
        pipe.incrby(key_imp, len(recommendatios_indices))
        pipe.expire(key_imp, 2 * 3600)


        # ====== Setting Titles ======
        recommendations = [
            {"item_id": item_idx_to_id[int(r)], "title": titles_mapping[int(r)]}
            for r in recommendatios_indices
        ]

        # === Saving Watched Items ===
        pipe.lpush(key_items_watched, *recommendatios_indices)
        pipe.ltrim(key_items_watched, 0, 40)

        pipe.execute()

        return recommendations

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to Provide Recommendations: {e}")