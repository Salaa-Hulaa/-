"""
不确定度计算工具

本程序用于计算一组数据的不确定度，包括：
1. A类不确定度（统计不确定度）
2. B类不确定度（仪器不确定度）
3. 合成不确定度
4. 扩展不确定度

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

class UncertaintyCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("数据不确定度计算工具")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("微软雅黑", 10))
        self.style.configure("TLabel", font=("微软雅黑", 10))
        
        # 数据存储
        self.data_values = []
        self.data_ids = []
        self.next_id = 1
        
        # 不确定度结果
        self.ua = None  # A类不确定度
        self.ub = None  # B类不确定度
        self.uc = None  # 合成不确定度
        self.ue = None  # 扩展不确定度
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧输入区域
        input_frame = ttk.LabelFrame(main_frame, text="数据输入", padding="10")
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 数据输入
        data_frame = ttk.Frame(input_frame)
        data_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(data_frame, text="数据值:").pack(side=tk.LEFT)
        self.data_entry = ttk.Entry(data_frame)
        self.data_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 仪器精度输入
        instrument_frame = ttk.Frame(input_frame)
        instrument_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(instrument_frame, text="仪器精度:").pack(side=tk.LEFT)
        self.instrument_entry = ttk.Entry(instrument_frame)
        self.instrument_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.instrument_entry.insert(0, "0.0")  # 默认值
        
        # 置信系数输入
        confidence_frame = ttk.Frame(input_frame)
        confidence_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(confidence_frame, text="置信系数k:").pack(side=tk.LEFT)
        self.confidence_entry = ttk.Entry(confidence_frame)
        self.confidence_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.confidence_entry.insert(0, "2.0")  # 默认值为2，对应约95%置信度
        
        # 分布类型选择
        distribution_frame = ttk.Frame(input_frame)
        distribution_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(distribution_frame, text="B类不确定度分布:").pack(side=tk.LEFT)
        self.distribution_var = tk.StringVar(value="均匀分布")
        distribution_combobox = ttk.Combobox(distribution_frame, 
                                            textvariable=self.distribution_var,
                                            values=["均匀分布", "正态分布", "三角分布"])
        distribution_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        distribution_combobox.state(["readonly"])
        
        # 添加按钮
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="添加数据", command=self.add_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除选中", command=self.delete_selected_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除所有", command=self.clear_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="计算不确定度", command=self.calculate_uncertainty).pack(side=tk.LEFT, padx=5)
        
        # 数据显示区域
        data_display_frame = ttk.Frame(input_frame)
        data_display_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(data_display_frame, text="已输入的数据:").pack(anchor=tk.W)
        
        # 创建表格
        columns = ("ID", "数据值")
        self.data_tree = ttk.Treeview(data_display_frame, columns=columns, show="headings", height=10, selectmode="extended")
        
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
        result_frame = ttk.LabelFrame(main_frame, text="结果与可视化", padding="10")
        result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 结果显示区域
        self.result_text = scrolledtext.ScrolledText(result_frame, height=10, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 公式说明区域
        formula_frame = ttk.LabelFrame(result_frame, text="不确定度计算公式", padding="10")
        formula_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        formula_text = scrolledtext.ScrolledText(formula_frame, height=10, wrap=tk.WORD)
        formula_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加公式说明
        formulas = """
1. A类不确定度（统计不确定度）:
   u_A = s / √n
   其中，s为样本标准差，n为样本数量

2. 样本标准差:
   s = √[Σ(x_i - x̄)² / (n-1)]
   其中，x_i为每个数据点，x̄为样本均值

3. B类不确定度（仪器不确定度）:
   - 均匀分布: u_B = a / √3
   - 正态分布: u_B = a / 3
   - 三角分布: u_B = a / √6
   其中，a为仪器精度的半宽度

4. 合成不确定度:
   u_c = √(u_A² + u_B²)

