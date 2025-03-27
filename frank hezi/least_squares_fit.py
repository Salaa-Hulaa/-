"""
最小二乘法拟合与参数不确定度计算工具

本程序用于：
1. 对一组(x,y)数据进行线性最小二乘法拟合
2. 计算拟合参数（斜率和截距）及其不确定度
3. 可视化拟合结果和不确定度范围

作者: Cascade
日期: 2025-03-26
"""

import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy import stats

class LeastSquaresFitApp:
    def __init__(self, root):
        self.root = root
        self.root.title("最小二乘法拟合与参数不确定度计算工具")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("微软雅黑", 10))
        self.style.configure("TLabel", font=("微软雅黑", 10))
        
        # 数据存储
        self.x_values = []
        self.y_values = []
        self.data_ids = []
        self.next_id = 1
        
        # 拟合结果
        self.slope = None  # 斜率a
        self.intercept = None  # 截距b
        self.slope_uncertainty = None  # 斜率不确定度
        self.intercept_uncertainty = None  # 截距不确定度
        self.r_squared = None  # 相关系数R²
        self.residual_std = None  # 残差标准差
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧输入区域
        input_frame = ttk.LabelFrame(main_frame, text="数据输入", padding="10")
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # X值输入
        x_frame = ttk.Frame(input_frame)
        x_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(x_frame, text="X值:").pack(side=tk.LEFT)
        self.x_entry = ttk.Entry(x_frame)
        self.x_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Y值输入
        y_frame = ttk.Frame(input_frame)
        y_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(y_frame, text="Y值:").pack(side=tk.LEFT)
        self.y_entry = ttk.Entry(y_frame)
        self.y_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 添加按钮
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="添加数据", command=self.add_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除选中", command=self.delete_selected_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除所有", command=self.clear_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="拟合数据", command=self.fit_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存图表", command=self.save_plot).pack(side=tk.LEFT, padx=5)
        
        # 数据显示区域
        data_display_frame = ttk.Frame(input_frame)
        data_display_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(data_display_frame, text="已输入的数据:").pack(anchor=tk.W)
        
        # 创建表格
        columns = ("ID", "X值", "Y值")
        self.data_tree = ttk.Treeview(data_display_frame, columns=columns, show="headings", height=15, selectmode="extended")
        
        # 设置列标题
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=80)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(data_display_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加表格右键菜单
        self.context_menu = tk.Menu(self.data_tree, tearoff=0)
        self.context_menu.add_command(label="删除选中项", command=self.delete_selected_data)
        self.context_menu.add_command(label="清除所有数据", command=self.clear_data)
        
        # 绑定右键菜单
        self.data_tree.bind("<Button-3>", self.show_context_menu)
        
        # 右侧结果和可视化区域
        result_frame = ttk.LabelFrame(main_frame, text="拟合结果与可视化", padding="10")
        result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 创建matplotlib图形
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_xlabel('X', fontsize=10)
        self.ax.set_ylabel('Y', fontsize=10)
        self.ax.set_title('最小二乘法拟合', fontsize=12)
        
        # 嵌入图形到tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=result_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 添加matplotlib工具栏
        toolbar_frame = ttk.Frame(result_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
        
        # 拟合结果显示区域
        self.result_text = scrolledtext.ScrolledText(result_frame, height=8, wrap=tk.WORD)
        self.result_text.pack(fill=tk.X, pady=10)
        
        # 公式说明区域
        formula_frame = ttk.LabelFrame(result_frame, text="最小二乘法拟合公式", padding="10")
        formula_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        formula_text = scrolledtext.ScrolledText(formula_frame, height=10, wrap=tk.WORD)
        formula_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加公式说明
        formulas = """
1. 最小二乘法拟合参数:
   - 斜率a = [n∑(xy) - ∑x∑y] / [n∑(x²) - (∑x)²]
   - 截距b = [∑y - a∑x] / n

2. 参数不确定度:
   - 残差平方和S = ∑(yi - (axi + b))²
   - 标准偏差σ = √[S/(n-2)]
   - 斜率a的不确定度ua = σ·√[n / (n∑(x²) - (∑x)²)]
   - 截距b的不确定度ub = σ·√[∑(x²) / (n∑(x²) - (∑x)²)]

3. 相关系数:
   - R² = 1 - [∑(yi - (axi + b))² / ∑(yi - ȳ)²]

4. 最终结果表示:
   - y = (a ± ua)x + (b ± ub)
        """
        formula_text.insert(tk.END, formulas)
        formula_text.configure(state="disabled")
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        # 先选中鼠标右键点击的项
        item = self.data_tree.identify_row(event.y)
        if item:
            self.data_tree.selection_set(item)
        
        # 显示右键菜单
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def add_data(self):
        """添加数据到列表"""
        try:
            x_value = float(self.x_entry.get())
            y_value = float(self.y_entry.get())
            
            # 添加到数据列表
            self.x_values.append(x_value)
            self.y_values.append(y_value)
            
            # 记录数据ID
            data_id = self.next_id
            self.data_ids.append(data_id)
            self.next_id += 1
            
            # 更新表格
            self.data_tree.insert("", tk.END, values=(data_id, x_value, y_value))
            
            # 清空输入框
            self.x_entry.delete(0, tk.END)
            self.y_entry.delete(0, tk.END)
            self.x_entry.focus()
            
            # 更新散点图
            self.update_scatter_plot()
            
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数值")
    
    def delete_selected_data(self):
        """删除选中的数据项"""
        selected_items = self.data_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择要删除的数据")
            return
        
        # 确认删除
        if messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selected_items)} 项数据吗？"):
            for item in selected_items:
                # 获取数据ID
                data_id = int(self.data_tree.item(item, "values")[0])
                
                # 查找数据在列表中的索引
                try:
                    idx = self.data_ids.index(data_id)
                    
                    # 从数据列表中删除
                    del self.x_values[idx]
                    del self.y_values[idx]
                    del self.data_ids[idx]
                    
                    # 从表格中删除
                    self.data_tree.delete(item)
                except ValueError:
                    continue
            
            # 更新散点图
            self.update_scatter_plot()
            
            # 清空结果区域
            self.result_text.delete(1.0, tk.END)
            
            # 重置拟合结果
            self.slope = None
            self.intercept = None
            self.slope_uncertainty = None
            self.intercept_uncertainty = None
            self.r_squared = None
            self.residual_std = None
    
    def clear_data(self):
        """清除所有数据"""
        # 确认清除
        if messagebox.askyesno("确认清除", "确定要清除所有数据吗？"):
            # 清空数据
            self.x_values = []
            self.y_values = []
            self.data_ids = []
            self.next_id = 1
            
            # 清空表格
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            # 清空图表
            self.ax.clear()
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.ax.set_xlabel('X', fontsize=10)
            self.ax.set_ylabel('Y', fontsize=10)
            self.ax.set_title('最小二乘法拟合', fontsize=12)
            self.canvas.draw()
            
            # 清空结果
            self.result_text.delete(1.0, tk.END)
            
            # 重置拟合结果
            self.slope = None
            self.intercept = None
            self.slope_uncertainty = None
            self.intercept_uncertainty = None
            self.r_squared = None
            self.residual_std = None
    
    def update_scatter_plot(self):
        """更新散点图"""
        # 清除旧图
        self.ax.clear()
        
        if self.x_values and self.y_values:
            # 绘制散点图
            self.ax.scatter(self.x_values, self.y_values, color='blue', marker='o')
        
        # 设置图表属性
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_xlabel('X', fontsize=10)
        self.ax.set_ylabel('Y', fontsize=10)
        self.ax.set_title('最小二乘法拟合', fontsize=12)
        
        # 更新画布
        self.canvas.draw()
    
    def fit_data(self):
        """使用最小二乘法拟合数据"""
        if len(self.x_values) < 2:
            messagebox.showwarning("数据不足", "至少需要2个数据点才能进行拟合")
            return
        
        try:
            # 转换为numpy数组
            x_array = np.array(self.x_values)
            y_array = np.array(self.y_values)
            n = len(x_array)
            
            # 使用scipy.stats进行线性回归
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_array, y_array)
            
            # 计算拟合值
            y_fit = slope * x_array + intercept
            
            # 计算残差
            residuals = y_array - y_fit
            
            # 计算残差平方和
            residual_sum_squares = np.sum(residuals**2)
            
            # 计算残差标准差
            residual_std = np.sqrt(residual_sum_squares / (n - 2))
            
            # 计算斜率的不确定度
            sum_x = np.sum(x_array)
            sum_x_squared = np.sum(x_array**2)
            denominator = n * sum_x_squared - sum_x**2
            
            slope_uncertainty = residual_std * np.sqrt(n / denominator)
            
            # 计算截距的不确定度
            intercept_uncertainty = residual_std * np.sqrt(sum_x_squared / denominator)
            
            # 计算R²
            r_squared = r_value**2
            
            # 保存结果
            self.slope = slope
            self.intercept = intercept
            self.slope_uncertainty = slope_uncertainty
            self.intercept_uncertainty = intercept_uncertainty
            self.r_squared = r_squared
            self.residual_std = residual_std
            
            # 显示结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"拟合方程: Y = ({slope:.6f} ± {slope_uncertainty:.6f})X + ({intercept:.6f} ± {intercept_uncertainty:.6f})\n\n")
            self.result_text.insert(tk.END, f"斜率(a): {slope:.6f} ± {slope_uncertainty:.6f}\n")
            self.result_text.insert(tk.END, f"截距(b): {intercept:.6f} ± {intercept_uncertainty:.6f}\n")
            self.result_text.insert(tk.END, f"相关系数(R²): {r_squared:.6f}\n")
            self.result_text.insert(tk.END, f"残差标准差(σ): {residual_std:.6f}\n")
            
            # 更新图表
            self.update_fit_plot(x_array, y_array, slope, intercept, slope_uncertainty, intercept_uncertainty)
            
        except Exception as e:
            messagebox.showerror("计算错误", f"拟合过程中出现错误: {str(e)}")
    
    def update_fit_plot(self, x_array, y_array, slope, intercept, slope_uncertainty, intercept_uncertainty):
        """更新拟合图"""
        # 清除旧图
        self.ax.clear()
        
        # 绘制散点图
        self.ax.scatter(x_array, y_array, color='blue', marker='o', label='数据点')
        
        # 为了绘制平滑的拟合线，创建更多的点
        x_min, x_max = min(x_array), max(x_array)
        x_fit = np.linspace(x_min - 0.1 * (x_max - x_min), x_max + 0.1 * (x_max - x_min), 100)
        y_fit = slope * x_fit + intercept
        
        # 绘制拟合线
        self.ax.plot(x_fit, y_fit, color='red', linewidth=2, label='拟合直线')
        
        # 绘制不确定度范围
        # 上边界：(slope + slope_uncertainty) * x + (intercept + intercept_uncertainty)
        # 下边界：(slope - slope_uncertainty) * x + (intercept - intercept_uncertainty)
        y_upper = (slope + slope_uncertainty) * x_fit + (intercept + intercept_uncertainty)
        y_lower = (slope - slope_uncertainty) * x_fit + (intercept - intercept_uncertainty)
        
        self.ax.fill_between(x_fit, y_lower, y_upper, color='green', alpha=0.2, label='不确定度范围')
        
        # 设置图表属性
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_xlabel('X', fontsize=10)
        self.ax.set_ylabel('Y', fontsize=10)
        self.ax.set_title('最小二乘法拟合', fontsize=12)
        self.ax.legend(fontsize=9)
        
        # 更新画布
        self.canvas.draw()
    
    def save_plot(self):
        """保存图表为图片"""
        if not self.x_values:
            messagebox.showwarning("无数据", "没有数据可以保存")
            return
        
        # 保存图表
        import os
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'least_squares_fit.png')
        self.fig.savefig(save_path, dpi=300, bbox_inches='tight')
        messagebox.showinfo("保存成功", f"图表已保存为:\n{save_path}")

def main():
    root = tk.Tk()
    app = LeastSquaresFitApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
