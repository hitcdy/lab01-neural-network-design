# -*- coding: utf-8 -*-
"""
在《作业一_实验报告样板.docx》基础上填写完整实验报告：
- 删除所有"提示：…"行（第 4 节的提示改写为说明文字）
- 用真实文字替换下划线答题区
- 填写表 1~表 5 的数据
- 把 10 张曲线图插入对应"【在此插入图片】"单元格
输出：大模型目录下《学号_姓名_实验作业一.docx》（学号/姓名待学生填写后重命名）
"""
import copy
import os

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm
from docx.table import Table
from docx.text.paragraph import Paragraph

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(BASE), "作业一_实验报告样板.docx")
DST = os.path.join(os.path.dirname(BASE), "学号_姓名_实验作业一.docx")
FIG = lambda name: os.path.join(BASE, name)

doc = docx.Document(SRC)
body = doc.element.body

# ---------- 顺序收集顶层段落与表格 ----------
items = []  # (kind, obj)
for child in body.iterchildren():
    if child.tag == qn('w:p'):
        items.append(('p', Paragraph(child, doc)))
    elif child.tag == qn('w:tbl'):
        items.append(('t', Table(child, doc)))

def ptext(item):
    return item[1].text if item[0] == 'p' else ''

def is_underscore(item):
    return item[0] == 'p' and item[1].text.strip() and set(item[1].text.strip()) <= set('_')

def is_hint(item):
    return item[0] == 'p' and item[1].text.strip().startswith('提示：')

def set_para_text(p, text):
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    if text:
        p.add_run(text)

def delete_para(p):
    p._element.getparent().remove(p._element)

def set_cell_text(cell, text):
    paras = cell.paragraphs
    set_para_text(paras[0], text)
    for extra in paras[1:]:
        extra._element.getparent().remove(extra._element)

