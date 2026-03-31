import torch
import pandas as pd
import numpy as np

# =======
# Device
# =======
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def extract_context_features(curr_time):
    hour = (curr_time // 3600) % 24
    hour_cos = np.cos(np.pi * 2 * hour / 24)
    hour_sin = np.sin(np.pi * 2 * hour / 24)

    day = (curr_time // 86400) % 7
    day_cos = np.cos(np.pi * 2 * day / 7)
    day_sin = np.sin(np.pi * 2 * day / 7)

    month = pd.to_datetime(curr_time, unit="s").month
    month_cos = np.cos(np.pi * 2 * month / 12)
    month_sin = np.sin(np.pi * 2 * month / 12)

    # ==== Conversion to Tensors ====
    hour_cos_tens = (
        torch.tensor(hour_cos, dtype=torch.float32, device=device)
        .unsqueeze(0)
        .unsqueeze(1)
    )
    hour_sin_tens = (
        torch.tensor(hour_sin, dtype=torch.float32, device=device)
        .unsqueeze(0)
        .unsqueeze(1)
    )
    day_cos_tens = (
        torch.tensor(day_cos, dtype=torch.float32, device=device)
        .unsqueeze(0)
        .unsqueeze(1)
    )
    day_sin_tens = (
        torch.tensor(day_sin, dtype=torch.float32, device=device)
        .unsqueeze(0)
        .unsqueeze(1)
    )
    month_cos_tens = (
        torch.tensor(month_cos, dtype=torch.float32, device=device)
        .unsqueeze(0)
        .unsqueeze(1)
    )
    month_sin_tens = (
        torch.tensor(month_sin, dtype=torch.float32, device=device)
        .unsqueeze(0)
        .unsqueeze(1)
    )

    return (
        hour_cos_tens,
        hour_sin_tens,
        day_cos_tens,
        day_sin_tens,
        month_cos_tens,
        month_sin_tens,
    )
