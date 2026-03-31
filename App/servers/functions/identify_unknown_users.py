import joblib
import torch

# ==============
# Prepare Device
# ==============
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ==================
# Load Users Mapping
# ==================
user_id_to_idx = joblib.load(r"Tools/user_id_to_idx.pkl")


def identifying_users(user_id):
    user_idx = user_id_to_idx.get(user_id, None)
    user_key = user_idx if user_idx is not None else f"{user_id}-not-saved"
    user_idx_to_model = (
        torch.tensor(user_idx, dtype=torch.long, device=device).unsqueeze(0)
        if user_idx is not None
        else None
    )
    return user_key, user_idx_to_model
