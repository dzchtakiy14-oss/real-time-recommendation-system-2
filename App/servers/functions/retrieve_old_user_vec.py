import redis
import numpy as np
import torch

# ==============
# Prepare Device
# ==============
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =============
# Prepare Redis
# =============
pool = redis.ConnectionPool(host="localhost", port=6379, db=0, decode_responses=False)
r = redis.Redis(connection_pool=pool)


def retrieve_old_user_vec(key_old_vec):
    # === Retrieve Old Vector ===
    old_vec_byte = r.get(key_old_vec)
    if old_vec_byte is None:
        return None

    old_vec_np = np.frombuffer(old_vec_byte, dtype=np.float32)
    old_vec_tens = torch.tensor(old_vec_np, dtype=torch.float32, device=device)
    return old_vec_tens
