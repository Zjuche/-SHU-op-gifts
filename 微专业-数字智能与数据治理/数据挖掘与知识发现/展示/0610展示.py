# -*- coding: utf-8 -*-
"""
AIGC微短剧问卷数据挖掘 - KMeans聚类分析（无GUI后端，自动保存图片）
"""

import pandas as pd
import numpy as np
import matplotlib
# 关键：使用Agg后端，避免Tcl/Tk错误，所有图表将保存为文件
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

# ==================== 设置中文字体（保存图片时支持中文） ====================
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
plt.rcParams['axes.unicode_minus'] = False
import matplotlib.font_manager as fm
available_fonts = [f.name for f in fm.fontManager.ttflist]
used_font = None
for font in plt.rcParams['font.sans-serif']:
    if font in available_fonts:
        used_font = font
        break
if used_font:
    print(f"使用中文字体: {used_font}")
else:
    print("警告：未找到中文字体，图表中的中文可能显示为方块。")

# ==================== 1. 数据读取 ====================
file_path = '问卷数据.xlsx'
df_raw = pd.read_excel(file_path, header=1, engine='openpyxl')

print("原始数据形状:", df_raw.shape)
print("前5行:\n", df_raw.head())

# ==================== 2. 数据清洗 ====================
df_raw.drop_duplicates(inplace=True)

id_cols = ['作答ID', '用户ID', '开始时间', '结束时间', '作答总时长(秒)', '作答渠道', '发布ID', '问卷发布名称', '省份', '城市', '设备类型', '操作系统类型', '浏览器类型', '屏幕分辨率']
drop_cols = [col for col in id_cols if col in df_raw.columns]
df_clean = df_raw.drop(columns=drop_cols)

print("清洗后保留的列:", df_clean.columns.tolist())

# ==================== 3. 缺失值处理（修正 Copy-on-Write 警告） ====================
print("\n缺失值统计:\n", df_clean.isnull().sum())

for col in df_clean.columns:
    if df_clean[col].dtype in ['int64', 'float64']:
        median_val = df_clean[col].median()
        df_clean[col] = df_clean[col].fillna(median_val)   # 非 inplace 赋值
    else:
        mode_val = df_clean[col].mode()[0] if not df_clean[col].mode().empty else 'Unknown'
        df_clean[col] = df_clean[col].fillna(mode_val)

# ==================== 4. 特征工程与标准化 ====================
numeric_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()
print("\n自动识别的数值列:", numeric_cols)

# 手动编码分类特征（如果没有这些列，代码会跳过）
if '您平均每周观看微短剧的时长' in df_clean.columns:
    duration_map = {'少于1小时': 1, '1-3小时': 2, '3-5小时': 3, '5小时以上': 4}
    df_clean['观看时长_编码'] = df_clean['您平均每周观看微短剧的时长'].map(duration_map)
    numeric_cols.append('观看时长_编码')

if '您平均每周观看微短剧的频次' in df_clean.columns:
    freq_map = {'少于1次': 1, '1-3次': 2, '4-6次': 3, '每天一次或更多': 4}
    df_clean['观看频次_编码'] = df_clean['您平均每周观看微短剧的频次'].map(freq_map)
    numeric_cols.append('观看频次_编码')

if '您的性别' in df_clean.columns:
    df_clean['性别_编码'] = df_clean['您的性别'].map({'男': 1, '女': 0})
    numeric_cols.append('性别_编码')

if '您当前的学历阶段' in df_clean.columns:
    edu_map = {'本科生': 1, '硕士研究生': 2, '博士研究生': 3, '其他': 0}
    df_clean['学历_编码'] = df_clean['您当前的学历阶段'].map(edu_map)
    numeric_cols.append('学历_编码')

# 最终特征集
features = [col for col in numeric_cols if col in df_clean.columns]
print("用于聚类的特征数:", len(features))
print("特征列表:", features)

X = df_clean[features].copy()
X = X.fillna(X.median())  # 二次保险

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ==================== 5. 确定最优K值 ====================
inertias = []
sil_scores = []
K_range = range(2, 11)

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    inertias.append(kmeans.inertia_)
    sil_scores.append(silhouette_score(X_scaled, kmeans.labels_))

# 绘制肘部图和轮廓系数图（保存为文件）
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(K_range, inertias, 'bo-')
plt.xlabel('聚类数 K')
plt.ylabel('簇内离差平方和')
plt.title('肘部法则确定K')