def add_img_to_cell(cell, path, width_cm):
    paras = cell.paragraphs
    for r in list(paras[0].runs):
        r._element.getparent().remove(r._element)
    paras[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    paras[0].add_run().add_picture(path, width=Cm(width_cm))
    for extra in paras[1:]:
        extra._element.getparent().remove(extra._element)

def fill_range_underscores(underscore_items, lines):
    """用内容段落替换答题区下划线：克隆首条下划线段落、逐条插入，再删除原下划线。"""
    ref = underscore_items[0][1]._element
    for line in lines:
        new_p = copy.deepcopy(ref)
        for r in new_p.findall(qn('w:r')):
            new_p.remove(r)
        ref.addprevious(new_p)
        Paragraph(new_p, doc).add_run(line)
    for it in underscore_items:
        delete_para(it[1])

# ============================================================
# 1) 提示行预处理：第 4 节提示改写为说明文字，其余提示全部删除
# ============================================================
AI_LEAD = ('说明：本实验按课程要求未安装 TRAE IDE，改用 ZCode AI 编程助手完成代码生成、'
           '修改与原理答疑。以下为真实协作记录：第 2 列给出提示词原文（摘要），第 3 列给出 '
           'AI 输出及我的采纳与修改；每一处 AI 代码均经通读、核对与修改后使用。')
for it in items:
    if is_hint(it):
        if '至少记录 3 处' in ptext(it):
            set_para_text(it[1], AI_LEAD)
        else:
            delete_para(it[1])

# ============================================================
# 2) 按标题锚点切分答题区，用内容替换下划线
# ============================================================
# (锚点搜索前缀, 回答内容行列表)
ZONES = [
    ('1.1', [
        '（1）理解人工神经元与多层感知器（MLP）的结构，掌握"加权和+偏置+激活函数"的计算过程与完整的训练流程（前向传播—损失计算—反向传播—参数更新）；',
        '（2）在 sklearn 手写数字数据集 load_digits 上，用 PyTorch 从零实现 MLP 分类器，通过控制变量对照实验考察激活函数、网络深度、优化器、学习率、L2 正则化、Dropout 与 BatchNorm 对模型性能的影响，最终组合出一个显著优于基线的"更好的神经网络"；',
        '（3）在 AI 编程助手的辅助下完成代码编写、批量实验编排与结果解读，养成"人机协作做实验"、如实记录并基于数据改进模型的习惯。',
    ]),
    ('2.3', [
        '训练损失从约 2.36 仅缓慢降到 2.29，几乎未显著下降；测试准确率前 20 个 epoch 一直停留在 10%（随机猜测水平），最后 10 个 epoch 才缓慢爬升，最终只有 22.22%。',
        '基线"能学但学不好"：Sigmoid 激活函数导数最大只有 0.25，单隐藏层在固定学习率 SGD(0.1) 下梯度更新缓慢，30 次全批量更新不足以让 64→32→10 的小网络有效拟合。',
        '损失与准确率曲线都表明：主要瓶颈在激活函数（梯度消失）与优化器/学习率组合，这正是后续逐项改进可以发挥作用的空间。',
    ]),
    ('3.1', [
        '改动动机：Sigmoid 在输入绝对值较大时进入饱和区、导数趋近 0，误差梯度逐层衰减；ReLU 在正区间导数为 1，可缓解梯度消失并加速收敛。',
        '结果：其余设置不变、仅把激活函数换成 ReLU，测试准确率从 22.22% 提高到 47.50%（约翻倍）；损失降到 2.17，准确率曲线全程单调上升（第 10/20/30 epoch 约 21%/40%/48%）。说明激活函数直接决定网络"能否有效学习"，但单层 32 神经元配 SGD(0.1) 的结构容量与训练效率仍有限。',
    ]),
    ('3.2', [
        '结果：把 1 层×32 加深为 2 层×128（仍为 Sigmoid），测试准确率不升反降：从 22.22% 跌到 7.22%，甚至低于随机猜测水平（10%）；训练损失也几乎不动（2.35→2.30）。',
        '原因：① 梯度消失更严重——两层 Sigmoid 的导数在反向传播中连乘（每层至多 ×0.25），误差信号很难传到较浅的层，权重得不到有效更新；② 参数量大增却只训练 30 个 epoch，模型严重欠训练，"容量大但没学会"。这组说明：在 Sigmoid + 固定小步长的前提下加大容量只会适得其反。',
    ]),
    ('3.3', [
        '改动动机：SGD 对所有参数使用同一个固定学习率；Adam 利用梯度的一阶矩（动量）与二阶矩估计为每个参数自适应调整步长。',
        '结果：换成 Adam(0.01) 后，第 10 个 epoch 测试准确率已从 10% 冲到约 71%，最终 82.22%（较基线提升约 60 个百分点），训练损失降到 1.24。可见在小数据、短训练条件下，优化器对收敛速度与精度的贡献远大于"加容量"，是收益最大的改进项之一。',
    ]),
    ('3.4', [
        '结果：学习率由 0.1 降到 0.01（其余同基线，SGD），30 个 epoch 内训练损失几乎不变（2.36→2.33），测试准确率全程 10.00%，相当于什么都没学到。',
        '解释：Sigmoid 网络的梯度本来就小，学习率再缩小 10 倍后每次更新的步长 η·∂L/∂w 微乎其微，无法走出初始区域。对比第 3 组：同样的 lr=0.01，SGD 完全学不动而 Adam 能到 82%，说明学习率的影响与优化器机制强耦合（详见思考题 2）。',
    ]),
    ('3.5', [
        '改动动机：L2 正则化（weight_decay）惩罚过大权重，期望缩小训练—测试差距、提高泛化。',
        '结果：weight_decay=1e-4 时准确率 22.22%，损失曲线与基线几乎重合，没有可见收益。原因：基线本身欠拟合（训练损失仍高、测试与训练阶段同步偏低、无明显训练—测试差距），此时正则化只会进一步压制本就不足的拟合能力；1e-4 的惩罚在 30 个 epoch 内作用也极弱。',
    ]),
    ('3.6', [
        '结果：加 Dropout（p=0.2）后测试准确率 21.39%，比基线 22.22% 略低；训练损失略高于基线（Dropout 训练时随机丢弃神经元、评估时关闭）。',
        '分析：Dropout 是抗过拟合手段（训练时随机失活、使网络不依赖个别神经元）。本实验基线欠拟合、容量本就不足、训练—测试差距很小，Dropout 反而减少了有效模型容量，故无正面收益——正则化应针对过拟合使用，对欠拟合模型应先解决拟合能力。',
    ]),
    ('3.7', [
        '结果：每个隐藏层后插入 BatchNorm1d（其余同基线，SGD(0.1)），测试准确率从 22.22% 大幅提升到 79.17%，训练损失降到 1.93，准确率曲线持续上升（第 10/20/30 epoch 约 13%/61%/79%）。',
        '分析：BatchNorm 对每批输入做零均值、单位方差归一化，再学习缩放 γ 与平移 β，缓解前层参数变化引起的"内部协变量偏移"，降低网络对初始化与学习率的敏感度、稳定梯度流；即使全批量更新（统计量即整批统计量），BN 依然显著加速训练，是收益最大的改进项之一。',
    ]),
    ('3.8', [
        '最优组合配置：ReLU + 2 层×128 神经元 + BatchNorm + Adam(0.001)，不另加 Dropout 与 L2（欠拟合阶段无必要）。',
        '单次运行（seed=42）测试准确率 97.22%、耗时约 0.14 s；固定数据划分、更换 torch 初始化种子复测 3 次为 97.22% / 95.00% / 95.56%，平均 95.93%（详见表 5），优于全部单项改进组（单项最高 82.22%）。原因：ReLU 消除梯度消失、BN 稳定训练、Adam 自适应步长、2×128 提供充足容量，四者叠加后 30 个 epoch 已能充分学习；1797 样本的小数据集上该容量尚不至于过拟合。',
        '结论：第 8 组验证各有效改进可以叠加——"更好的神经网络"来自训练机制（激活/优化/归一化）与合适容量的组合，而非单纯加层加宽。',
    ]),
    ('5.2', [
        '现象：学习率设为 10.0（其余同基线）后，训练损失不再单调下降而是大幅上下震荡，测试准确率在 10%~37% 之间来回跳动（第 10/20/30 epoch 约 27%/16%/37%），末次损失仍有 2.19，网络无法稳定收敛。',
        '解释：学习率过大时，每次更新的步长 η·∂L/∂w 太大，参数会"越过"损失谷底并在最优点两侧来回甩动，甚至被甩出稳定区域，故损失曲线呈锯齿状、无法落到谷底。',
        '发散临界点扫描（加分项）：在 lr=0.1/1.0/5.0/10.0/20.0 间扫描发现，lr=1.0 反而达 78.89%、5.0 为 64.72%，到 10.0 明显退化（36.94%）、20.0 跌回 10.28%（接近随机）——本设置下发散临界点约在 10~20 之间。原因是数据集极小且全批量只更新 30 步，较大的学习率能更快走出 Sigmoid 平坦区；这并不违背"学习率过大会发散"的一般规律，只是小数据、少步数下临界点大幅后移，是有价值的反直觉现象。',
    ]),
    ('5.3', [
        '（1）各设计维度在本实验中的有效性排序（30 epoch、CPU）：Adam（+60pt）≈ BatchNorm（+57pt）＞ ReLU（+25pt）＞ L2（无效）≈ Dropout（略负）＞ 加深网络（负）；"更好的神经网络"首先来自让训练有效进行的机制改进。',
        '（2）小数据集上"容量大"不等于"更好"：2×128 Sigmoid 网络因梯度消失 + 欠训练反降到 7.22%；只有先用 ReLU、BN、Adam 打通梯度、让训练真正推进，大容量才转化为 97% 的精度——容量与可训练性必须同时满足。',
        '（3）学习率是双刃剑且与优化器耦合：0.01 时 SGD 几乎不学（10.0%），10.0 时震荡不收敛（36.94%），而 Adam 在 0.001~0.01 都表现良好；实用中应优先配合自适应优化器并做学习率扫描。',
        '（4）控制变量法让结论可靠：9 组实验共用同一数据划分与随机种子、每组只改一个变量，每个因素的贡献都可归因；对"反直觉"结果（加深变差、lr=1.0 反而更好）如实记录并用原理分析，本身就是重要的实验结论。',
    ]),
    ('(1)', [
        '换用 ReLU 后收敛明显加快：同样 30 个 epoch，前 10 个 epoch 测试准确率已从约 10% 升到约 21%，最终达 47.50%，而 Sigmoid 基线只有 22.22%。数学原因：Sigmoid 的导数 σ′(x)=σ(x)(1−σ(x)) 最大只有 0.25，反向传播时误差梯度逐层与各层导数连乘，每过一层至多衰减为原来的 1/4，网络稍深梯度就指数级衰减（梯度消失），权重几乎得不到更新；ReLU 在正区间导数为 1，梯度可"原样"向前传播，负区间输出 0 还带来稀疏性，因此收敛更快、学得更好。',
    ]),
    ('(2)', [
        '不相同。SGD 对所有参数共用固定的全局学习率，lr 从 0.1 降到 0.01 使每次更新步长缩小为 1/10，叠加 Sigmoid 本身的小梯度，30 个 epoch 内参数几乎不动（测试准确率始终 10.00%）；Adam 为每个参数维护一阶矩与二阶矩估计，更新步长≈lr·m_t/(√v_t+ε) 已按梯度尺度归一化，名义学习率只起上限/缩放作用，梯度整体变小会被自适应项抵消，所以 lr=0.01 的 Adam 仍能收敛到 82.22%。可见"学习率的影响"必须结合优化器机制分析。',
    ]),
    ('(3)', [
        'BatchNorm 先对每批数据做零均值、单位方差归一化，再用可学习的 γ、β 恢复表达能力，使每层接收的输入分布保持稳定，缓解前层参数更新导致后层输入分布不断漂移的"内部协变量偏移"。分布稳定后，梯度不会因某层输出过大而爆炸、也不会过小，训练对学习率的敏感度下降，因此能"容忍"更大的学习率而不震荡发散。本实验中全批量 SGD(0.1) 加入 BatchNorm 后测试准确率从 22.22% 提升到 79.17%，正是该机制的体现。',
    ]),
    ('(4)', [
        '训练时 Dropout 以概率 p 随机丢弃神经元（对激活输出乘 0/1 掩码），若推理时不加处理，输出会整体变小、与训练期望不一致。PyTorch 采用 inverted dropout（反向缩放）：训练时把保留神经元的输出乘以 1/(1−p)，使每个神经元输出的期望与推理时一致；推理时 Dropout 层等价于恒等映射，使用全部神经元且不缩放。这样训练与推理的输出规模保持一致。',
    ]),
    ('(5)', [
        '本实验数据集只有 1797 个样本，"更大更深"的网络容量大、对训练数据表达能力（低偏差）更强，但样本不足时更容易拟合训练集中的个别噪声，方差上升、泛化变差；更直接的是在 30 次全批量更新下大网络严重欠训练，容量优势发挥不出来——实测 2×128 的 Sigmoid 网络准确率反而跌到 7.22%。只有先用 ReLU、BN、Adam 让梯度正常传播、训练真正推进，大容量才转化为收益（最优组合 97%）。用偏差—方差的语言说：小数据集上应在偏差与方差、容量与数据量之间取平衡，而不是一味加层加宽。',
    ]),
    ('(6)', [
        '本实验全程由我与 AI 编程助手分工完成（按课程要求可不安装 TRAE，协作方式与使用 TRAE 一致）。AI 最擅长"从想法到可运行代码"的转化：生成数据加载、模型定义、训练循环与画图框架，把 9 组控制变量实验批量编排成脚本，并解释梯度消失、BatchNorm、Adam 等原理——这些环节快且不易遗漏细节；必须由人来做的决策包括：实验设计是否符合"每组只改一个变量"、所有数字是否来自真实运行（编造数据该项 0 分）、最优组合如何取舍、以及把现象写成有依据的分析。我的体会：AI 是高效的执行者与资料库，人是负责任务定义、校验与解释的决策者；人机协作的价值在于把人从重复代码中解放出来去思考实验本身，前提是人必须能读懂并修改 AI 生成的每一行关键代码。',
    ]),
]

def find_anchors(defs):
    """为每个 (搜索前缀, 行) 找段落位置，返回按文档顺序的 (index, lines)。"""
    res = []
    for prefix, lines in defs:
        for i, item in enumerate(items):
            if item[0] == 'p' and ptext(item).strip().startswith(prefix):
                res.append((i, lines, prefix))
                break
    res.sort(key=lambda x: x[0])
    return res

anchors = find_anchors(ZONES)
for k, (idx, lines, prefix) in enumerate(anchors):
    end = anchors[k + 1][0] if k + 1 < len(anchors) else len(items)
    seg = items[idx + 1:end]
    underscores = [it for it in seg if is_underscore(it)]
    if underscores:
        fill_range_underscores(underscores, lines)

# ============================================================
# 3) 封面
# ============================================================
for it in items:
    if it[0] == 'p' and ptext(it).strip() == '完成日期：':
        set_para_text(it[1], '完成日期：2026 年 9 月 8 日')
    # 姓　　名：/ 学　　号：留待学生本人填写

# ============================================================
# 4) 标题微调：第 4 节不再强制出现 TRAE
# ============================================================
for it in items:
    if it[0] != 'p':
        continue
    t = ptext(it).strip()
    if t.startswith('4  AI 协作记录'):
        set_para_text(it[1], '4  AI 协作记录（AI 助手使用情况）')
    elif t.startswith('表 4'):
        set_para_text(it[1], '表 4  AI 协作过程记录')

# ============================================================
# 5) 表格数据
# ============================================================
tables = [it[1] for it in items if it[0] == 't']
def find_table(head0):
    for tb in tables:
        if tb.rows and tb.rows[0].cells[0].text.strip() == head0:
            return tb
    return None

# 表 1 实验环境清单
env = find_table('类别')
set_cell_text(env.rows[1].cells[1], 'Windows 11（版本 10.0.26200）')
set_cell_text(env.rows[1].cells[2], 'CPU 环境，无独立显卡')
set_cell_text(env.rows[2].cells[1], '3.14.6（64 位，满足 ≥3.10）')
set_cell_text(env.rows[3].cells[1], '2.14.0+cpu')
set_cell_text(env.rows[3].cells[2], 'CUDA 可用：否（verify_env.py 输出 False；CPU 训练单组不足 1 s）')
set_cell_text(env.rows[4].cells[1], 'scikit-learn 1.9.0 / NumPy 2.5.2 / Matplotlib 3.11.1')
set_cell_text(env.rows[5].cells[0], 'AI 编程助手')
set_cell_text(env.rows[5].cells[1], 'ZCode（对话式 AI 智能体）')
set_cell_text(env.rows[5].cells[2], '核心功能：对话答疑、代码生成/修改、批量运行实验（与 TRAE 同类，本实验未安装 TRAE IDE）')

# 表 2 基线模型配置
base = find_table('项目')
set_cell_text(base.rows[2].cells[1], '64 → 隐藏层 1×32（Sigmoid 激活） → 输出 10')
set_cell_text(base.rows[3].cells[1], 'SGD / 0.1')
set_cell_text(base.rows[5].cells[1], '无（weight_decay = 0，无 Dropout / BatchNorm）')

# 表 3 对照实验汇总（行 1~9 = 组 0~8，行 10 = 失败实验）
EXP3 = [
    ('22.22', '0.03', '能学但学不好：损失降幅小，准确率仅 22.22%'),
    ('47.50', '0.04', '收敛明显加快、准确率约翻倍，梯度消失缓解'),
    ('7.22',  '0.09', '梯度消失 + 欠训练，反低于随机水平（10%）'),
    ('82.22', '0.06', 'Adam 自适应学习率大幅加速收敛'),
    ('10.00', '0.04', '学习率过小，30 个 epoch 几乎不更新'),
    ('22.22', '0.03', '与基线相同：正则化对欠拟合模型无收益'),
    ('21.39', '0.07', '略降：欠拟合阶段 Dropout 削弱有限拟合能力'),
    ('79.17', '0.05', 'BN 稳定训练，准确率大幅提升（+57pt）'),
    ('97.22', '0.14', '组合全部有效改进，达到最优'),
]
cmp = find_table('组号')
for i, (acc, t, concl) in enumerate(EXP3, start=1):
    row = cmp.rows[i]
    set_cell_text(row.cells[3], acc)
    set_cell_text(row.cells[4], t)
    set_cell_text(row.cells[5], concl)
fail = cmp.rows[10]
set_cell_text(fail.cells[2], '学习率过大（lr = 10.0）')
set_cell_text(fail.cells[3], '36.94')
set_cell_text(fail.cells[4], '0.05')
set_cell_text(fail.cells[5], '损失震荡、准确率来回波动，无法稳定收敛')

# 表 4 AI 协作过程记录
AI4 = [
    ('1', '生成可配置的实验代码框架',
     '“创建 mlp_digits.py：用 PyTorch 实现 load_digits 手写数字 MLP 分类，数据 8:2 分层划分、随机种子 42、标签转 torch.long；模型隐藏层结构/激活函数/Dropout/BatchNorm 参数化；训练循环含前向、交叉熵损失、反向传播、参数更新，逐 epoch 记录训练损失与测试准确率，画图并打印最终准确率与耗时。”',
     'AI 输出完整可运行框架（数据加载、MLP 类、run 训练函数、画图函数）。我通读并逐段核对后，把它改造成命令行参数化入口，并拆分为"单组运行"（mlp_digits.py）与"批量实验"（run_experiments.py）两个脚本；确认分层划分、标签 Long 类型、超参可配置等关键点。'),
    ('2', '批量编排 9 组对照实验（控制变量）',
     '“把基线 + 8 组改进实验 + 失败组（lr=10.0）写成一个批量脚本：每组只改一个变量、共用同一数据划分与随机种子，曲线按 result_baseline.png、result_exp1.png……命名保存，并输出结果 JSON。”',
     'AI 生成 run_experiments.py（遍历配置字典依次运行并汇总）。我修正了最优组合结构为 ReLU + 2 层×128 + BatchNorm + Adam(0.001)，并自行补充了最优组合固定种子复测 3 次与 lr=0.1/1.0/5.0/10.0/20.0 扫描两段代码。'),
    ('3', '曲线与结果解读（原理答疑）',
     '“为什么把网络加深到 2 层×128（Sigmoid）后准确率反而跌到 7%？”、“lr=10.0 时损失剧烈震荡该怎样解释？”',
     'AI 从梯度消失（Sigmoid 导数 ≤0.25 逐层连乘）、容量大而欠训练、学习率过大导致参数在最优值附近"来回甩"等角度解释，并建议对照损失与准确率曲线验证。我逐条比对了逐 epoch 数据后采用，写进第 3、5 章；发散临界点（约 10~20 之间）按实测结果自行下结论。'),
    ('4（可选）', '绘图中文显示与代码细节',
     '“matplotlib 画出的图中文变成方框怎么办？”',
     'AI 提示设置 plt.rcParams["font.sans-serif"]=["Microsoft YaHei"] 与 axes.unicode_minus=False。我直接采用，并把字体设置与画图逻辑统一封装进 save_curve()，保证全部曲线图风格一致。'),
]
ai_t = find_table('序号')
for vals in AI4:
    for row in ai_t.rows[1:]:
        if row.cells[0].text.strip() == vals[0]:
            for c, v in enumerate(vals[1:], start=1):
                set_cell_text(row.cells[c], v)
            break

# 表 5 最优组合 3 次复测
r5 = find_table('运行次数')
vals5 = [('42', '97.22', '0.19'), ('0', '95.00', '0.14'), ('2024', '95.56', '0.18')]
for row, (seed, acc, t) in zip(r5.rows[1:4], vals5):
    set_cell_text(row.cells[1], seed)
    set_cell_text(row.cells[2], acc)
    set_cell_text(row.cells[3], t)
avg = r5.rows[4]
set_cell_text(avg.cells[1], '—')
set_cell_text(avg.cells[2], '95.93')
set_cell_text(avg.cells[3], '0.17')

# ============================================================
# 6) 基线结果一行
# ============================================================
for it in items:
    if it[0] == 'p' and ptext(it).strip().startswith('最终测试准确率'):
        set_para_text(it[1], '最终测试准确率：22.22 %　　　训练耗时：0.03 s')
        break

# ============================================================
# 7) 插图：插入到图题上方那个 1×1 占位表中
# ============================================================
CAP_FIG = {
    '图 1':  ('result_baseline.png', 14),
    '图 2':  ('result_exp1.png', 14),
    '图 3':  ('result_exp2.png', 14),
    '图 4':  ('result_exp3.png', 14),
    '图 5':  ('result_exp4.png', 14),
    '图 6':  ('result_exp5.png', 14),
    '图 7':  ('result_exp6.png', 14),
    '图 8':  ('result_exp7.png', 14),
    '图 9':  ('result_exp8_run1.png', 12),
    '图 10': ('result_lr_too_big.png', 14),
}
for i, item in enumerate(items):
    if item[0] == 'p':
        t = ptext(item).strip()
        for cap, (fname, w) in CAP_FIG.items():
            if t.startswith(cap):
                prev = items[i - 1]
                if prev[0] == 't' and len(prev[1].rows) == 1:
                    add_img_to_cell(prev[1].rows[0].cells[0], FIG(fname), w)
                break

doc.save(DST)
print('saved:', DST)
