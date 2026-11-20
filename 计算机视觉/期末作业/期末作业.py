import matplotlib

matplotlib.use('Agg')  # 强制使用无界面后端，解决无法显示/作图问题

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torchvision.models import resnet18, ResNet18_Weights
import matplotlib.pyplot as plt
import numpy as np
import cv2
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from tqdm import tqdm
import os


# -------------------- 函数定义 --------------------
def train_one_epoch(model, trainloader, criterion, optimizer, device, epoch, epochs):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    pbar = tqdm(trainloader, desc=f"Epoch {epoch + 1}/{epochs}")
    for inputs, labels in pbar:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        pbar.set_postfix(loss=loss.item(), acc=100. * correct / total)
    return running_loss / len(trainloader), 100. * correct / total


def evaluate(model, testloader, device):
    model.eval()
    correct = 0
    total = 0
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for inputs, labels in testloader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    return 100. * correct / total, all_preds, all_labels


def grad_cam(model, image_tensor, target_class, device, feature_module='layer4'):
    gradients = []
    activations = []

    def backward_hook(module, grad_in, grad_out):
        gradients.append(grad_out[0].detach())
        return None

    def forward_hook(module, inp, outp):
        activations.append(outp.detach())
        return None

    target_layer = getattr(model, feature_module)[-1].conv2
    hook_f = target_layer.register_forward_hook(forward_hook)
    hook_b = target_layer.register_full_backward_hook(backward_hook)

    output = model(image_tensor)
    score = output[0, target_class]
    model.zero_grad()
    score.backward()

    grad = gradients[0]
    act = activations[0]
    weights = torch.mean(grad, dim=[2, 3], keepdim=True)
    cam = torch.sum(weights * act, dim=1, keepdim=True)
    cam = torch.relu(cam)
    cam = cam.squeeze().cpu().numpy()
    cam = np.maximum(cam, 0)
    if np.max(cam) != np.min(cam):
        cam = (cam - np.min(cam)) / (np.max(cam) - np.min(cam) + 1e-8)
    else:
        cam = np.zeros_like(cam)
    cam = cv2.resize(cam, (32, 32))

    hook_f.remove()
    hook_b.remove()
    return cam


def denormalize(tensor, mean, std):
    img = tensor.cpu().numpy().transpose(1, 2, 0)
    img = std * img + mean
    img = np.clip(img, 0, 1)
    return img


# -------------------- 主程序 --------------------
if __name__ == '__main__':
    # 超参数
    BATCH_SIZE = 64
    EPOCHS = 10
    LEARNING_RATE = 1e-3
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {DEVICE}")

    # 数据均值和标准差（CIFAR-10 官方值）
    mean = (0.4914, 0.4822, 0.4465)
    std = (0.2023, 0.1994, 0.2010)

    transform_train = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    # 加载完整数据集（会自动下载）
    full_trainset = torchvision.datasets.CIFAR10(root='./data', train=True, download=True, transform=transform_train)
    full_testset = torchvision.datasets.CIFAR10(root='./data', train=False, download=True, transform=transform_test)

    # 随机采样子集（加速训练）
    np.random.seed(42)
    train_subset_size = 5000  # 训练子集大小
    test_subset_size = 1000  # 测试子集大小
    train_indices = np.random.choice(len(full_trainset), train_subset_size, replace=False)
    test_indices = np.random.choice(len(full_testset), test_subset_size, replace=False)

    trainset = torch.utils.data.Subset(full_trainset, train_indices)
    testset = torch.utils.data.Subset(full_testset, test_indices)

    # DataLoader（num_workers=0 避免 Windows 多进程错误）
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    testloader = torch.utils.data.DataLoader(testset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    classes = ('plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck')
    print(f"Training on {len(trainset)} images, testing on {len(testset)} images")

    # 模型：预训练 ResNet-18，修改全连接层
    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, 10)
    model = model.to(DEVICE)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    # 训练循环
    train_losses, train_accs = [], []
    best_acc = 0.0
    for epoch in range(EPOCHS):
        train_loss, train_acc = train_one_epoch(model, trainloader, criterion, optimizer, DEVICE, epoch, EPOCHS)
        train_losses.append(train_loss)
        train_accs.append(train_acc)
        scheduler.step()

        test_acc, preds, labels = evaluate(model, testloader, DEVICE)
        print(f"Test acc: {test_acc:.2f}%")
        if test_acc > best_acc:
            best_acc = test_acc
            torch.save(model.state_dict(), 'best_cifar10_subset.pth')

    print(f"Best test accuracy: {best_acc:.2f}%")

    # -------------------- 保存训练曲线（不使用显示） --------------------
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(range(1, EPOCHS + 1), train_losses, 'b-o', label='Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Loss Curve')
    plt.legend()
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(range(1, EPOCHS + 1), train_accs, 'r-o', label='Training Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.title('Accuracy Curve')
    plt.legend()
    plt.grid(True)
    plt.savefig('training_curves.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("已保存: training_curves.png")

    # -------------------- 混淆矩阵 --------------------
    cm = confusion_matrix(labels, preds)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=classes)
    disp.plot(cmap='Blues', xticks_rotation=45)
    plt.title('Confusion Matrix on Test Set')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("已保存: confusion_matrix.png")

    # -------------------- Grad-CAM 可视化 --------------------
    model.load_state_dict(torch.load('best_cifar10_subset.pth', map_location=DEVICE))
    model.eval()
    num_images = 8
    fig, axes = plt.subplots(num_images, 3, figsize=(9, 3 * num_images))

    for idx, (data, label) in enumerate(testset):
        if idx >= num_images: break
        img_tensor = data.unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            output = model(img_tensor)
            pred = torch.argmax(output, dim=1).item()

        cam = grad_cam(model, img_tensor, target_class=pred, device=DEVICE)
        orig_img = denormalize(data, np.array(mean), np.array(std))
        heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB) / 255.0
        overlay = 0.6 * heatmap + 0.4 * orig_img

        axes[idx, 0].imshow(orig_img)
        axes[idx, 0].set_title(f"True: {classes[label]}\nPred: {classes[pred]}")
        axes[idx, 0].axis('off')

        axes[idx, 1].imshow(cam, cmap='jet')
        axes[idx, 1].set_title("Grad-CAM heatmap")
        axes[idx, 1].axis('off')

        axes[idx, 2].imshow(overlay)
        axes[idx, 2].set_title("Overlay")
        axes[idx, 2].axis('off')

    plt.tight_layout()
    plt.savefig('gradcam_results.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("已保存: gradcam_results.png")

    print("所有图片已生成完毕！")