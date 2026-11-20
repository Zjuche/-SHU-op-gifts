import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score
import os
from torch.utils.tensorboard import SummaryWriter  # 添加TensorBoard支持
from torchsummary import summary  # 添加文本摘要支持

# 创建保存结果的目录
os.makedirs('results', exist_ok=True)

# 步骤1: 准备数据
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

train_set = torchvision.datasets.MNIST(root='./data', train=True, download=True, transform=transform)
test_set = torchvision.datasets.MNIST(root='./data', train=False, download=True, transform=transform)

train_loader = torch.utils.data.DataLoader(train_set, batch_size=64, shuffle=True)
test_loader = torch.utils.data.DataLoader(test_set, batch_size=64, shuffle=False)


# 步骤2: 定义CNN模型
class MNISTCNN(nn.Module):
    def __init__(self):
        super(MNISTCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.fc1 = nn.Linear(32 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, 10)
        # 使用LogSoftmax配合NLLLoss更稳定
        self.softmax = nn.LogSoftmax(dim=1)

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(-1, 32 * 7 * 7)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return self.softmax(x)


# 创建模型实例
model = MNISTCNN()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)


# 步骤3: 生成网络结构示意图（更可靠的替代方案）
def visualize_model(model):
    # 方案1: 使用TensorBoard可视化
    try:
        writer = SummaryWriter('results/tensorboard')
        dummy_input = torch.randn(1, 1, 28, 28).to(device)
        writer.add_graph(model, dummy_input)
        writer.close()
        print("TensorBoard网络结构已保存到 'results/tensorboard'")
        print("在命令行运行: tensorboard --logdir=results/tensorboard")
        return "TensorBoard可视化成功"
    except Exception as e:
        print(f"TensorBoard可视化失败: {e}")

    # 方案2: 文本摘要（无需额外依赖）
    try:
        from torchsummary import summary
        summary_str = str(summary(model, (1, 28, 28), device=device.type))
        with open('results/model_summary.txt', 'w') as f:
            f.write(summary_str)
        print("模型文本摘要已保存为 'results/model_summary.txt'")
        print("\n网络结构文本摘要:\n")
        print(summary_str)
        return summary_str
    except Exception as e:
        print(f"文本摘要失败: {e}")

    # 方案3: 手动绘图（最后备选）
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle

        plt.figure(figsize=(12, 8))
        plt.title("CNN 结构示意图")

        # 绘制网络层
        layers = [
            ("Input (1, 28, 28)", 0, 0),
            ("Conv1 (16@28x28)", 1, 0),
            ("ReLU", 2, 0),
            ("MaxPool1 (16@14x14)", 3, 0),
            ("Conv2 (32@14x14)", 4, 0),
            ("ReLU", 5, 0),
            ("MaxPool2 (32@7x7)", 6, 0),
            ("Flatten (1568)", 7, 0),
            ("FC1 (128)", 8, 0),
            ("ReLU", 9, 0),
            ("FC2 (10)", 10, 0),
            ("Softmax", 11, 0)
        ]

        for i, (name, x, y) in enumerate(layers):
            plt.gca().add_patch(Rectangle((x, y), 0.8, 0.8, fill=None, edgecolor='blue'))
            plt.text(x + 0.4, y + 0.4, name, ha='center', va='center')
            if i > 0:
                plt.arrow(x - 0.8 + 0.4, y + 0.4, 0.4, 0, head_width=0.1, head_length=0.1, fc='k', ec='k')

        plt.xlim(-0.5, 12)
        plt.ylim(-0.5, 1)
        plt.axis('off')
        plt.savefig('results/manual_cnn_architecture.png')
        print("手动绘制的网络结构图已保存为 'results/manual_cnn_architecture.png'")
        return "手动绘图成功"
    except Exception as e:
        print(f"手动绘图失败: {e}")
        return "无法生成网络结构"


# 执行可视化
architecture_summary = visualize_model(model)

# 步骤4: 训练配置
criterion = nn.NLLLoss()  # 配合LogSoftmax使用NLLLoss
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 步骤5: 训练模型
epochs = 5
train_losses = []
train_accuracies = []

print("\n开始训练模型...")
for epoch in range(epochs):
    model.train()
    running_loss = 0.0
    preds, labels_list = [], []

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        preds.extend(predicted.cpu().numpy())
        labels_list.extend(labels.cpu().numpy())

    epoch_loss = running_loss / len(train_loader)
    epoch_acc = accuracy_score(labels_list, preds)
    train_losses.append(epoch_loss)
    train_accuracies.append(epoch_acc)
    print(f"Epoch {epoch + 1}/{epochs} - 损失: {epoch_loss:.4f}, 准确率: {epoch_acc:.4f}")

# 步骤6: 测试模型
model.eval()
test_preds, test_labels = [], []

with torch.no_grad():
    correct = 0
    total = 0
    for images, labels in test_loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        _, predicted = torch.max(outputs, 1)
        test_preds.extend(predicted.cpu().numpy())
        test_labels.extend(labels.cpu().numpy())
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

test_accuracy = correct / total
print(f"\n测试准确率: {test_accuracy:.4f}")

# 步骤7: 可视化训练结果
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(range(1, epochs + 1), train_losses, 'o-')
plt.title('训练损失变化')
plt.xlabel('训练轮次')
plt.ylabel('损失值')
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(range(1, epochs + 1), train_accuracies, 'o-')
plt.title('训练准确率变化')
plt.xlabel('训练轮次')
plt.ylabel('准确率')
plt.grid(True)

plt.tight_layout()
plt.savefig('results/training_results.png')
print("训练结果图已保存为 'results/training_results.png'")

# 保存模型
torch.save(model.state_dict(), 'results/mnist_cnn_model.pth')

# 输出最终结果
print("\n实验完成!")
print(f"最终测试准确率: {test_accuracy:.4f}")
print(f"模型和结果保存在 'results' 目录中")