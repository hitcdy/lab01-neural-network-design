# 大模型课程 · 实验作业一：使用神经网络设计更好的分类器（load_digits）

《人工智能——深度学习大模型智能体》配套实验作业一（对应教材第 2 章《神经元与神经网络》）。
本作业在本机 CPU 环境下用 PyTorch 完成（按要求未安装 TRAE IDE，AI 协作由通用 AI 编程助手完成）。

## 实验结论速览

| 组号 | 实验 | 改动 | 测试准确率 | 说明 |
|---|---|---|---|---|
| 0 | 基线 | 1×32 Sigmoid + SGD(0.1) | 22.22% | 能学但学不好 |
| 1 | 换激活函数 | Sigmoid→ReLU | 47.50% | 缓解梯度消失 |
| 2 | 加深网络 | 2 层×128（Sigmoid） | 7.22% | 梯度消失+欠训练，反低于随机 |
| 3 | 换优化器 | SGD→Adam(0.01) | 82.22% | 自适应学习率加速收敛 |
| 4 | 调学习率 | 0.1→0.01 | 10.00% | 学习率过小，几乎不学习 |
| 5 | L2 正则 | wd=1e-4 | 22.22% | 对欠拟合模型无收益 |
| 6 | Dropout | p=0.2 | 21.39% | 略降 |
| 7 | BatchNorm | 隐藏层后 BatchNorm1d | 79.17% | 稳定训练，大幅提升 |
| 8 | 最优组合 | ReLU+2×128+BN+Adam(0.001) | 97.22% | 3 次复测平均 95.93% |
| — | 失败实验 | lr=10.0 | 36.94% | 损失震荡不收敛（发散临界点约在 lr=10~20） |

数据：sklearn `load_digits`（1797 样本，8:2 分层划分，random_state=42，30 epoch 全批量）。

## 目录结构

- `学号_姓名_实验作业一.docx` — 完整实验报告（基于课程样板填写，学号/姓名待学生填写）
- `verify_env.py` — 环境验证脚本
- `mlp_digits.py` — 可配置实验框架（MLP 类 + 训练/评估/画图）
- `run_experiments.py` — 批量运行全部对照实验（组 0–8、复测、失败组、lr 扫描）
- `fill_report.py` — 生成报告 docx 的填写脚本（辅助）
- `result_*.png` — 各组损失/准确率曲线图（图 1~图 10）
- `results.json` / `traces.json` — 汇总结果与逐 epoch 数据

## 复现方式

```bash
python -m venv venv
venv\Scripts\activate            # Windows；macOS/Linux: source venv/bin/activate
pip install torch scikit-learn matplotlib numpy
python verify_env.py             # 环境检查
python mlp_digits.py             # 单组运行（默认基线，可用参数切换）
python run_experiments.py        # 一键跑完全部实验并生成结果与曲线图
```
