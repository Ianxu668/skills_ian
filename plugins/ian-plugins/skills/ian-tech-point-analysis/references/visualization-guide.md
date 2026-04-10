# 技术可视化指南

## 图表类型选择

### 原理说明类
| 图表类型 | 适用场景 | 工具建议 |
|---------|---------|---------|
| 系统框图 | 展示组件关系 | SVG + CSS |
| 流程图 | 算法/工作流程 | SVG |
| 时序图 | 信号时序关系 | SVG/TikZ |
| 状态图 | 状态转换 | SVG |

### 数据分析类
| 图表类型 | 适用场景 | 工具建议 |
|---------|---------|---------|
| 曲线图 | 性能随参数变化 | Chart.js/D3.js |
| 柱状图 | 对比不同方案 | Chart.js |
| 散点图 | 相关性分析 | Chart.js |
| 热力图 | 参数敏感性分析 | D3.js |

### 结构展示类
| 图表类型 | 适用场景 | 工具建议 |
|---------|---------|---------|
| 剖面图 | 内部结构展示 | SVG |
| 3D示意图 | 空间关系 | Three.js (简化) |
| 装配图 | 零件装配关系 | SVG |
| 应力云图 | FEA结果展示 | 外部工具生成PNG |

## SVG 绘制规范

### 基础模板
```svg
<svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
  <!-- 定义样式 -->
  <defs>
    <style>
      .component { fill: #f0f0f0; stroke: #333; stroke-width: 2; }
      .signal { stroke: #0066cc; stroke-width: 2; marker-end: url(#arrow); }
      .label { font-family: Arial; font-size: 14px; }
    </style>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#0066cc"/>
    </marker>
  </defs>

  <!-- 图形内容 -->
</svg>
```

### 配色方案
```css
/* 技术图表配色 */
--primary: #2c3e50;      /* 主色：深蓝灰 */
--secondary: #3498db;    /* 次色：亮蓝 */
--accent: #e74c3c;       /* 强调：红色 */
--success: #27ae60;      /* 成功：绿色 */
--warning: #f39c12;      /* 警告：橙色 */
--background: #f8f9fa;   /* 背景：浅灰 */
--text: #333333;         /* 文字：深灰 */
```

## 动画设计原则

### 适用场景
- 信号流向演示
- 算法迭代过程
- 机械运动仿真
- 数据流转换

### 技术实现
```html
<!-- CSS 动画示例：信号流动 -->
<style>
  .signal-flow {
    stroke-dasharray: 10;
    animation: flow 1s linear infinite;
  }
  @keyframes flow {
    to { stroke-dashoffset: -20; }
  }
</style>
```

### 交互设计
- 鼠标悬停显示详细信息
- 滑块控制参数变化
- 点击展开/收起详情
- 步骤式演示（下一步/上一步）

## 公式渲染

### MathJax 集成
```html
<!-- 在 HTML 中渲染公式 -->
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

<!-- 行内公式 -->
<p>应变公式: \( \frac{\Delta R}{R} = K \cdot \varepsilon \)</p>

<!-- 独立公式 -->
$$ \sigma = E \cdot \varepsilon $$
```

## 图表最佳实践

### 清晰度
- 线条粗细适中（1.5-2px）
- 字体大小一致（12-14px）
- 足够的留白
- 避免过度装饰

### 可读性
- 重要信息高亮
- 图例清晰完整
- 坐标轴标注明确
- 单位不能遗漏

### 一致性
- 同类型图表风格统一
- 颜色使用有逻辑
- 符号定义一致
- 布局规范统一

## 推荐工具链

### 代码绘制
- **SVG**: 手动编写或使用 SVG 编辑器
- **D3.js**: 复杂数据可视化
- **Chart.js**: 标准图表快速生成
- **Mermaid.js**: 流程图、时序图

### 外部工具
- **Figma**: UI/矢量设计
- **Blender**: 3D模型（导出SVG）
- **MATLAB/Python**: 科学计算图表
- **LaTeX/TikZ**: 学术论文级图表

### 在线服务
- **Wolfram Alpha**: 公式验证
- **Desmos**: 函数可视化
- **GeoGebra**: 几何图形
