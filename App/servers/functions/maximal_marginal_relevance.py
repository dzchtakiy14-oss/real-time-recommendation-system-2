import numpy as np

def mmr_ranker_fast(query_vec, candidate_vecs, candidate_ids, top_k=10, lambda_=0.7):
    candidate_vecs = np.asarray(candidate_vecs, dtype=np.float32)
    query_vec = np.asarray(query_vec, dtype=np.float32)

    n = len(candidate_ids)
    if n == 0:
        return []
    if n <= top_k:
        return list(candidate_ids)

    # Similarity with query
    rel = candidate_vecs @ query_vec

    selected_indices = []
    selected_mask = np.zeros(n, dtype=bool)

    # First item: most relevant
    first_idx = int(np.argmax(rel))
    selected_indices.append(first_idx)
    selected_mask[first_idx] = True

    # Max similarity to selected items for each candidate
    max_sim = candidate_vecs @ candidate_vecs[first_idx]

    for _ in range(1, top_k):
        scores = lambda_ * rel - (1 - lambda_) * max_sim
        scores[selected_mask] = -np.inf

        next_idx = int(np.argmax(scores))
        selected_indices.append(next_idx)
        selected_mask[next_idx] = True

        # Update max similarity incrementally
        sim_to_new = candidate_vecs @ candidate_vecs[next_idx]
        max_sim = np.maximum(max_sim, sim_to_new)

    return [candidate_ids[i] for i in selected_indices]