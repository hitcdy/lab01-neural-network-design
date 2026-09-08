# -*- coding: utf-8 -*-
"""验证 PyTorch / scikit-learn / Matplotlib 环境是否可用。"""
import torch, sklearn, matplotlib, numpy as np
print("PyTorch     :", torch.__version__)
print("scikit-learn:", sklearn.__version__)
print("NumPy       :", np.__version__)
print("Matplotlib  :", matplotlib.__version__)
print("CUDA 可用   :", torch.cuda.is_available())  # 无 GPU 显示 False 也可正常完成本实验
