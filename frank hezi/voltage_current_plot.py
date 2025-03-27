try:
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator
    from scipy import stats
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext, simpledialog
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import os
    from matplotlib.widgets import RectangleSelector
    import matplotlib.patches as patches
except ImportError:
    import sys
    import subprocess
    
    print("正在安装所需的库，请稍候...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy", "matplotlib", "scipy"])
    
    # 安装完成后重新导入
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator
    from scipy import stats
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext, simpledialog
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    import os
    from matplotlib.widgets import RectangleSelector
    import matplotlib.patches as patches

class ZoomPreviewWindow(tk.Toplevel):
    """缩放预览窗口类"""
    def __init__(self, parent, x_data, y_data, fit_line=None, x_min=None, x_max=None, y_min=None, y_max=None):
        super().__init__(parent)
        self.title("缩放预览")
        self.geometry("600x500")
        
        # 保存数据
        self.x_data = x_data
        self.y_data = y_data
        self.fit_line = fit_line
        
        # 创建图表
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # 绘制数据点
        self.ax.scatter(x_data, y_data, color='blue', marker='o', label='实验数据')
        
        # 如果有拟合线，绘制拟合线
        if fit_line is not None and len(fit_line) == len(x_data):
            self.ax.plot(x_data, fit_line, color='red', linewidth=2, label='拟合曲线')
        
        # 设置坐标轴范围
        if x_min is not None and x_max is not None and y_min is not None and y_max is not None:
            self.ax.set_xlim(x_min, x_max)
            self.ax.set_ylim(y_min, y_max)
        
        # 设置网格和标签
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_xlabel('电压 (V)', fontsize=10)
        self.ax.set_ylabel('电流 (nA)', fontsize=10)
        self.ax.set_title('缩放预览', fontsize=12)
        self.ax.legend(fontsize=9)
        
        # 添加坐标轴刻度
        self.ax.xaxis.set_minor_locator(MultipleLocator(0.1))
        self.ax.yaxis.set_minor_locator(MultipleLocator(0.1))
        
        # 嵌入图形到tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 添加工具栏
        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(fill=tk.X, padx=10)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
        
        # 添加关闭按钮
        close_button = ttk.Button(self, text="关闭", command=self.destroy)
        close_button.pack(pady=10)

class VoltageCurrentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("电压-电流数据分析工具")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("微软雅黑", 10))
        self.style.configure("TLabel", font=("微软雅黑", 10))
        
        # 数据存储
        self.voltages = []
        self.currents = []
        self.data_ids = []  # 存储数据ID，用于删除操作
        self.next_id = 1    # 下一个数据ID
        
        # 拟合结果存储
        self.fit_line = None
        self.slope = None
        self.intercept = None
        
        # 缩放选择器
        self.zoom_selector = None
        self.zoom_rect = None
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧输入区域
        input_frame = ttk.LabelFrame(main_frame, text="数据输入", padding="10")
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 电流输入 - 放在上方
        current_frame = ttk.Frame(input_frame)
        current_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(current_frame, text="电流 (nA):").pack(side=tk.LEFT)
        self.current_entry = ttk.Entry(current_frame)
        self.current_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 电压输入 - 放在下方
        voltage_frame = ttk.Frame(input_frame)
        voltage_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(voltage_frame, text="电压 (V):").pack(side=tk.LEFT)
        self.voltage_entry = ttk.Entry(voltage_frame)
        self.voltage_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 添加按钮
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="添加数据", command=self.add_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除选中", command=self.delete_selected_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除所有", command=self.clear_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="拟合数据", command=self.fit_and_plot).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存图表", command=self.save_plot).pack(side=tk.LEFT, padx=5)
        
        # 数据显示区域
        data_frame = ttk.Frame(input_frame)
        data_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(data_frame, text="已输入的数据:").pack(anchor=tk.W)
        
        # 创建表格
        columns = ("ID", "电压 (V)", "电流 (nA)")
        self.data_tree = ttk.Treeview(data_frame, columns=columns, show="headings", height=10, selectmode="extended")
        
        # 设置列标题
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=80)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=scrollbar.set)
        
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加表格右键菜单
        self.context_menu = tk.Menu(self.data_tree, tearoff=0)
        self.context_menu.add_command(label="删除选中项", command=self.delete_selected_data)
        self.context_menu.add_command(label="清除所有数据", command=self.clear_data)
        
        # 绑定右键菜单
        self.data_tree.bind("<Button-3>", self.show_context_menu)
        
        # 右侧图表区域
        plot_frame = ttk.LabelFrame(main_frame, text="数据可视化", padding="10")
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 创建matplotlib图形
        self.fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_xlabel('电压 (V)', fontsize=10)
        self.ax.set_ylabel('电流 (nA)', fontsize=10)
        self.ax.set_title('电压-电流特性曲线', fontsize=12)
        
        # 嵌入图形到tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加matplotlib工具栏
        toolbar_frame = ttk.Frame(plot_frame)
        toolbar_frame.pack(fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
        
        # 添加缩放按钮
        zoom_button_frame = ttk.Frame(plot_frame)
        zoom_button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(zoom_button_frame, text="启用区域缩放", command=self.enable_zoom_selection).pack(side=tk.LEFT, padx=5)
        ttk.Button(zoom_button_frame, text="打开缩放预览", command=self.open_zoom_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(zoom_button_frame, text="重置缩放", command=self.reset_zoom).pack(side=tk.LEFT, padx=5)
        
        # 拟合结果显示区域
        self.result_text = scrolledtext.ScrolledText(plot_frame, height=5, wrap=tk.WORD)
        self.result_text.pack(fill=tk.X, pady=10)
    
    def enable_zoom_selection(self):
        """启用区域缩放选择"""
        if not self.voltages:
            messagebox.showinfo("提示", "请先添加数据")
            return
        
        # 移除之前的选择器（如果有）
        if self.zoom_selector:
            self.zoom_selector.set_active(False)
            self.zoom_selector = None
        
        # 移除之前的矩形（如果有）
        if self.zoom_rect and self.zoom_rect in self.ax.patches:
            self.zoom_rect.remove()
            self.zoom_rect = None
            self.canvas.draw()
        
        # 创建新的选择器
        self.zoom_selector = RectangleSelector(
            self.ax, self.on_zoom_select,
            useblit=True,
            button=[1],  # 只使用鼠标左键
            minspanx=5, minspany=5,
            spancoords='pixels',
            interactive=True
        )
        
        messagebox.showinfo("区域缩放", "请在图表上拖动鼠标选择要缩放的区域")
    
    def on_zoom_select(self, eclick, erelease):
        """处理缩放区域选择"""
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        
        # 确保坐标有效
        if None in (x1, y1, x2, y2):
            return
        
        # 计算选择区域
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        
        # 移除之前的矩形（如果有）
        if self.zoom_rect and self.zoom_rect in self.ax.patches:
            self.zoom_rect.remove()
        
        # 添加高亮矩形
        self.zoom_rect = patches.Rectangle(
            (x_min, y_min), x_max - x_min, y_max - y_min,
            linewidth=1, edgecolor='green', facecolor='green', alpha=0.2
        )
        self.ax.add_patch(self.zoom_rect)
        self.canvas.draw()
        
        # 询问是否打开缩放预览
        if messagebox.askyesno("缩放预览", "是否打开选定区域的缩放预览？"):
            self.open_zoom_preview(x_min, x_max, y_min, y_max)
    
    def open_zoom_preview(self, x_min=None, x_max=None, y_min=None, y_max=None):
        """打开缩放预览窗口"""
        if not self.voltages:
            messagebox.showinfo("提示", "请先添加数据")
            return
        
        # 如果没有指定缩放范围，则使用用户输入
        if None in (x_min, x_max, y_min, y_max):
            # 如果有选择区域，使用选择区域
            if self.zoom_rect:
                x_min = self.zoom_rect.get_x()
                y_min = self.zoom_rect.get_y()
                width = self.zoom_rect.get_width()
                height = self.zoom_rect.get_height()
                x_max = x_min + width
                y_max = y_min + height
            else:
                # 否则让用户输入缩放范围
                x_min = simpledialog.askfloat("缩放范围", "请输入最小电压值 (V):", 
                                            initialvalue=min(self.voltages))
                x_max = simpledialog.askfloat("缩放范围", "请输入最大电压值 (V):", 
                                            initialvalue=max(self.voltages))
                y_min = simpledialog.askfloat("缩放范围", "请输入最小电流值 (nA):", 
                                            initialvalue=min(self.currents))
                y_max = simpledialog.askfloat("缩放范围", "请输入最大电流值 (nA):", 
                                            initialvalue=max(self.currents))
                
                if None in (x_min, x_max, y_min, y_max):
                    return
        
        # 创建并显示缩放预览窗口
        zoom_window = ZoomPreviewWindow(
            self.root, 
            self.voltages, 
            self.currents, 
            self.fit_line, 
            x_min, x_max, 
            y_min, y_max
        )
        zoom_window.focus_set()
    
    def reset_zoom(self):
        """重置缩放"""
        if not self.voltages:
            return
        
        # 移除选择器
        if self.zoom_selector:
            self.zoom_selector.set_active(False)
            self.zoom_selector = None
        
        # 移除矩形
        if self.zoom_rect and self.zoom_rect in self.ax.patches:
            self.zoom_rect.remove()
            self.zoom_rect = None
            self.canvas.draw()
        
        # 重置坐标轴范围
        self.ax.set_xlim(min(self.voltages) - 0.1, max(self.voltages) + 0.1)
        self.ax.set_ylim(min(self.currents) - 0.1, max(self.currents) + 0.1)
        self.canvas.draw()
    
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
        try:
            voltage = float(self.voltage_entry.get())
            current = float(self.current_entry.get())
            
            # 添加到数据列表
            self.voltages.append(voltage)
            self.currents.append(current)
            
            # 记录数据ID
            data_id = self.next_id
            self.data_ids.append(data_id)
            self.next_id += 1
            
            # 更新表格
            self.data_tree.insert("", tk.END, values=(data_id, voltage, current))
            
            # 清空输入框
            self.voltage_entry.delete(0, tk.END)
            self.current_entry.delete(0, tk.END)
            self.voltage_entry.focus()
            
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
                    del self.voltages[idx]
                    del self.currents[idx]
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
            self.fit_line = None
            self.slope = None
            self.intercept = None
    
    def clear_data(self):
        # 确认清除
        if messagebox.askyesno("确认清除", "确定要清除所有数据吗？"):
            # 清空数据
            self.voltages = []
            self.currents = []
            self.data_ids = []
            self.next_id = 1
            
            # 清空表格
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            # 清空图表
            self.ax.clear()
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.ax.set_xlabel('电压 (V)', fontsize=10)
            self.ax.set_ylabel('电流 (nA)', fontsize=10)
            self.ax.set_title('电压-电流特性曲线', fontsize=12)
            self.canvas.draw()
            
            # 清空结果
            self.result_text.delete(1.0, tk.END)
            
            # 重置拟合结果
            self.fit_line = None
            self.slope = None
            self.intercept = None
            
            # 重置缩放
            if self.zoom_selector:
                self.zoom_selector.set_active(False)
                self.zoom_selector = None
            
            if self.zoom_rect and self.zoom_rect in self.ax.patches:
                self.zoom_rect.remove()
                self.zoom_rect = None
    
    def update_scatter_plot(self):
        # 更新散点图
        self.ax.clear()
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.scatter(self.voltages, self.currents, color='blue', marker='o')
        self.ax.set_xlabel('电压 (V)', fontsize=10)
        self.ax.set_ylabel('电流 (nA)', fontsize=10)
        self.ax.set_title('电压-电流特性曲线', fontsize=12)
        self.canvas.draw()
    
    def fit_and_plot(self):
        if len(self.voltages) < 2:
            messagebox.showwarning("数据不足", "至少需要2个数据点才能进行拟合")
            return
        
        # 转换为numpy数组
        voltages_array = np.array(self.voltages)
        currents_array = np.array(self.currents)
        
        # 拟合数据
        slope, intercept, r_value, p_value, std_err = stats.linregress(voltages_array, currents_array)
        
        # 保存拟合结果
        self.slope = slope
        self.intercept = intercept
        self.fit_line = slope * voltages_array + intercept
        
        # 计算R²值
        r_squared = r_value ** 2
        
        # 更新图表
        self.ax.clear()
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.scatter(voltages_array, currents_array, color='blue', marker='o', label='实验数据')
        
        # 为了绘制平滑的拟合线，创建更多的点
        x_min, x_max = min(voltages_array), max(voltages_array)
        x_fit = np.linspace(x_min, x_max, 100)
        y_fit = slope * x_fit + intercept
        
        self.ax.plot(x_fit, y_fit, color='red', linewidth=2, label='拟合曲线')
        self.ax.set_xlabel('电压 (V)', fontsize=10)
        self.ax.set_ylabel('电流 (nA)', fontsize=10)
        self.ax.set_title('电压-电流特性曲线', fontsize=12)
        self.ax.legend(fontsize=9)
        
        # 美化图表
        self.ax.xaxis.set_minor_locator(MultipleLocator(0.5))
        self.ax.yaxis.set_minor_locator(MultipleLocator(0.5))
        
        self.canvas.draw()
        
        # 显示拟合结果
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"拟合方程: I = {slope:.4f} × V + {intercept:.4f}\n")
        self.result_text.insert(tk.END, f"斜率: {slope:.4f} nA/V\n")
        self.result_text.insert(tk.END, f"截距: {intercept:.4f} nA\n")
        self.result_text.insert(tk.END, f"R²值: {r_squared:.4f}")
    
    def save_plot(self):
        if not self.voltages:
            messagebox.showwarning("无数据", "没有数据可以保存")
            return
        
        # 保存图表
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voltage_current_curve.png')
        self.fig.savefig(save_path, dpi=300, bbox_inches='tight')
        messagebox.showinfo("保存成功", f"图表已保存为:\n{save_path}")

def main():
    root = tk.Tk()
    app = VoltageCurrentApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