5. 扩展不确定度:
   U = k × u_c
   其中，k为置信系数（通常取k=2，对应约95%置信水平）
        """
        formula_text.insert(tk.END, formulas)
        formula_text.configure(state="disabled")
        
        # 创建matplotlib图形
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_title('数据分布与不确定度', fontsize=12)
        
        # 嵌入图形到tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=result_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 添加matplotlib工具栏
        toolbar_frame = ttk.Frame(result_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
    
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
            value = float(self.data_entry.get())
            
            # 添加到数据列表
            self.data_values.append(value)
            
            # 记录数据ID
            data_id = self.next_id
            self.data_ids.append(data_id)
            self.next_id += 1
            
            # 更新表格
            self.data_tree.insert("", tk.END, values=(data_id, value))
            
            # 清空输入框
            self.data_entry.delete(0, tk.END)
            self.data_entry.focus()
            
            # 更新图表
            self.update_plot()
            
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
                    del self.data_values[idx]
                    del self.data_ids[idx]
                    
                    # 从表格中删除
                    self.data_tree.delete(item)
                except ValueError:
                    continue
            
            # 更新图表
            self.update_plot()
            
            # 清空结果区域
            self.result_text.delete(1.0, tk.END)
            
            # 重置不确定度结果
            self.ua = None
            self.ub = None
            self.uc = None
            self.ue = None
    
    def clear_data(self):
        """清除所有数据"""
        # 确认清除
        if messagebox.askyesno("确认清除", "确定要清除所有数据吗？"):
            # 清空数据
            self.data_values = []
            self.data_ids = []
            self.next_id = 1
            
            # 清空表格
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            # 清空图表
            self.ax.clear()
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.ax.set_title('数据分布与不确定度', fontsize=12)
            self.canvas.draw()
            
            # 清空结果
            self.result_text.delete(1.0, tk.END)
            
            # 重置不确定度结果
            self.ua = None
            self.ub = None
            self.uc = None
            self.ue = None
    
    def update_plot(self):
        """更新数据分布图"""
        if not self.data_values:
            self.ax.clear()
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.ax.set_title('数据分布与不确定度', fontsize=12)
            self.canvas.draw()
            return
        
        # 清除旧图
        self.ax.clear()
        
        # 绘制数据分布直方图
        self.ax.hist(self.data_values, bins='auto', alpha=0.7, color='skyblue', edgecolor='black')
        
        # 绘制均值线
        mean_value = np.mean(self.data_values)
        self.ax.axvline(mean_value, color='red', linestyle='--', linewidth=2, label=f'均值: {mean_value:.4f}')
        
        # 如果已计算不确定度，绘制不确定度范围
        if self.uc is not None:
            self.ax.axvline(mean_value - self.ue, color='green', linestyle=':', linewidth=2, 
                           label=f'扩展不确定度范围: ±{self.ue:.4f}')
            self.ax.axvline(mean_value + self.ue, color='green', linestyle=':', linewidth=2)
        
        # 设置图表属性
        self.ax.set_xlabel('数据值')
        self.ax.set_ylabel('频数')
        self.ax.set_title('数据分布与不确定度', fontsize=12)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.legend()
        
        # 更新画布
        self.canvas.draw()
    
    def calculate_uncertainty(self):
        """计算不确定度"""
        if len(self.data_values) < 2:
            messagebox.showwarning("数据不足", "至少需要2个数据点才能计算不确定度")
            return
        
        try:
            # 获取仪器精度和置信系数
            instrument_precision = float(self.instrument_entry.get())
            confidence_factor = float(self.confidence_entry.get())
            
            # 计算A类不确定度
            data_array = np.array(self.data_values)
            mean_value = np.mean(data_array)
            std_dev = np.std(data_array, ddof=1)  # 样本标准差，ddof=1表示无偏估计
            n = len(data_array)
            ua = std_dev / np.sqrt(n)
            
            # 计算B类不确定度
            distribution = self.distribution_var.get()
            if distribution == "均匀分布":
                ub = instrument_precision / np.sqrt(3)
            elif distribution == "正态分布":
                ub = instrument_precision / 3
            elif distribution == "三角分布":
                ub = instrument_precision / np.sqrt(6)
            else:
                ub = instrument_precision / np.sqrt(3)  # 默认使用均匀分布
            
            # 计算合成不确定度
            uc = np.sqrt(ua**2 + ub**2)
            
            # 计算扩展不确定度
            ue = confidence_factor * uc
            
            # 保存结果
            self.ua = ua
            self.ub = ub
            self.uc = uc
            self.ue = ue
            
            # 显示结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"数据均值: {mean_value:.6f}\n")
            self.result_text.insert(tk.END, f"样本标准差: {std_dev:.6f}\n")
            self.result_text.insert(tk.END, f"样本数量: {n}\n\n")
            
            self.result_text.insert(tk.END, f"A类不确定度 (u_A): {ua:.6f}\n")
            self.result_text.insert(tk.END, f"B类不确定度 (u_B): {ub:.6f} ({distribution})\n")
            self.result_text.insert(tk.END, f"合成不确定度 (u_c): {uc:.6f}\n")
            self.result_text.insert(tk.END, f"扩展不确定度 (U=k×u_c): {ue:.6f} (k={confidence_factor})\n\n")
            
            self.result_text.insert(tk.END, f"最终测量结果表示为:\n")
            self.result_text.insert(tk.END, f"X = ({mean_value:.6f} ± {ue:.6f})")
            
            # 更新图表
            self.update_plot()
            
        except ValueError:
            messagebox.showerror("输入错误", "请确保仪器精度和置信系数为有效的数值")

def main():
    root = tk.Tk()
    app = UncertaintyCalculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
