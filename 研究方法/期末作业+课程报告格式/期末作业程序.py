"""
经典图神经网络模型对比——节点分类任务
模型：MLP、GCN、GAT
数据集：Cora 论文引用网络
Python 3.13 + PyTorch + PyTorch Geometric
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.datasets import Planetoid
from torch_geometric.transforms import NormalizeFeatures
from torch_geometric.nn import GCNConv, GATConv
import numpy as np

# ========== 修改1：设置非交互后端，避免 Tkinter 错误 ==========
import matplotlib

matplotlib.use('Agg')  # 不显示窗口，直接保存图片

# ========== 修改2：导入 pyplot 并设置中文字体 ==========
import matplotlib.pyplot as plt

# 设置中文字体（Windows 系统一般自带 SimHei/黑体）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

from collections import defaultdict


# ==================== 1. 加载数据集 ====================
def load_data(dataset_name='Cora'):
    """
    加载 Planetoid 数据集（Cora 或 CiteSeer）
    使用 NormalizeFeatures 对节点特征进行归一化
    """
    dataset = Planetoid(
        root='./data',
        name=dataset_name,
        transform=NormalizeFeatures()
    )
    data = dataset[0]  # 获取第一个（也是唯一的）图对象
    return data, dataset


# ==================== 2. 定义模型 ====================
class MLP(nn.Module):
    """
    多层感知机 (MLP)
    仅使用节点自身的特征向量，忽略图结构
    """

    def __init__(self, in_channels, hidden_channels, out_channels, dropout=0.5):
        super(MLP, self).__init__()
        self.fc1 = nn.Linear(in_channels, hidden_channels)
        self.fc2 = nn.Linear(hidden_channels, out_channels)
        self.dropout = dropout

    def forward(self, x, edge_index=None):
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)


class GCN(nn.Module):
    """
    图卷积网络 (GCN)
    使用 GCNConv 层聚合邻居节点信息
    """

    def __init__(self, in_channels, hidden_channels, out_channels, dropout=0.5):
        super(GCN, self).__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)
        self.dropout = dropout

    def forward(self, x, edge_index):
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        return F.log_softmax(x, dim=1)


class GAT(nn.Module):
    """
    图注意力网络 (GAT)
    使用 GATConv 层，带注意力机制聚合邻居信息
    """

    def __init__(self, in_channels, hidden_channels, out_channels,
                 heads=8, dropout=0.5):
        super(GAT, self).__init__()
        # 第一层：8个注意力头，输出维度 hidden_channels
        self.conv1 = GATConv(
            in_channels, hidden_channels, heads=heads, dropout=dropout
        )
        # 第二层：1个注意力头，输出维度 out_channels
        self.conv2 = GATConv(
            hidden_channels * heads, out_channels, heads=1,
            concat=False, dropout=dropout
        )
        self.dropout = dropout

    def forward(self, x, edge_index):
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = F.elu(self.conv1(x, edge_index))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        return F.log_softmax(x, dim=1)


# ==================== 3. 训练与评估函数 ====================
def train(model, data, optimizer, criterion):
    """单轮训练"""
    model.train()
    optimizer.zero_grad()

    # 前向传播
    if isinstance(model, MLP):
        out = model(data.x, None)
    else:
        out = model(data.x, data.edge_index)

    # 仅使用训练节点计算损失
    loss = criterion(out[data.train_mask], data.y[data.train_mask])
    loss.backward()
    optimizer.step()

    return loss.item()


def evaluate(model, data, mask):
    """评估模型在指定掩码上的准确率"""
    model.eval()
    with torch.no_grad():
        if isinstance(model, MLP):
            out = model(data.x, None)
        else:
            out = model(data.x, data.edge_index)
        pred = out.argmax(dim=1)
        correct = pred[mask] == data.y[mask]
        acc = int(correct.sum()) / int(mask.sum())
    return acc


def run_experiment(model_class, data, model_params, train_params,
                   runs=10, verbose=True):
    """
    多次运行实验，取平均值
    返回训练历史记录和测试准确率
    """
    all_train_accs = []
    all_val_accs = []
    all_test_accs = []
    best_test_accs = []

    for run in range(runs):
        # 初始化模型和优化器
        model = model_class(**model_params)
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=train_params['lr'],
            weight_decay=train_params['weight_decay']
        )
        criterion = nn.NLLLoss()

        best_val_acc = 0
        best_test_acc = 0
        patience = train_params['patience']
        patience_counter = 0

        for epoch in range(train_params['epochs']):
            loss = train(model, data, optimizer, criterion)

            # 评估
            train_acc = evaluate(model, data, data.train_mask)
            val_acc = evaluate(model, data, data.val_mask)
            test_acc = evaluate(model, data, data.test_mask)

            # 早停机制
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_test_acc = test_acc
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    if verbose and run == 0:
                        print(f"  早停于 Epoch {epoch}")
                    break

        all_train_accs.append(evaluate(model, data, data.train_mask))
        all_val_accs.append(best_val_acc)
        all_test_accs.append(best_test_acc)
        best_test_accs.append(best_test_acc)

        if verbose:
            print(f"  Run {run + 1}/{runs}: "
                  f"Train={all_train_accs[-1]:.4f}, "
                  f"Val={all_val_accs[-1]:.4f}, "
                  f"Test={all_test_accs[-1]:.4f}")

    return {
        'train_mean': np.mean(all_train_accs),
        'train_std': np.std(all_train_accs),
        'val_mean': np.mean(all_val_accs),
        'val_std': np.std(all_val_accs),
        'test_mean': np.mean(all_test_accs),
        'test_std': np.std(all_test_accs),
        'all_test': best_test_accs
    }


def train_with_history(model, data, optimizer, criterion, epochs):
    """
    带完整历史记录的训练（用于绘制损失曲线）
    """
    history = {'loss': [], 'train_acc': [], 'val_acc': [], 'test_acc': []}
    best_val_acc = 0
    best_model_state = None

    for epoch in range(epochs):
        loss = train(model, data, optimizer, criterion)

        train_acc = evaluate(model, data, data.train_mask)
        val_acc = evaluate(model, data, data.val_mask)
        test_acc = evaluate(model, data, data.test_mask)

        history['loss'].append(loss)
        history['train_acc'].append(train_acc)
        history['val_acc'].append(val_acc)
        history['test_acc'].append(test_acc)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_state = model.state_dict().copy()

    return history, best_model_state


# ==================== 4. 可视化函数 ====================
def plot_training_curves(histories, model_names, save_path='training_curves.png'):
    """绘制三个模型的训练曲线对比"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 损失曲线
    ax = axes[0]
    for name in model_names:
        ax.plot(histories[name]['loss'], label=name)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.set_title('训练损失曲线')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 验证准确率曲线
    ax = axes[1]
    for name in model_names:
        ax.plot(histories[name]['val_acc'], label=name)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Validation Accuracy')
    ax.set_title('验证准确率曲线')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()  # 关闭图形，释放内存
    print(f"训练曲线已保存至 {save_path}")


