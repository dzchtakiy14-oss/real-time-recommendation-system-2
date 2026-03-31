import torch
import torch.nn as nn
import torch.nn.functional as F


class TwoTowerModel(nn.Module):
    def __init__(self, num_users, num_genres, emb_dim=128):
        super().__init__()
        self.emb_dim = emb_dim

        # ==== Linear mlp ====
        self.linear_context = nn.Linear(6, emb_dim)

        # ==== Embedding dim ====
        self.emb_user = nn.Embedding(num_users, emb_dim)

        # ==== EmbeddingBag ====
        self.Embag_genres = nn.EmbeddingBag(num_genres, emb_dim, mode="sum")

        # ===== User MLP =====
        self.context_mlp = nn.Sequential(
            nn.Linear(emb_dim, emb_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(emb_dim, emb_dim),
        )

        self.user_context_mlp = nn.Sequential(
            nn.Linear(emb_dim * 2, emb_dim * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(emb_dim * 2, emb_dim),
        )

        # ==== Item MLP ====
        self.item_mlp = nn.Sequential(
            nn.Linear(emb_dim, emb_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(emb_dim, emb_dim),
        )

    def user_tower(
        self,
        hour_cos,
        hour_sin,
        day_cos,
        day_sin,
        month_cos,
        month_sin,
        user_id=None,
        history_vec=None,
        old_vec=None,
    ):
        # ==== Process Context ====
        # Context Integration
        integated_cont = torch.cat(
            [hour_cos, hour_sin, day_cos, day_sin, month_cos, month_sin], dim=1
        )
        context_emb = self.linear_context(integated_cont)

        # User Verification
        if user_id is not None:
            user_emb = self.emb_user(user_id)
            user_context_emb = torch.cat([context_emb, user_emb], dim=1)
            final_vec = self.user_context_mlp(user_context_emb)
        else:
            final_vec = self.context_mlp(context_emb)

        # ==== Weights Distribution ====
        vectors = [final_vec]
        weights = [0.4]

        if history_vec is not None:
            print("history_vec IS EXISTS")
            vectors.append(history_vec)
            weights.append(0.3)

        if old_vec is not None:
            print("old_vec IS EXISTS")
            vectors.append(old_vec)
            weights.append(0.3)

        sum_weights = sum(weights)
        final_weights = [w / sum_weights for w in weights]

        # ==== Compute Final User Vector ====
        user_vec = sum(w * v for w, v in zip(final_weights, vectors))
        final_vec = F.normalize(user_vec, p=2, dim=1)
        return final_vec

    def item_tower(self, genres, offsets):
        genre_mlp = self.Embag_genres(genres, offsets)
        genre_vec = self.item_mlp(genre_mlp)
        final_item_vec = F.normalize(genre_vec, p=2, dim=1)
        return final_item_vec

    def forward(
        self,
        genres,
        offsets,
        hour_cos,
        hour_sin,
        day_cos,
        day_sin,
        month_cos,
        month_sin,
        user_id=None,
        history_vec=None,
        old_vec=None,
    ):
        user_vec = self.user_tower(
            hour_cos,
            hour_sin,
            day_cos,
            day_sin,
            month_cos,
            month_sin,
            user_id=user_id,
            history_vec=history_vec,
            old_vec=old_vec,
        )
        item_vec = self.item_tower(genres, offsets)

        return user_vec, item_vec
