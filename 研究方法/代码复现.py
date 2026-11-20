import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torch_geometric.nn import SAGEConv
from torch_geometric.utils import degree, add_self_loops
from typing import List, Tuple, Optional
import os
import random

# ----------------------------- 辅助函数 -----------------------------
def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def build_user_item_graph(interactions, num_users, num_items):
    """构建用户-物品二分图
    interactions: list of (user_id, item_id)
    """
    edge_index = []
    for u, i in interactions:
        edge_index.append([u, num_users + i])
        edge_index.append([num_users + i, u])  # 无向图
    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    node_type = torch.cat([
        torch.zeros(num_users, dtype=torch.long),
        torch.ones(num_items, dtype=torch.long)
    ])
    return edge_index, node_type

# ----------------------------- 核心模块 -----------------------------
class AttentionSampling(nn.Module):
    def __init__(self, alpha: float = 0.5):
        super().__init__()
        self.alpha = alpha

    def compute_similarity_matrix(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        N = x.size(0)
        sim = torch.mm(x, x.t())
        adj = torch.zeros(N, N, device=x.device)
        adj[edge_index[0], edge_index[1]] = 1.0
        A_hat = adj + torch.eye(N, device=x.device)
        S = sim + self.alpha * torch.mm(A_hat, sim)
        return S

    def sample(self, x: torch.Tensor, edge_index: torch.Tensor, k: int) -> torch.Tensor:
        S = self.compute_similarity_matrix(x, edge_index)
        _, topk_indices = torch.topk(S, k=k, dim=1)
        return topk_indices  # (N, k)


class PositionalEncoding(nn.Module):
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.spe_mlp = nn.Sequential(
            nn.Linear(1, hidden_dim // 2), nn.ReLU(), nn.Linear(hidden_dim // 2, hidden_dim)
        )
        self.de_mlp = nn.Sequential(
            nn.Linear(1, hidden_dim // 2), nn.ReLU(), nn.Linear(hidden_dim // 2, hidden_dim)
        )
        self.pre_mlp = nn.Sequential(
            nn.Linear(1, hidden_dim // 2), nn.ReLU(), nn.Linear(hidden_dim // 2, hidden_dim)
        )
        self.combine_mlp = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, hidden_dim)
        )

    def forward(self, x: torch.Tensor, sp_dist: torch.Tensor, deg: torch.Tensor, pr: torch.Tensor):
        spe = self.spe_mlp(sp_dist.unsqueeze(-1))
        de = self.de_mlp(deg.unsqueeze(-1).float())
        pre = self.pre_mlp(pr.unsqueeze(-1))
        pos_enc = spe + de + pre
        combined = torch.cat([x, pos_enc], dim=-1)
        return self.combine_mlp(combined)


class MultiHeadSelfAttention(nn.Module):
    def __init__(self, hidden_dim: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        assert self.head_dim * num_heads == hidden_dim

        self.q_proj = nn.Linear(hidden_dim, hidden_dim)
        self.k_proj = nn.Linear(hidden_dim, hidden_dim)
        self.v_proj = nn.Linear(hidden_dim, hidden_dim)
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor) -> torch.Tensor:
        B = query.size(0)
        k = key.size(1)
        Q = self.q_proj(query).view(B, self.num_heads, self.head_dim)
        K = self.k_proj(key).view(B, k, self.num_heads, self.head_dim).transpose(1, 2)
        V = self.v_proj(value).view(B, k, self.num_heads, self.head_dim).transpose(1, 2)

        attn_weights = torch.matmul(Q.unsqueeze(2), K.transpose(-2, -1)) / np.sqrt(self.head_dim)
        attn_weights = F.softmax(attn_weights, dim=-1)
        attn_weights = self.dropout(attn_weights)

        out = torch.matmul(attn_weights, V)  # (B, heads, 1, head_dim)
        out = out.squeeze(2).reshape(B, self.hidden_dim)
        out = self.out_proj(out)
        return out


class TransformerLayer(nn.Module):
    def __init__(self, hidden_dim: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        self.attention = MultiHeadSelfAttention(hidden_dim, num_heads, dropout)
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.ffn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim)
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, center_emb: torch.Tensor, sample_embs: torch.Tensor) -> torch.Tensor:
        # center_emb: (B, d), sample_embs: (B, k, d)
        attn_out = self.attention(center_emb, sample_embs, sample_embs)
        center_emb = self.norm1(center_emb + self.dropout(attn_out))
        ffn_out = self.ffn(center_emb)
        center_emb = self.norm2(center_emb + self.dropout(ffn_out))
        return center_emb


class GNNLayer(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float = 0.1):
        super().__init__()
        self.conv = SAGEConv(hidden_dim, hidden_dim)
        self.norm = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        x = self.conv(x, edge_index)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.norm(x)
        return x


class SamplesUpdate(nn.Module):
    """消息传递式样本更新"""
    def __init__(self):
        super().__init__()

    def update(self, samples: torch.Tensor, edge_index: torch.Tensor,
               node_embs: torch.Tensor, k: int) -> torch.Tensor:
        N = node_embs.size(0)
        device = node_embs.device
        new_samples = []
        # 构建邻接表
        adj_list = [[] for _ in range(N)]
        for src, dst in edge_index.t().tolist():
            adj_list[src].append(dst)
        # 节点到样本集映射
        node_to_samples = {i: set(samples[i].tolist()) for i in range(N)}
        for i in range(N):
            neighbor_samples = set()
            for nb in adj_list[i]:
                neighbor_samples.update(node_to_samples.get(nb, set()))
            if len(neighbor_samples) < k:
                new_samples.append(list(node_to_samples[i])[:k])
                continue
            # 按相似度选取最相关的k个
            center_emb = node_embs[i]
            cand_list = list(neighbor_samples)
            cand_embs = node_embs[cand_list]
            sim = torch.matmul(center_emb.unsqueeze(0), cand_embs.t()).squeeze(0)
            topk_idx = torch.topk(sim, k=k).indices
            new_samples.append([cand_list[idx] for idx in topk_idx.tolist()])
        return torch.tensor(new_samples, dtype=torch.long, device=device)


class TransGNN(nn.Module):
    def __init__(self, num_users: int, num_items: int, hidden_dim: int = 64,
                 num_trans_layers: int = 3, num_gnn_layers: int = 2,
                 num_heads: int = 8, sample_size: int = 20, dropout: float = 0.1,
                 alpha: float = 0.5):
        super().__init__()
        self.num_users = num_users
        self.num_items = num_items
        self.hidden_dim = hidden_dim
        self.sample_size = sample_size

        self.user_embedding = nn.Embedding(num_users, hidden_dim)
        self.item_embedding = nn.Embedding(num_items, hidden_dim)

        self.attn_sampling = AttentionSampling(alpha)
        self.pos_encoding = PositionalEncoding(hidden_dim)

        self.trans_layers = nn.ModuleList([
            TransformerLayer(hidden_dim, num_heads, dropout) for _ in range(num_trans_layers)
        ])
        self.gnn_layers = nn.ModuleList([
            GNNLayer(hidden_dim, dropout) for _ in range(num_gnn_layers)
        ])
        self.sample_update = SamplesUpdate()

        nn.init.xavier_uniform_(self.user_embedding.weight)
        nn.init.xavier_uniform_(self.item_embedding.weight)

    def get_all_embeddings(self, node_type: torch.Tensor) -> torch.Tensor:
        N = node_type.size(0)
        device = node_type.device
        emb = torch.zeros(N, self.hidden_dim, device=device)
        user_mask = (node_type == 0)
        item_mask = (node_type == 1)
        if user_mask.any():
            emb[user_mask] = self.user_embedding(torch.arange(self.num_users, device=device))
        if item_mask.any():
            emb[item_mask] = self.item_embedding(torch.arange(self.num_items, device=device))
        return emb

    def compute_pagerank(self, edge_index: torch.Tensor, num_nodes: int,
                         damping: float = 0.85, num_iters: int = 50) -> torch.Tensor:
        N = num_nodes
        adj = torch.zeros(N, N, device=edge_index.device)
        adj[edge_index[0], edge_index[1]] = 1.0
        deg = adj.sum(dim=1, keepdim=True).clamp(min=1e-12)
        P = adj / deg
        pr = torch.ones(N, 1, device=edge_index.device) / N
        for _ in range(num_iters):
            pr = damping * torch.mm(P.t(), pr) + (1 - damping) / N
        return pr.squeeze()

    def forward(self, user_ids: torch.Tensor, item_ids: torch.Tensor,
                edge_index: torch.Tensor, node_type: torch.Tensor) -> torch.Tensor:
        N = node_type.size(0)
        device = user_ids.device

        # 初始节点嵌入
        x = self.get_all_embeddings(node_type)

        # 度、PageRank、最短路径（此处为简化，使用0作为自距离）
        deg = degree(edge_index[0], num_nodes=N)
        pr = self.compute_pagerank(edge_index, N)
        sp_dist = torch.zeros(N, device=device)  # 实际应使用最短路径距离，简化处理
        x = self.pos_encoding(x, sp_dist, deg, pr)

        # 初始采样
        samples = self.attn_sampling.sample(x, edge_index, self.sample_size)  # (N, k)

        # 交替Transformer和GNN
        for trans_layer, gnn_layer in zip(self.trans_layers, self.gnn_layers):
            # Transformer层
            new_x = x.clone()
            for i in range(N):
                s_idx = samples[i]
                sample_embs = x[s_idx].unsqueeze(0)  # (1, k, d)
                new_x[i] = trans_layer(x[i].unsqueeze(0), sample_embs).squeeze(0)
            # GNN层
            x = gnn_layer(new_x, edge_index)
            # 更新样本
            samples = self.sample_update.update(samples, edge_index, x, self.sample_size)

        # 提取用户和物品嵌入
        user_emb = x[user_ids]
        item_emb = x[self.num_users + item_ids]
        scores = (user_emb * item_emb).sum(dim=-1)
        return scores


# ----------------------------- 训练与评估 -----------------------------
class Trainer:
    def __init__(self, model: TransGNN, lr: float = 1e-3, weight_decay: float = 1e-4):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    def pairwise_loss(self, pos_scores: torch.Tensor, neg_scores: torch.Tensor) -> torch.Tensor:
        return -torch.log(torch.sigmoid(pos_scores - neg_scores)).mean()

    def train_step(self, batch_users, batch_pos_items, batch_neg_items, edge_index, node_type):
        self.model.train()
        self.optimizer.zero_grad()
        pos_scores = self.model(batch_users, batch_pos_items, edge_index, node_type)
        neg_scores = self.model(batch_users, batch_neg_items, edge_index, node_type)
        loss = self.pairwise_loss(pos_scores, neg_scores)
        loss.backward()
        self.optimizer.step()
        return loss.item()

    @torch.no_grad()
    def evaluate(self, all_users, all_items, edge_index, node_type,
                 test_interactions, k=20):
        """test_interactions: dict user -> list of positive items"""
        self.model.eval()
        device = next(self.model.parameters()).device
        N_users = len(all_users)
        N_items = len(all_items)
        recalls, ndcgs = [], []

        for u in all_users:
            u_tensor = torch.full((N_items,), u, dtype=torch.long, device=device)
            scores = self.model(u_tensor, all_items, edge_index, node_type)
            _, topk = torch.topk(scores, k=k)
            topk_items = topk.cpu().tolist()
            pos_items = test_interactions.get(u, [])
            if not pos_items:
                continue
            hits = len(set(topk_items) & set(pos_items))
            recall = hits / len(pos_items)
            recalls.append(recall)

            dcg = 0.0
            idcg = 0.0
            for i, item in enumerate(topk_items):
                if item in pos_items:
                    dcg += 1.0 / np.log2(i + 2)
            for i in range(min(len(pos_items), k)):
                idcg += 1.0 / np.log2(i + 2)
            ndcg = dcg / idcg if idcg > 0 else 0
            ndcgs.append(ndcg)

        return np.mean(recalls), np.mean(ndcgs)


# ----------------------------- 数据加载（示例：MovieLens 1M） -----------------------------
def load_movielens_1m(root='./data/ml-1m'):
    """加载MovieLens 1M数据集，返回用户-物品交互列表"""
    if not os.path.exists(root):
        os.makedirs(root, exist_ok=True)
        # 提示用户自行下载
        raise FileNotFoundError("请先下载MovieLens 1M数据集并放在指定目录。"
                                "下载链接: https://files.grouplens.org/datasets/movielens/ml-1m.zip")
    ratings_file = os.path.join(root, 'ratings.dat')
    if not os.path.isfile(ratings_file):
        raise FileNotFoundError("ratings.dat 未找到，请确认数据集完整。")
    interactions = []
    users_set = set()
    items_set = set()
    with open(ratings_file, 'r') as f:
        for line in f:
            parts = line.strip().split('::')
            u = int(parts[0]) - 1  # 转为0索引
            i = int(parts[1]) - 1
            interactions.append((u, i))
            users_set.add(u)
            items_set.add(i)
    num_users = max(users_set) + 1
    num_items = max(items_set) + 1
    return interactions, num_users, num_items


def split_interactions(interactions, train_ratio=0.8, val_ratio=0.1):
    """按用户划分训练/验证/测试，保证每个用户都有正样本"""
    from collections import defaultdict
    user_items = defaultdict(list)
    for u, i in interactions:
        user_items[u].append(i)
    train, val, test = [], [], []
    for u, items in user_items.items():
        n = len(items)
        if n < 3:
            # 样本太少，全部用于训练
            train.extend([(u, i) for i in items])
            continue
        random.shuffle(items)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        train.extend([(u, i) for i in items[:train_end]])
        val.extend([(u, i) for i in items[train_end:val_end]])
        test.extend([(u, i) for i in items[val_end:]])
    return train, val, test


# ----------------------------- 主程序 -----------------------------
def main():
    set_seed(42)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")

    # 1. 加载数据
    print("加载MovieLens 1M数据集...")
    try:
        interactions, num_users, num_items = load_movielens_1m()
    except Exception as e:
        print(e)
        print("使用模拟数据代替...")
        # 模拟一个小数据集
        num_users, num_items = 500, 200
        interactions = [(random.randint(0, num_users-1), random.randint(0, num_items-1)) for _ in range(5000)]
    print(f"用户数: {num_users}, 物品数: {num_items}, 交互数: {len(interactions)}")

    # 划分数据集
    train_inter, val_inter, test_inter = split_interactions(interactions, train_ratio=0.8, val_ratio=0.1)
    print(f"训练交互: {len(train_inter)}, 验证交互: {len(val_inter)}, 测试交互: {len(test_inter)}")

    # 构建图
    edge_index, node_type = build_user_item_graph(train_inter, num_users, num_items)
    edge_index = edge_index.to(device)
    node_type = node_type.to(device)

    # 2. 模型参数
    hidden_dim = 64
    sample_size = 20
    num_heads = 8
    num_trans_layers = 3
    num_gnn_layers = 2
    batch_size = 256
    lr = 1e-3
    weight_decay = 1e-4
    epochs = 30

    model = TransGNN(
        num_users=num_users,
        num_items=num_items,
        hidden_dim=hidden_dim,
        num_trans_layers=num_trans_layers,
        num_gnn_layers=num_gnn_layers,
        num_heads=num_heads,
        sample_size=sample_size,
        dropout=0.1,
        alpha=0.5
    ).to(device)

    trainer = Trainer(model, lr=lr, weight_decay=weight_decay)

    # 构建验证和测试交互字典
    val_dict = {}
    for u, i in val_inter:
        val_dict.setdefault(u, []).append(i)
    test_dict = {}
    for u, i in test_inter:
        test_dict.setdefault(u, []).append(i)

    # 所有用户和物品的索引
    all_users = torch.arange(num_users, device=device)
    all_items = torch.arange(num_items, device=device)

    # 训练循环
    print("开始训练...")
    for epoch in range(1, epochs+1):
        # 随机采样负样本
        indices = list(range(len(train_inter)))
        random.shuffle(indices)
        total_loss = 0.0
        num_batches = 0
        for start in range(0, len(indices), batch_size):
            batch_idx = indices[start:start+batch_size]
            batch_users = []
            batch_pos = []
            batch_neg = []
            for idx in batch_idx:
                u, pos_i = train_inter[idx]
                # 随机负采样
                while True:
                    neg_i = random.randint(0, num_items-1)
                    if (u, neg_i) not in train_inter:
                        break
                batch_users.append(u)
                batch_pos.append(pos_i)
                batch_neg.append(neg_i)
            batch_users = torch.tensor(batch_users, dtype=torch.long, device=device)
            batch_pos = torch.tensor(batch_pos, dtype=torch.long, device=device)
            batch_neg = torch.tensor(batch_neg, dtype=torch.long, device=device)

            loss = trainer.train_step(batch_users, batch_pos, batch_neg, edge_index, node_type)
            total_loss += loss
            num_batches += 1

        avg_loss = total_loss / num_batches if num_batches > 0 else 0
        if epoch % 5 == 0 or epoch == 1:
            # 验证
            recall, ndcg = trainer.evaluate(all_users, all_items, edge_index, node_type, val_dict, k=20)
            print(f"Epoch {epoch:3d} | Loss: {avg_loss:.4f} | Val Recall@20: {recall:.4f} | Val NDCG@20: {ndcg:.4f}")

    # 测试
    test_recall, test_ndcg = trainer.evaluate(all_users, all_items, edge_index, node_type, test_dict, k=20)
    print(f"\n测试结果 | Recall@20: {test_recall:.4f} | NDCG@20: {test_ndcg:.4f}")

if __name__ == "__main__":
    main()