def plot_results_comparison(results, dataset_name, save_path='results_comparison.png'):
    """绘制三个模型测试准确率的对比柱状图"""
    fig, ax = plt.subplots(figsize=(10, 6))

    model_names = list(results.keys())
    test_means = [results[name]['test_mean'] for name in model_names]
    test_stds = [results[name]['test_std'] for name in model_names]

    colors = ['#3498db', '#2ecc71', '#e74c3c']
    bars = ax.bar(model_names, test_means, yerr=test_stds,
                  capsize=10, color=colors, alpha=0.8, edgecolor='black')

    # 在柱子上方显示数值
    for bar, mean, std in zip(bars, test_means, test_stds):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f'{mean:.4f}±{std:.4f}', ha='center', va='bottom', fontsize=11)

    ax.set_ylim(0, 1.0)
    ax.set_ylabel('测试准确率', fontsize=12)
    ax.set_title(f'{dataset_name} 数据集上模型对比\n(MLP vs GCN vs GAT)', fontsize=14)
    ax.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"结果对比图已保存至 {save_path}")


# ==================== 5. 主程序 ====================
def main(dataset_name='Cora'):
    print("=" * 60)
    print(f"经典图神经网络模型对比——节点分类任务")
    print(f"数据集: {dataset_name}")
    print("=" * 60)

    # 加载数据
    data, dataset = load_data(dataset_name)
    print(f"\n数据集信息:")
    print(f"  - 节点数: {data.num_nodes}")
    print(f"  - 边数: {data.num_edges}")
    print(f"  - 特征维度: {dataset.num_features}")
    print(f"  - 类别数: {dataset.num_classes}")
    print(f"  - 训练节点数: {data.train_mask.sum().item()}")
    print(f"  - 验证节点数: {data.val_mask.sum().item()}")
    print(f"  - 测试节点数: {data.test_mask.sum().item()}")

    # 模型公共参数
    model_params_common = {
        'in_channels': dataset.num_features,
        'hidden_channels': 16,
        'out_channels': dataset.num_classes,
        'dropout': 0.5
    }

    train_params = {
        'lr': 0.01,
        'weight_decay': 5e-4,
        'epochs': 200,
        'patience': 20
    }

    # 存储结果
    results = {}
    histories = {}

    # ========== 训练 MLP ==========
    print("\n" + "=" * 40)
    print("训练 MLP (多层感知机，仅使用节点特征)")
    print("=" * 40)
    mlp_result = run_experiment(
        MLP, data, model_params_common, train_params, runs=10
    )
    results['MLP'] = mlp_result

    # 单独训练一次用于记录历史曲线
    mlp_model = MLP(**model_params_common)
    mlp_optimizer = torch.optim.Adam(mlp_model.parameters(),
                                     lr=train_params['lr'],
                                     weight_decay=train_params['weight_decay'])
    mlp_history, _ = train_with_history(
        mlp_model, data, mlp_optimizer, nn.NLLLoss(), train_params['epochs']
    )
    histories['MLP'] = mlp_history

    # ========== 训练 GCN ==========
    print("\n" + "=" * 40)
    print("训练 GCN (图卷积网络)")
    print("=" * 40)
    gcn_result = run_experiment(
        GCN, data, model_params_common, train_params, runs=10
    )
    results['GCN'] = gcn_result

    gcn_model = GCN(**model_params_common)
    gcn_optimizer = torch.optim.Adam(gcn_model.parameters(),
                                     lr=train_params['lr'],
                                     weight_decay=train_params['weight_decay'])
    gcn_history, _ = train_with_history(
        gcn_model, data, gcn_optimizer, nn.NLLLoss(), train_params['epochs']
    )
    histories['GCN'] = gcn_history

    # ========== 训练 GAT ==========
    print("\n" + "=" * 40)
    print("训练 GAT (图注意力网络)")
    print("=" * 40)
    model_params_gat = model_params_common.copy()
    model_params_gat['heads'] = 8
    gat_result = run_experiment(
        GAT, data, model_params_gat, train_params, runs=10
    )
    results['GAT'] = gat_result

    gat_model = GAT(**model_params_gat)
    gat_optimizer = torch.optim.Adam(gat_model.parameters(),
                                     lr=train_params['lr'],
                                     weight_decay=train_params['weight_decay'])
    gat_history, _ = train_with_history(
        gat_model, data, gat_optimizer, nn.NLLLoss(), train_params['epochs']
    )
    histories['GAT'] = gat_history

    # ========== 输出结果 ==========
    print("\n" + "=" * 60)
    print("实验结果汇总")
    print("=" * 60)
    print(f"\n模型在 {dataset_name} 数据集上的测试准确率 (10次运行平均):")
    print("-" * 50)
    for name in ['MLP', 'GCN', 'GAT']:
        r = results[name]
        print(f"  {name}: {r['test_mean']:.4f} ± {r['test_std']:.4f}")

    # 计算性能提升
    print("\n" + "-" * 50)
    print("性能提升分析:")
    print(f"  GCN 相比 MLP 提升: "
          f"{(results['GCN']['test_mean'] - results['MLP']['test_mean']) * 100:.2f}%")
    print(f"  GAT 相比 MLP 提升: "
          f"{(results['GAT']['test_mean'] - results['MLP']['test_mean']) * 100:.2f}%")
    print(f"  GAT 相比 GCN: "
          f"{(results['GAT']['test_mean'] - results['GCN']['test_mean']) * 100:.2f}%")

    # 绘制可视化图表（自动保存，不弹窗）
    plot_training_curves(histories, ['MLP', 'GCN', 'GAT'],
                         save_path=f'{dataset_name}_训练曲线.png')
    plot_results_comparison(results, dataset_name,
                            save_path=f'{dataset_name}_结果对比.png')

    print("\n" + "=" * 60)
    print("程序运行完成！图片已保存至当前文件夹。")
    print("=" * 60)

    return results, histories


if __name__ == "__main__":
    # 可以修改为 'Citeseer' 测试另一个数据集
    main(dataset_name='Cora')