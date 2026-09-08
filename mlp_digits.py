# -*- coding: utf-8 -*-
"""
实验作业一：使用 PyTorch 在 load_digits 上设计更好的神经网络
参考代码框架（与实验指南第 7 节一致）：
  模型类 MLP 的隐藏层结构 / 激活函数 / Dropout / BatchNorm 均可通过参数配置，
  训练函数 run 的优化器 / 学习率 / weight_decay 均为可配置参数。

用法示例：
  # 基线：1x32 Sigmoid + SGD(0.1)，30 epoch
  python mlp_digits.py --tag baseline --hidden 32 --act sigmoid --opt sgd --lr 0.1
  # 换激活函数 ReLU
  python mlp_digits.py --tag exp1 --hidden 32 --act relu --opt sgd --lr 0.1
"""
import argparse
import time

import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 图中文字体
plt.rcParams["axes.unicode_minus"] = False

DATA_SEED = 42  # 全局数据划分随机种子，保证对比公平
DIGIT_OUT = 10  # 10 个数字类别


# ---------- 1. 数据 ----------
def load_data():
    """加载 load_digits，归一化到 [0,1]，8:2 分层划分（共用同一份划分）。"""
    X, y = load_digits(return_X_y=True)
    X = X.astype(np.float32) / 16.0
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=DATA_SEED
    )
    X_tr = torch.tensor(X_tr)
    y_tr = torch.tensor(y_tr, dtype=torch.long)  # 必须 Long，否则 CrossEntropyLoss 报错
    X_te = torch.tensor(X_te)
    y_te = torch.tensor(y_te, dtype=torch.long)
    return X_tr, X_te, y_tr, y_te


# ---------- 2. 模型 ----------
class MLP(nn.Module):
    """多层感知器。hidden 为各隐藏层神经元数元组，例如 (32,) 或 (128, 128)。"""

    def __init__(self, hidden=(32,), act="sigmoid", dropout=0.0, use_bn=False):
        super().__init__()
        act_layer = {"sigmoid": nn.Sigmoid, "tanh": nn.Tanh,
                     "relu": nn.ReLU, "gelu": nn.GELU}[act]
        layers, prev = [], 64  # 输入为 8x8=64 维
        for h in hidden:
            layers.append(nn.Linear(prev, h))
            if use_bn:                       # 改进点①：BatchNorm
                layers.append(nn.BatchNorm1d(h))
            layers.append(act_layer())
            if dropout > 0:                  # 改进点②：Dropout
                layers.append(nn.Dropout(dropout))
            prev = h
        layers.append(nn.Linear(prev, DIGIT_OUT))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


# ---------- 3. 训练与评估 ----------
def run(model, X_tr, X_te, y_tr, y_te, opt_name="sgd", lr=0.1,
        epochs=30, wd=0.0):
    """全批量训练；每个 epoch 记录训练损失与测试准确率，返回历史与耗时。"""
    if opt_name == "sgd":                    # 改进点③：优化器可切换
        opt = torch.optim.SGD(model.parameters(), lr=lr, weight_decay=wd)
    else:
        opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    loss_fn = nn.CrossEntropyLoss()
    hist = {"loss": [], "acc": []}
    t0 = time.time()
    for _ in range(epochs):
        model.train()
        opt.zero_grad()
        loss = loss_fn(model(X_tr), y_tr)    # 前向 + 损失
        loss.backward()                      # 反向传播
        opt.step()                           # 参数更新
        model.eval()
        with torch.no_grad():
            acc = (model(X_te).argmax(1) == y_te).float().mean().item()
        hist["loss"].append(loss.item())
        hist["acc"].append(acc)
    return hist, time.time() - t0


def save_curve(hist, path, title, acc_only=False):
    """绘制训练损失 / 测试准确率随 epoch 的变化曲线并保存。"""
    epochs = range(1, len(hist["loss"]) + 1)
    if acc_only:
        fig, ax = plt.subplots(figsize=(5.2, 3.6))
        ax.plot(epochs, np.array(hist["acc"]) * 100, "-o", ms=3, color="#1f77b4")
        ax.set_xlabel("epoch")
        ax.set_ylabel("测试准确率 (%)")
        ax.set_ylim(0, 105)
        ax.grid(True, ls="--", alpha=0.4)
    else:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.6))
        ax1.plot(epochs, hist["loss"], "-o", ms=3, color="#d62728")
        ax1.set_xlabel("epoch")
        ax1.set_ylabel("训练损失")
        ax1.grid(True, ls="--", alpha=0.4)
        ax2.plot(epochs, np.array(hist["acc"]) * 100, "-o", ms=3, color="#1f77b4")
        ax2.set_xlabel("epoch")
        ax2.set_ylabel("测试准确率 (%)")
        ax2.set_ylim(0, 105)
        ax2.grid(True, ls="--", alpha=0.4)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="baseline", help="输出文件名标签")
    ap.add_argument("--hidden", type=int, nargs="+", default=[32])
    ap.add_argument("--act", default="sigmoid", choices=["sigmoid", "tanh", "relu", "gelu"])
    ap.add_argument("--opt", default="sgd", choices=["sgd", "adam"])
    ap.add_argument("--lr", type=float, default=0.1)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--wd", type=float, default=0.0, help="weight_decay (L2)")
    ap.add_argument("--dropout", type=float, default=0.0)
    ap.add_argument("--bn", action="store_true", help="在隐藏层后加 BatchNorm")
    ap.add_argument("--seed", type=int, default=DATA_SEED, help="torch 随机种子")
    ap.add_argument("--no-fig", action="store_true", help="不保存曲线图")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    X_tr, X_te, y_tr, y_te = load_data()
    model = MLP(hidden=tuple(args.hidden), act=args.act,
                dropout=args.dropout, use_bn=args.bn)
    hist, dt = run(model, X_tr, X_te, y_tr, y_te,
                   opt_name=args.opt, lr=args.lr, epochs=args.epochs, wd=args.wd)
    acc = hist["acc"][-1] * 100
    print(f"[{args.tag}] 最终测试准确率: {acc:.2f}%  训练耗时: {dt:.1f}s")

    if not args.no_fig:
        cfg = (f"hidden={tuple(args.hidden)} act={args.act} opt={args.opt}"
               f" lr={args.lr} wd={args.wd} dropout={args.dropout} bn={args.bn}"
               f" seed={args.seed}")
        save_curve(hist, f"result_{args.tag}.png",
                   f"{args.tag}  (最终测试准确率 {acc:.2f}%)\n{cfg}")
    return {"tag": args.tag, "acc": acc, "time": dt,
            "loss_last": hist["loss"][-1], "config": vars(args)}


if __name__ == "__main__":
    main()
