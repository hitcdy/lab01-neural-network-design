# -*- coding: utf-8 -*-
"""
批量运行实验作业一的全部对照实验：
  组0 基线  1x32 Sigmoid + SGD(0.1)
  组1 换激活函数    Sigmoid -> ReLU
  组2 加深网络      1层 -> 2层x128 (Sigmoid)
  组3 换优化器      SGD -> Adam(0.01)
  组4 调学习率      0.1 -> 0.01 (SGD)
  组5 加L2正则      weight_decay = 1e-4
  组6 加Dropout     p = 0.2
  组7 加BatchNorm   每个隐藏层后 BatchNorm1d
  组8 最优组合      ReLU + 2x128 + BatchNorm + Adam(0.001)，固定种子复测3次
  失败组 学习率过大 lr=10.0（另扫描 lr=1/5/10/20 找发散临界点）
全部组共用同一数据划分（random_state=42），每组只改动一个变量。
"""
import json
import time

import numpy as np
import torch

import mlp_digits as lab

GROUPS = [
    # (tag, hidden, act, opt, lr, wd, dropout, bn, 说明)
    ("baseline", (32,),    "sigmoid", "sgd",  0.1,  0.0, 0.0, False, "组0 基线 Baseline"),
    ("exp1",     (32,),    "relu",    "sgd",  0.1,  0.0, 0.0, False, "组1 换激活函数 Sigmoid->ReLU"),
    ("exp2",     (128,128),"sigmoid", "sgd",  0.1,  0.0, 0.0, False, "组2 加深网络 2层x128"),
    ("exp3",     (32,),    "sigmoid", "adam", 0.01, 0.0, 0.0, False, "组3 换优化器 SGD->Adam(0.01)"),
    ("exp4",     (32,),    "sigmoid", "sgd",  0.01, 0.0, 0.0, False, "组4 调学习率 0.1->0.01"),
    ("exp5",     (32,),    "sigmoid", "sgd",  0.1,  1e-4,0.0, False, "组5 加L2正则 wd=1e-4"),
    ("exp6",     (32,),    "sigmoid", "sgd",  0.1,  0.0, 0.2, False, "组6 加Dropout p=0.2"),
    ("exp7",     (32,),    "sigmoid", "sgd",  0.1,  0.0, 0.0, True,  "组7 加BatchNorm"),
    ("exp8",     (128,128),"relu",    "adam", 0.001,0.0, 0.0, True,  "组8 最优组合"),
]


def run_once(tag, hidden, act, opt, lr, wd, dropout, bn, seed, save_fig=True):
    torch.manual_seed(seed)
    np.random.seed(seed)
    X_tr, X_te, y_tr, y_te = lab.load_data()
    model = lab.MLP(hidden=hidden, act=act, dropout=dropout, use_bn=bn)
    hist, dt = lab.run(model, X_tr, X_te, y_tr, y_te, opt_name=opt,
                       lr=lr, epochs=30, wd=wd)
    acc = hist["acc"][-1] * 100
    if save_fig:
        lab.save_curve(hist, f"result_{tag}.png",
                       f"{tag}: acc={acc:.2f}%  "
                       f"hidden={list(hidden)} act={act} opt={opt} lr={lr} "
                       f"wd={wd} dropout={dropout} bn={bn} seed={seed}",
                       acc_only=(tag == "exp8"))
    return {"tag": tag, "acc": round(acc, 2), "time": round(dt, 2),
            "loss": hist["loss"][-1]}


def main():
    results = []
    # 1) 组0-8（单次，种子42，与基线可比）
    for tag, hidden, act, opt, lr, wd, dropout, bn, note in GROUPS:
        r = run_once(tag, hidden, act, opt, lr, wd, dropout, bn, seed=42)
        r["note"] = note
        results.append(r)
        print(f"[{tag}] {note}: acc={r['acc']:.2f}%  time={r['time']}s")

    # 2) 最优组合复测 3 次（不同 torch 种子，数据划分不变）
    seeds = [42, 0, 2024]
    reruns = []
    for k, s in enumerate(seeds, 1):
        torch.manual_seed(s); np.random.seed(s)
        X_tr, X_te, y_tr, y_te = lab.load_data()
        model = lab.MLP(hidden=(128, 128), act="relu", dropout=0.0, use_bn=True)
        hist, dt = lab.run(model, X_tr, X_te, y_tr, y_te, opt_name="adam",
                           lr=0.001, epochs=30, wd=0.0)
        acc = hist["acc"][-1] * 100
        reruns.append({"seed": s, "acc": round(acc, 2), "time": round(dt, 2)})
        if k == 1:  # 用第1次复测的图作为组8代表图
            lab.save_curve(hist, "result_exp8_run1.png",
                           f"exp8 run{k} (seed={s}): acc={acc:.2f}%", acc_only=True)
        print(f"[exp8 rerun {k}/3] seed={s}: acc={acc:.2f}%  time={dt:.1f}s")

    # 3) 失败实验：lr=10.0（基线其余配置不变）
    r = run_once("lr_too_big", (32,), "sigmoid", "sgd", 10.0, 0.0, 0.0, False,
                 seed=42)
    r["note"] = "失败实验 lr=10.0"
    results.append(r)
    print(f"[lr_too_big] acc={r['acc']:.2f}%  loss_last={r['loss']:.4g}  time={r['time']}s")

    # 4) 学习率扫描：0.1 / 1.0 / 5.0 / 10.0 / 20.0（基线，无图）
    scan = []
    for lr in [0.1, 1.0, 5.0, 10.0, 20.0]:
        r = run_once(f"lrscan_{lr}", (32,), "sigmoid", "sgd", lr, 0.0, 0.0,
                     False, seed=42, save_fig=False)
        r["lr"] = lr
        scan.append(r)
        print(f"[lr scan] lr={lr}: acc={r['acc']:.2f}%  loss_last={r['loss']:.4g}")

    summary = {
        "data": "load_digits, 8:2 stratify, random_state=42, epochs=30 full-batch",
        "groups": results,
        "exp8_reruns": reruns,
        "exp8_avg_acc": round(float(np.mean([x["acc"] for x in reruns])), 2),
        "lr_scan": scan,
    }
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("\n=== 汇总表 ===")
    print("| 组号 | 实验名称 | 测试准确率(%) | 训练耗时(s) | 末次损失 |")
    print("|---|---|---|---|---|")
    order = ["baseline", "exp1", "exp2", "exp3", "exp4", "exp5",
             "exp6", "exp7", "exp8", "lr_too_big"]
    for tag in order:
        r = next(x for x in results if x["tag"] == tag)
        print(f"| {r['note']} | {r['acc']} | {r['time']} | {r['loss']:.4g} |")
    print("| 最优组合复测 | " + " / ".join(f"seed{s}:{r['acc']}" for r in reruns)
          + f" | 平均 {summary['exp8_avg_acc']} | - | - |")


if __name__ == "__main__":
    main()