plt.subplot(1, 2, 2)
plt.plot(K_range, sil_scores, 'ro-')
plt.xlabel('聚类数 K')
plt.ylabel('轮廓系数')
plt.title('轮廓系数确定K')
plt.tight_layout()
plt.savefig('K值确定图.png', dpi=150)
plt.close()
print("已保存: K值确定图.png")

best_k = K_range[np.argmax(sil_scores)]
print(f"\n最佳聚类数 K = {best_k} (轮廓系数最高)")

# ==================== 6. 最终聚类 ====================
kmeans_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
df_clean['Cluster'] = kmeans_final.fit_predict(X_scaled)

print("\n聚类结果样例:\n", df_clean[['Cluster'] + features[:5]].head())

# ==================== 7. 可视化（全部保存为图片） ====================
# 7.1 PCA散点图
pca = PCA(n_components=2, random_state=42)
X_pca = pca.fit_transform(X_scaled)
df_clean['PCA1'] = X_pca[:, 0]
df_clean['PCA2'] = X_pca[:, 1]

plt.figure(figsize=(10, 6))
sns.scatterplot(data=df_clean, x='PCA1', y='PCA2', hue='Cluster', palette='Set2', s=60)
plt.title(f'PCA降维后聚类分布 (K={best_k})')
plt.xlabel(f'主成分1 ({pca.explained_variance_ratio_[0]:.2%})')
plt.ylabel(f'主成分2 ({pca.explained_variance_ratio_[1]:.2%})')
plt.legend(title='聚类类别')
plt.savefig('PCA聚类散点图.png', dpi=150)
plt.close()
print("已保存: PCA聚类散点图.png")

# 7.2 雷达图（选取前8个量表题）
scale_questions = [col for col in features if 'AIGC' in col or '您觉得' in col or '您认为' in col or '观看' not in col]
scale_questions = scale_questions[:8]
if scale_questions:
    cluster_means = df_clean.groupby('Cluster')[scale_questions].mean()
    angles = np.linspace(0, 2 * np.pi, len(scale_questions), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={'projection': 'polar'})
    for c in range(best_k):
        values = cluster_means.loc[c].values.tolist()
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=f'簇 {c}')
        ax.fill(angles, values, alpha=0.1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(scale_questions, size=8)
    ax.set_ylim(1, 5)
    ax.set_title('各聚类在主要量表题上的均值轮廓', fontsize=14)
    ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
    plt.savefig('雷达图.png', dpi=150)
    plt.close()
    print("已保存: 雷达图.png")

# 7.3 热力图
plt.figure(figsize=(14, 8))
cluster_profile = df_clean.groupby('Cluster')[features].mean()
sns.heatmap(cluster_profile.T, annot=True, cmap='coolwarm', center=0, fmt='.2f')
plt.title('各聚类特征均值热力图')
plt.xlabel('聚类类别')
plt.ylabel('特征名称')
plt.tight_layout()
plt.savefig('特征均值热力图.png', dpi=150)
plt.close()
print("已保存: 特征均值热力图.png")

# 7.4 样本量柱状图
plt.figure(figsize=(8, 5))
cluster_counts = df_clean['Cluster'].value_counts().sort_index()
sns.barplot(x=cluster_counts.index, y=cluster_counts.values, palette='viridis')
plt.xlabel('聚类类别')
plt.ylabel('样本数')
plt.title(f'各聚类样本量 (K={best_k})')
for i, v in enumerate(cluster_counts.values):
    plt.text(i, v + 2, str(v), ha='center')
plt.savefig('样本量柱状图.png', dpi=150)
plt.close()
print("已保存: 样本量柱状图.png")

# ==================== 8. 保存结果 ====================
output_file = '聚类结果_带标签.xlsx'
df_clean.to_excel(output_file, index=False)
print(f"\n聚类结果已保存至: {output_file}")

centers_scaled = kmeans_final.cluster_centers_
centers_original = scaler.inverse_transform(centers_scaled)
centers_df = pd.DataFrame(centers_original, columns=features)
centers_df.index.name = 'Cluster'
centers_df.to_excel('聚类中心_原始尺度.xlsx')
print("聚类中心（原始尺度）已保存至: 聚类中心_原始尺度.xlsx")

print("\n所有图表已保存为当前目录下的 PNG 文件，请用图片查看器打开。")