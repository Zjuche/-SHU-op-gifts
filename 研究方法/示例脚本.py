import torch
import numpy as np
from transgnn import TransGNN, TransGNNTrainer

# ========== 数据生成 ==========
num_users = 1000
num_items = 500
num_interactions = 5000
batch_size = 32
num_epochs = 5

# 随机交互
interactions = [(np.random.randint(0, num_users), np.random.randint(0, num_items)) for _ in range(num_interactions)]
src = [u for u, _ in interactions]
dst = [i + num_users for _, i in interactions]
edge_index = torch.tensor([src, dst], dtype=torch.long)
node_type = torch.cat([
    torch.zeros(num_users, dtype=torch.long),
    torch.ones(num_items, dtype=torch.long)
])

# ========== 模型 ==========
model = TransGNN(
    num_users=num_users,
    num_items=num_items,
    hidden_dim=64,
    num_trans_layers=3,
    num_gnn_layers=2,
    num_heads=8,
    sample_size=20,
    dropout=0.1
)

trainer = TransGNNTrainer(model, lr=1e-3)

# ========== 训练 ==========
for epoch in range(num_epochs):
    batch_users = torch.randint(0, num_users, (batch_size,))
    pos_items = torch.randint(0, num_items, (batch_size,))
    neg_items = torch.randint(0, num_items, (batch_size,))
    loss = trainer.train_step(batch_users, pos_items, neg_items, edge_index, node_type)
    print(f"Epoch {epoch+1}, loss: {loss:.4f}")

# ========== 评估 ==========
test_users = torch.arange(10)
all_items = torch.arange(num_items)
# 模拟每个用户有5个正样本
test_interactions = torch.randint(0, num_items, (len(test_users), 5))
recall, ndcg = trainer.evaluate(test_users, all_items, edge_index, node_type, test_interactions, k=20)
print(f"Recall@20: {recall:.4f}, NDCG@20: {ndcg:.4f}")