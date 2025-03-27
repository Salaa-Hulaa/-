# 数据分析与可视化工具集

这个项目包含一系列用于数据分析和可视化的Python工具，主要用于物理实验数据处理。

## 功能模块

1. **电压-电流数据分析工具** (voltage_current_plot.py)
   - 输入电压和电流数据
   - 绘制电压-电流特性曲线
   - 数据拟合与分析

2. **最小二乘法拟合工具** (least_squares_fit.py)
   - 对(x,y)数据进行线性最小二乘法拟合
   - 计算拟合参数（斜率和截距）及其不确定度
   - 可视化拟合结果和不确定度范围

3. **不确定度计算工具** (uncertainty_calculator.py)
   - 计算A类不确定度（统计不确定度）
   - 计算B类不确定度（仪器不确定度）
   - 计算合成不确定度和扩展不确定度

## 环境配置

项目使用conda管理环境依赖。可以使用以下命令创建并激活环境：

```bash
# 创建环境
conda env create -f environment.yml

# 激活环境
conda activate data-analysis-env
```

## 运行程序

项目提供了批处理文件方便运行程序：

- `run_program.bat` - 运行电压-电流数据分析工具
- `run_voltage_current.bat` - 运行电压-电流数据分析工具

也可以直接运行Python脚本：

```bash
python voltage_current_plot.py
python least_squares_fit.py
python uncertainty_calculator.py
```
