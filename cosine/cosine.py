import numpy as np

def cosine_search(query, vectors, top_k=3):
    query = np.array(query)
    vectors = np.array(vectors)
    
    # normalize
    query_norm = query / np.linalg.norm(query)
    vectors_norm = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    
    # cosine similarity
    scores = np.dot(vectors_norm, query_norm)
    
    # get top k
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    return [(int(i), float(scores[i])) for i in top_indices]


# Example
vectors = [
    [1, 0],
    [0, 1],
    [1, 1],
    [2, 2]
]

query = [1, 1]

results = cosine_search(query, vectors)

for idx, score in results:
    print(f"Vector {idx}: {score:.4f}")