import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Toplevel

class LoginWindow:
    """登录窗口"""
    def __init__(self, root):
        self.root = root
        self.root.title("学生选课成绩管理系统 - 登录")
        self.root.geometry("400x300")
        self.root.resizable(False, False)

        # 数据库连接
        self.conn = sqlite3.connect('multi_role_course.db')
        self.init_database()

        # 创建登录界面
        self.create_login_ui()

    def init_database(self):
        """初始化所有表及默认数据"""
        cursor = self.conn.cursor()

        # 学生表
        cursor.execute('''CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class_name TEXT)''')

        # 教师表
        cursor.execute('''CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT)''')

        # 课程表
        cursor.execute('''CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            credit REAL,
            teacher_id INTEGER,
            FOREIGN KEY(teacher_id) REFERENCES teachers(id))''')

        # 选课成绩表
        cursor.execute('''CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            course_id INTEGER,
            score REAL,
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(course_id) REFERENCES courses(id),
            UNIQUE(student_id, course_id))''')

        # 用户表
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            student_id INTEGER,
            teacher_id INTEGER,
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(teacher_id) REFERENCES teachers(id))''')

        # 插入默认数据（如果表为空）
        cursor.execute("SELECT COUNT(*) FROM students")
        if cursor.fetchone()[0] == 0:
            # 学生
            cursor.execute("INSERT INTO students (name, class_name) VALUES (?,?)", ('张三', '计算机1班'))
            cursor.execute("INSERT INTO students (name, class_name) VALUES (?,?)", ('李四', '计算机2班'))
            # 教师
            cursor.execute("INSERT INTO teachers (name, department) VALUES (?,?)", ('王老师', '计算机系'))
            cursor.execute("INSERT INTO teachers (name, department) VALUES (?,?)", ('李老师', '英语系'))
            # 课程
            cursor.execute("INSERT INTO courses (name, credit, teacher_id) VALUES (?,?,?)", ('高等数学', 3.0, 1))
            cursor.execute("INSERT INTO courses (name, credit, teacher_id) VALUES (?,?,?)", ('大学英语', 2.0, 2))
            cursor.execute("INSERT INTO courses (name, credit, teacher_id) VALUES (?,?,?)", ('Python编程', 3.0, 1))
            cursor.execute("INSERT INTO courses (name, credit, teacher_id) VALUES (?,?,?)", ('数据库原理', 3.0, 1))
            # 选课示例：张三选了大学英语，王老师（teacher_id=1）的Python编程被李四选修（添加示例成绩便于教师测试）
            cursor.execute("INSERT OR IGNORE INTO scores (student_id, course_id, score) VALUES (?,?,?)", (1, 2, None))
            cursor.execute("INSERT OR IGNORE INTO scores (student_id, course_id, score) VALUES (?,?,?)", (2, 3, None))
            # 用户账户
            cursor.execute("INSERT INTO users (username, password, role, student_id, teacher_id) VALUES (?,?,?,?,?)",
                           ('student', 'student', 'student', 1, None))
            cursor.execute("INSERT INTO users (username, password, role, student_id, teacher_id) VALUES (?,?,?,?,?)",
                           ('teacher', 'teacher', 'teacher', None, 1))
            cursor.execute("INSERT INTO users (username, password, role, student_id, teacher_id) VALUES (?,?,?,?,?)",
                           ('admin', 'admin', 'admin', None, None))

        self.conn.commit()

    def create_login_ui(self):
        """登录界面布局"""
        frame = tk.Frame(self.root)
        frame.pack(expand=True)

        tk.Label(frame, text="学生选课成绩管理系统", font=("微软雅黑", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=20)

        tk.Label(frame, text="用户名:", font=("微软雅黑", 11)).grid(row=1, column=0, sticky="e", pady=10, padx=5)
        self.username_entry = tk.Entry(frame, font=("微软雅黑", 11), width=20)
        self.username_entry.grid(row=1, column=1, pady=10, padx=5)

        tk.Label(frame, text="密码:", font=("微软雅黑", 11)).grid(row=2, column=0, sticky="e", pady=10, padx=5)
        self.password_entry = tk.Entry(frame, show="*", font=("微软雅黑", 11), width=20)
        self.password_entry.grid(row=2, column=1, pady=10, padx=5)

        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        tk.Button(btn_frame, text="登录", command=self.login, width=10, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="退出", command=self.root.quit, width=10).pack(side=tk.LEFT)

        self.root.bind('<Return>', lambda e: self.login())

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空", parent=self.root)
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, role, student_id, teacher_id FROM users WHERE username=? AND password=?",
                       (username, password))
        user = cursor.fetchone()
        if user:
            self.conn.close()  # 关闭登录窗口的连接，后续主窗口重新连接
            self.root.destroy()
            # 打开主窗口
            main_root = tk.Tk()
            app = MainApplication(main_root, user)
            main_root.mainloop()
        else:
            messagebox.showerror("错误", "用户名或密码错误", parent=self.root)

class MainApplication:
    """主程序，根据角色显示不同界面"""
    def __init__(self, root, user_info):
        self.root = root
        self.user_id = user_info[0]
        self.username = user_info[1]
        self.role = user_info[2]
        self.student_id = user_info[3]
        self.teacher_id = user_info[4]

        self.root.title(f"学生选课成绩管理系统 - {self.role}用户: {self.username}")
        self.root.geometry("1100x700")

        # 重新建立数据库连接
        self.conn = sqlite3.connect('multi_role_course.db')

        # 创建菜单栏
        self.create_menu()

        # 根据角色创建界面
        if self.role == 'student':
            self.create_student_ui()
        elif self.role == 'teacher':
            self.create_teacher_ui()
        elif self.role == 'admin':
            self.create_admin_ui()
        else:
            messagebox.showerror("错误", "未知角色", parent=self.root)
            self.root.quit()

        # 窗口关闭时关闭数据库
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_menu(self):
        """创建统一的菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 系统菜单
        system_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="系统", menu=system_menu)
        system_menu.add_command(label="注销", command=self.logout)
        system_menu.add_separator()
        system_menu.add_command(label="退出", command=self.on_close)

    def logout(self):
        """注销：返回登录界面"""
        if messagebox.askyesno("确认注销", "确定要退出当前账户并返回登录界面吗？", parent=self.root):
            # 关闭数据库连接
            self.conn.close()
            # 销毁当前主窗口
            self.root.destroy()
            # 重新启动登录窗口
            new_login_root = tk.Tk()
            login_app = LoginWindow(new_login_root)
            new_login_root.mainloop()

    def on_close(self):
        self.conn.close()
        self.root.destroy()

    # ==================== 学生界面 ====================
    def create_student_ui(self):
        # 获取学生姓名
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, class_name FROM students WHERE id=?", (self.student_id,))
        stu_info = cursor.fetchone()
        stu_name = stu_info[0] if stu_info else "未知"

        # 顶部信息栏
        top_frame = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        tk.Label(top_frame, text=f"欢迎，学生：{stu_name}", font=("微软雅黑", 12, "bold"), fg="blue").pack(side=tk.LEFT, padx=10)

        # 左右两个主要区域
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧：所有课程
        left_frame = tk.LabelFrame(main_pane, text="📚 所有课程", font=("微软雅黑", 11))
        main_pane.add(left_frame, width=500)
        self.all_courses_tree = ttk.Treeview(left_frame, columns=("id", "name", "credit", "teacher"), show="headings", height=18)
        self.all_courses_tree.heading("id", text="课程ID")
        self.all_courses_tree.heading("name", text="课程名称")
        self.all_courses_tree.heading("credit", text="学分")
        self.all_courses_tree.heading("teacher", text="教师")
        self.all_courses_tree.column("id", width=60)
        self.all_courses_tree.column("name", width=200)
        self.all_courses_tree.column("credit", width=80)
        self.all_courses_tree.column("teacher", width=120)
        vsb1 = ttk.Scrollbar(left_frame, orient="vertical", command=self.all_courses_tree.yview)
        self.all_courses_tree.configure(yscrollcommand=vsb1.set)
        self.all_courses_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb1.pack(side=tk.RIGHT, fill=tk.Y)

        # 右侧：已选课程
        right_frame = tk.LabelFrame(main_pane, text="✅ 已选课程及成绩", font=("微软雅黑", 11))
        main_pane.add(right_frame, width=500)
        self.selected_courses_tree = ttk.Treeview(right_frame, columns=("id", "name", "credit", "score"), show="headings", height=18)
        self.selected_courses_tree.heading("id", text="课程ID")
        self.selected_courses_tree.heading("name", text="课程名称")
        self.selected_courses_tree.heading("credit", text="学分")
        self.selected_courses_tree.heading("score", text="成绩")
        self.selected_courses_tree.column("id", width=60)
        self.selected_courses_tree.column("name", width=200)
        self.selected_courses_tree.column("credit", width=80)
        self.selected_courses_tree.column("score", width=100)
        vsb2 = ttk.Scrollbar(right_frame, orient="vertical", command=self.selected_courses_tree.yview)
        self.selected_courses_tree.configure(yscrollcommand=vsb2.set)
        self.selected_courses_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb2.pack(side=tk.RIGHT, fill=tk.Y)

        # 底部按钮
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        tk.Button(button_frame, text="➕ 选课", command=self.student_enroll, bg="#e1f5fe", width=12).pack(side=tk.LEFT, padx=20)
        tk.Button(button_frame, text="➖ 退课", command=self.student_drop, bg="#ffebee", width=12).pack(side=tk.LEFT, padx=20)
        tk.Button(button_frame, text="🔄 刷新", command=self.refresh_student_data, width=12).pack(side=tk.LEFT, padx=20)

        # 初始加载数据
        self.refresh_student_data()

    def refresh_student_data(self):
        # 刷新所有课程列表
        for item in self.all_courses_tree.get_children():
            self.all_courses_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute('''SELECT c.id, c.name, c.credit, t.name 
                          FROM courses c LEFT JOIN teachers t ON c.teacher_id = t.id''')
        for row in cursor.fetchall():
            self.all_courses_tree.insert("", tk.END, values=row)

        # 刷新已选课程及成绩
        for item in self.selected_courses_tree.get_children():
            self.selected_courses_tree.delete(item)
        cursor.execute('''SELECT c.id, c.name, c.credit, s.score
                          FROM scores s
                          JOIN courses c ON s.course_id = c.id
                          WHERE s.student_id = ?''', (self.student_id,))
        for row in cursor.fetchall():
            score_display = row[3] if row[3] is not None else "未录入"
            self.selected_courses_tree.insert("", tk.END, values=(row[0], row[1], row[2], score_display))

    def student_enroll(self):
        selected = self.all_courses_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一门课程", parent=self.root)
            return
        values = self.all_courses_tree.item(selected[0], "values")
        course_id = values[0]
        course_name = values[1]
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM scores WHERE student_id=? AND course_id=?", (self.student_id, course_id))
        if cursor.fetchone():
            messagebox.showinfo("提示", f"你已经选过《{course_name}》", parent=self.root)
            return
        try:
            cursor.execute("INSERT INTO scores (student_id, course_id, score) VALUES (?,?,?)", (self.student_id, course_id, None))
            self.conn.commit()
            messagebox.showinfo("成功", f"成功添加课程：《{course_name}》", parent=self.root)
            self.refresh_student_data()
        except Exception as e:
            messagebox.showerror("错误", f"选课失败：{e}", parent=self.root)

    def student_drop(self):
        selected = self.selected_courses_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一门已选课程", parent=self.root)
            return
        values = self.selected_courses_tree.item(selected[0], "values")
        course_id = values[0]
        course_name = values[1]
        if messagebox.askyesno("确认退课", f"确定要退选《{course_name}》吗？", parent=self.root):
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM scores WHERE student_id=? AND course_id=?", (self.student_id, course_id))
            self.conn.commit()
            messagebox.showinfo("成功", f"已退选《{course_name}》", parent=self.root)
            self.refresh_student_data()

    # ==================== 教师界面 ====================
    def create_teacher_ui(self):
        # 获取教师姓名
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM teachers WHERE id=?", (self.teacher_id,))
        tea_info = cursor.fetchone()
        tea_name = tea_info[0] if tea_info else "未知"

        top_frame = tk.Frame(self.root, relief=tk.RAISED, bd=2)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        tk.Label(top_frame, text=f"教师：{tea_name}", font=("微软雅黑", 12, "bold"), fg="green").pack(side=tk.LEFT, padx=10)

        # 左右分栏：左侧课程列表，右侧学生成绩管理
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=5)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = tk.LabelFrame(main_pane, text="📖 我的课程", font=("微软雅黑", 11))
        main_pane.add(left_frame, width=400)
        self.teacher_courses_tree = ttk.Treeview(left_frame, columns=("id", "name", "credit"), show="headings", height=20)
        self.teacher_courses_tree.heading("id", text="课程ID")
        self.teacher_courses_tree.heading("name", text="课程名称")
        self.teacher_courses_tree.heading("credit", text="学分")
        self.teacher_courses_tree.column("id", width=80)
        self.teacher_courses_tree.column("name", width=200)
        self.teacher_courses_tree.column("credit", width=80)
        vsb1 = ttk.Scrollbar(left_frame, orient="vertical", command=self.teacher_courses_tree.yview)
        self.teacher_courses_tree.configure(yscrollcommand=vsb1.set)
        self.teacher_courses_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb1.pack(side=tk.RIGHT, fill=tk.Y)
        self.teacher_courses_tree.bind('<<TreeviewSelect>>', self.on_course_select)

        right_frame = tk.LabelFrame(main_pane, text="✏️ 选课学生及成绩录入（双击成绩单元格修改）", font=("微软雅黑", 11))
        main_pane.add(right_frame, width=600)
        # 学生成绩表格
        self.score_tree = ttk.Treeview(right_frame, columns=("student_id", "student_name", "class", "score"), show="headings", height=20)
        self.score_tree.heading("student_id", text="学号")
        self.score_tree.heading("student_name", text="姓名")
        self.score_tree.heading("class", text="班级")
        self.score_tree.heading("score", text="成绩")
        self.score_tree.column("student_id", width=80)
        self.score_tree.column("student_name", width=120)
        self.score_tree.column("class", width=150)
        self.score_tree.column("score", width=100)
        vsb2 = ttk.Scrollbar(right_frame, orient="vertical", command=self.score_tree.yview)
        self.score_tree.configure(yscrollcommand=vsb2.set)
        self.score_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb2.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定双击事件修改成绩
        self.score_tree.bind('<Double-1>', self.edit_score)

        # 底部按钮
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        tk.Button(btn_frame, text="💾 保存成绩", command=self.save_scores, bg="#c8e6c9", width=15).pack(side=tk.LEFT, padx=20)
        tk.Button(btn_frame, text="🔄 刷新", command=self.refresh_teacher_data, width=10).pack(side=tk.LEFT, padx=20)

        self.current_course_id = None
        self.refresh_teacher_data()

    def refresh_teacher_data(self):
        # 刷新教师所教课程
        for item in self.teacher_courses_tree.get_children():
            self.teacher_courses_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, credit FROM courses WHERE teacher_id=?", (self.teacher_id,))
        for row in cursor.fetchall():
            self.teacher_courses_tree.insert("", tk.END, values=row)

    def on_course_select(self, event):
        selected = self.teacher_courses_tree.selection()
        if not selected:
            return
        values = self.teacher_courses_tree.item(selected[0], "values")
        self.current_course_id = values[0]
        # 加载该课程下的学生及成绩
        for item in self.score_tree.get_children():
            self.score_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute('''SELECT s.id, s.name, s.class_name, sc.score
                          FROM scores sc
                          JOIN students s ON sc.student_id = s.id
                          WHERE sc.course_id = ?''', (self.current_course_id,))
        for row in cursor.fetchall():
            score_display = row[3] if row[3] is not None else ""
            self.score_tree.insert("", tk.END, values=(row[0], row[1], row[2], score_display))

    def edit_score(self, event):
        """双击成绩单元格，弹出输入框修改成绩"""
        region = self.score_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self.score_tree.identify_column(event.x)   # 列标识如 '#4'
        if column != '#4':   # 只有成绩列可以编辑
            return
        item = self.score_tree.identify_row(event.y)
        if not item:
            return
        # 获取当前值
        current_values = self.score_tree.item(item, "values")
        if len(current_values) < 4:
            return
        student_name = current_values[1]
        current_score = current_values[3]
        # 弹出输入对话框
        new_score_str = simpledialog.askstring("修改成绩", f"请输入学生 {student_name} 的成绩 (0-100):",
                                               initialvalue=str(current_score) if current_score else "", parent=self.root)
        if new_score_str is None:  # 取消
            return
        try:
            new_score = float(new_score_str)
            if 0 <= new_score <= 100:
                # 更新表格显示
                new_values = list(current_values)
                new_values[3] = new_score
                self.score_tree.item(item, values=tuple(new_values))
            else:
                messagebox.showwarning("警告", "成绩必须在0-100之间", parent=self.root)
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的数字", parent=self.root)

    def save_scores(self):
        if self.current_course_id is None:
            messagebox.showwarning("提示", "请先选择一门课程", parent=self.root)
            return
        # 遍历表格，更新成绩到数据库
        cursor = self.conn.cursor()
        for item in self.score_tree.get_children():
            values = self.score_tree.item(item, "values")
            student_id = values[0]
            score_str = values[3]
            if score_str == "":
                continue
            try:
                score = float(score_str)
                if 0 <= score <= 100:
                    cursor.execute("UPDATE scores SET score=? WHERE student_id=? AND course_id=?",
                                   (score, student_id, self.current_course_id))
                else:
                    messagebox.showwarning("警告", f"学生 {values[1]} 的成绩 {score} 超出0-100范围，未保存", parent=self.root)
            except ValueError:
                messagebox.showwarning("警告", f"学生 {values[1]} 的成绩格式不正确，未保存", parent=self.root)
        self.conn.commit()
        messagebox.showinfo("成功", "成绩已保存", parent=self.root)
        self.on_course_select(None)  # 刷新当前显示，重新从数据库加载确认保存成功

    # ==================== 管理员界面 ====================
    def create_admin_ui(self):
        # 使用 Notebook 选项卡
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 学生管理标签页
        self.student_frame = tk.Frame(notebook)
        notebook.add(self.student_frame, text="学生管理")
        self.create_student_management()

        # 教师管理标签页
        self.teacher_frame = tk.Frame(notebook)
        notebook.add(self.teacher_frame, text="教师管理")
        self.create_teacher_management()

        # 课程管理标签页
        self.course_frame = tk.Frame(notebook)
        notebook.add(self.course_frame, text="课程管理")
        self.create_course_management()

        # 用户账户管理标签页
        self.user_frame = tk.Frame(notebook)
        notebook.add(self.user_frame, text="账户管理")
        self.create_user_management()

    # 学生管理（显示序号，隐藏真实ID）
    def create_student_management(self):
        # 表格：显示序号、姓名、班级
        self.student_tree = ttk.Treeview(self.student_frame, columns=("sn", "name", "class"), show="headings", height=20)
        self.student_tree.heading("sn", text="序号")
        self.student_tree.heading("name", text="姓名")
        self.student_tree.heading("class", text="班级")
        self.student_tree.column("sn", width=60)
        self.student_tree.column("name", width=150)
        self.student_tree.column("class", width=200)
        self.student_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(self.student_frame, orient="vertical", command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(self.student_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        tk.Button(btn_frame, text="添加", command=self.add_student, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="修改", command=self.edit_student, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="删除", command=self.delete_student, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="刷新", command=self.refresh_students, width=10).pack(side=tk.LEFT, padx=5)

        self.refresh_students()

    def refresh_students(self):
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, class_name FROM students ORDER BY id")
        rows = cursor.fetchall()
        for idx, (sid, name, class_name) in enumerate(rows, start=1):
            # 将真实ID存储在item的iid中，显示序号、姓名、班级
            self.student_tree.insert("", tk.END, iid=str(sid), values=(idx, name, class_name))

    def add_student(self):
        name = simpledialog.askstring("添加学生", "请输入学生姓名", parent=self.root)
        if not name:
            return
        class_name = simpledialog.askstring("添加学生", "请输入班级", parent=self.root)
        if class_name is None:
            class_name = ""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO students (name, class_name) VALUES (?,?)", (name, class_name))
        self.conn.commit()
        self.refresh_students()

    def edit_student(self):
        selected = self.student_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要修改的学生", parent=self.root)
            return
        sid = int(selected[0])  # iid 存储真实ID
        current_values = self.student_tree.item(selected[0], "values")
        if len(current_values) < 2:
            return
        current_name = current_values[1]
        current_class = current_values[2] if len(current_values) > 2 else ""
        new_name = simpledialog.askstring("修改学生", "请输入新姓名", initialvalue=current_name, parent=self.root)
        if new_name is None:
            return
        new_class = simpledialog.askstring("修改学生", "请输入新班级", initialvalue=current_class, parent=self.root)
        if new_class is None:
            new_class = current_class
        cursor = self.conn.cursor()
        cursor.execute("UPDATE students SET name=?, class_name=? WHERE id=?", (new_name, new_class, sid))
        self.conn.commit()
        self.refresh_students()

    def delete_student(self):
        selected = self.student_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的学生", parent=self.root)
            return
        if messagebox.askyesno("确认", "删除学生也会同时删除其选课记录和用户账户，确定吗？", parent=self.root):
            sid = int(selected[0])
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM scores WHERE student_id=?", (sid,))
            cursor.execute("DELETE FROM users WHERE student_id=?", (sid,))
            cursor.execute("DELETE FROM students WHERE id=?", (sid,))
            self.conn.commit()
            self.refresh_students()

    # 教师管理（显示序号，隐藏真实ID）
    def create_teacher_management(self):
        self.teacher_tree = ttk.Treeview(self.teacher_frame, columns=("sn", "name", "dept"), show="headings", height=20)
        self.teacher_tree.heading("sn", text="序号")
        self.teacher_tree.heading("name", text="姓名")
        self.teacher_tree.heading("dept", text="院系")
        self.teacher_tree.column("sn", width=60)
        self.teacher_tree.column("name", width=150)
        self.teacher_tree.column("dept", width=200)
        self.teacher_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(self.teacher_frame, orient="vertical", command=self.teacher_tree.yview)
        self.teacher_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(self.teacher_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        tk.Button(btn_frame, text="添加", command=self.add_teacher, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="修改", command=self.edit_teacher, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="删除", command=self.delete_teacher, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="刷新", command=self.refresh_teachers, width=10).pack(side=tk.LEFT, padx=5)

        self.refresh_teachers()

    def refresh_teachers(self):
        for item in self.teacher_tree.get_children():
            self.teacher_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, department FROM teachers ORDER BY id")
        rows = cursor.fetchall()
        for idx, (tid, name, dept) in enumerate(rows, start=1):
            self.teacher_tree.insert("", tk.END, iid=str(tid), values=(idx, name, dept))

    def add_teacher(self):
        name = simpledialog.askstring("添加教师", "请输入教师姓名", parent=self.root)
        if not name:
            return
        dept = simpledialog.askstring("添加教师", "请输入院系", parent=self.root)
        if dept is None:
            dept = ""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO teachers (name, department) VALUES (?,?)", (name, dept))
        self.conn.commit()
        self.refresh_teachers()

    def edit_teacher(self):
        selected = self.teacher_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要修改的教师", parent=self.root)
            return
        tid = int(selected[0])
        current_values = self.teacher_tree.item(selected[0], "values")
        if len(current_values) < 2:
            return
        current_name = current_values[1]
        current_dept = current_values[2] if len(current_values) > 2 else ""
        new_name = simpledialog.askstring("修改教师", "请输入新姓名", initialvalue=current_name, parent=self.root)
        if new_name is None:
            return
        new_dept = simpledialog.askstring("修改教师", "请输入新院系", initialvalue=current_dept, parent=self.root)
        if new_dept is None:
            new_dept = current_dept
        cursor = self.conn.cursor()
        cursor.execute("UPDATE teachers SET name=?, department=? WHERE id=?", (new_name, new_dept, tid))
        self.conn.commit()
        self.refresh_teachers()

    def delete_teacher(self):
        selected = self.teacher_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的教师", parent=self.root)
            return
        if messagebox.askyesno("确认", "删除教师也会同时删除其教授的课程（将教师置空）和关联的用户账户，确定吗？", parent=self.root):
            tid = int(selected[0])
            cursor = self.conn.cursor()
            cursor.execute("UPDATE courses SET teacher_id=NULL WHERE teacher_id=?", (tid,))
            cursor.execute("DELETE FROM users WHERE teacher_id=?", (tid,))
            cursor.execute("DELETE FROM teachers WHERE id=?", (tid,))
            self.conn.commit()
            self.refresh_teachers()
            self.refresh_courses()  # 同时刷新课程列表

    # 课程管理（显示序号，隐藏真实ID）
    def create_course_management(self):
        self.course_tree = ttk.Treeview(self.course_frame, columns=("sn", "name", "credit", "teacher"), show="headings", height=20)
        self.course_tree.heading("sn", text="序号")
        self.course_tree.heading("name", text="课程名")
        self.course_tree.heading("credit", text="学分")
        self.course_tree.heading("teacher", text="授课教师")
        self.course_tree.column("sn", width=60)
        self.course_tree.column("name", width=180)
        self.course_tree.column("credit", width=80)
        self.course_tree.column("teacher", width=150)
        self.course_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(self.course_frame, orient="vertical", command=self.course_tree.yview)
        self.course_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(self.course_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        tk.Button(btn_frame, text="添加", command=self.add_course, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="修改", command=self.edit_course, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="删除", command=self.delete_course, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="刷新", command=self.refresh_courses, width=10).pack(side=tk.LEFT, padx=5)

        self.refresh_courses()

    def refresh_courses(self):
        for item in self.course_tree.get_children():
            self.course_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute('''SELECT c.id, c.name, c.credit, t.name 
                          FROM courses c LEFT JOIN teachers t ON c.teacher_id = t.id
                          ORDER BY c.id''')
        rows = cursor.fetchall()
        for idx, (cid, name, credit, teacher_name) in enumerate(rows, start=1):
            teacher_display = teacher_name if teacher_name else "未分配"
            self.course_tree.insert("", tk.END, iid=str(cid), values=(idx, name, credit, teacher_display))

    def add_course(self):
        name = simpledialog.askstring("添加课程", "请输入课程名", parent=self.root)
        if not name:
            return
        credit = simpledialog.askfloat("添加课程", "请输入学分", initialvalue=2.0, parent=self.root)
        if credit is None:
            return
        # 选择授课教师
        teachers = self.get_teacher_list()
        if not teachers:
            teacher_id = None
        else:
            teacher_names = [f"{t[0]} - {t[1]}" for t in teachers]
            teacher_choice = simpledialog.askstring("选择教师", f"可选教师：\n{', '.join(teacher_names)}\n请输入教师姓名或ID（留空则不指定）", parent=self.root)
            teacher_id = None
            if teacher_choice:
                for t in teachers:
                    if teacher_choice.strip() == t[1] or teacher_choice.strip() == str(t[0]):
                        teacher_id = t[0]
                        break
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO courses (name, credit, teacher_id) VALUES (?,?,?)", (name, credit, teacher_id))
        self.conn.commit()
        self.refresh_courses()

    def get_teacher_list(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name FROM teachers")
        return cursor.fetchall()

    def edit_course(self):
        selected = self.course_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要修改的课程", parent=self.root)
            return
        cid = int(selected[0])
        current_values = self.course_tree.item(selected[0], "values")
        if len(current_values) < 4:
            return
        current_name = current_values[1]
        current_credit = current_values[2]
        current_teacher = current_values[3]
        new_name = simpledialog.askstring("修改课程", "请输入新课程名", initialvalue=current_name, parent=self.root)
        if new_name is None:
            new_name = current_name
        new_credit = simpledialog.askfloat("修改课程", "请输入新学分", initialvalue=current_credit, parent=self.root)
        if new_credit is None:
            new_credit = current_credit
        # 教师修改
        teachers = self.get_teacher_list()
        teacher_names = [f"{t[0]} - {t[1]}" for t in teachers] + ["无"]
        teacher_choice = simpledialog.askstring("修改课程", f"可选教师：\n{', '.join(teacher_names)}\n输入教师姓名/ID或'无'", parent=self.root)
        teacher_id = None
        if teacher_choice and teacher_choice != "无":
            for t in teachers:
                if teacher_choice.strip() == t[1] or teacher_choice.strip() == str(t[0]):
                    teacher_id = t[0]
                    break
        cursor = self.conn.cursor()
        cursor.execute("UPDATE courses SET name=?, credit=?, teacher_id=? WHERE id=?", (new_name, new_credit, teacher_id, cid))
        self.conn.commit()
        self.refresh_courses()

    def delete_course(self):
        selected = self.course_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的课程", parent=self.root)
            return
        if messagebox.askyesno("确认", "删除课程也会删除所有相关的选课记录，确定吗？", parent=self.root):
            cid = int(selected[0])
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM scores WHERE course_id=?", (cid,))
            cursor.execute("DELETE FROM courses WHERE id=?", (cid,))
            self.conn.commit()
            self.refresh_courses()

    # 用户账户管理（不变）
    def create_user_management(self):
        self.user_tree = ttk.Treeview(self.user_frame, columns=("username", "role", "related_name"), show="headings", height=20)
        self.user_tree.heading("username", text="用户名")
        self.user_tree.heading("role", text="角色")
        self.user_tree.heading("related_name", text="关联人员")
        self.user_tree.column("username", width=150)
        self.user_tree.column("role", width=100)
        self.user_tree.column("related_name", width=200)
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb = ttk.Scrollbar(self.user_frame, orient="vertical", command=self.user_tree.yview)
        self.user_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = tk.Frame(self.user_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        tk.Button(btn_frame, text="重置密码", command=self.reset_password, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="为学生创建账户", command=self.create_student_account, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="为教师创建账户", command=self.create_teacher_account, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="刷新", command=self.refresh_users, width=10).pack(side=tk.LEFT, padx=5)

        self.refresh_users()

    def refresh_users(self):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        cursor = self.conn.cursor()
        cursor.execute('''SELECT u.username, u.role, 
                          CASE 
                            WHEN u.student_id IS NOT NULL THEN (SELECT name FROM students WHERE id=u.student_id)
                            WHEN u.teacher_id IS NOT NULL THEN (SELECT name FROM teachers WHERE id=u.teacher_id)
                            ELSE ''
                          END AS related
                          FROM users u''')
        for row in cursor.fetchall():
            self.user_tree.insert("", tk.END, values=row)

    def reset_password(self):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个用户", parent=self.root)
            return
        values = self.user_tree.item(selected[0], "values")
        username = values[0]
        new_pwd = simpledialog.askstring("重置密码", f"请输入用户 {username} 的新密码", show='*', parent=self.root)
        if new_pwd:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE users SET password=? WHERE username=?", (new_pwd, username))
            self.conn.commit()
            messagebox.showinfo("成功", f"用户 {username} 密码已重置为 {new_pwd}", parent=self.root)

    def create_student_account(self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT id, name FROM students WHERE id NOT IN (SELECT student_id FROM users WHERE student_id IS NOT NULL)''')
        students = cursor.fetchall()
        if not students:
            messagebox.showinfo("提示", "所有学生都已拥有账户", parent=self.root)
            return
        student_list = "\n".join([f"{s[0]}: {s[1]}" for s in students])
        sid_str = simpledialog.askstring("创建学生账户", f"可选学生ID：\n{student_list}\n请输入学生ID", parent=self.root)
        if not sid_str or not sid_str.isdigit():
            return
        sid = int(sid_str)
        cursor.execute("SELECT name FROM students WHERE id=?", (sid,))
        stu = cursor.fetchone()
        if stu:
            default_pwd = "123456"
            username = stu[0]
            base_username = username
            counter = 1
            while True:
                cursor.execute("SELECT id FROM users WHERE username=?", (username,))
                if cursor.fetchone():
                    username = f"{base_username}{counter}"
                    counter += 1
                else:
                    break
            cursor.execute("INSERT INTO users (username, password, role, student_id) VALUES (?,?,?,?)",
                           (username, default_pwd, 'student', sid))
            self.conn.commit()
            messagebox.showinfo("成功", f"已为学生 {stu[0]} 创建账户\n用户名: {username}\n初始密码: {default_pwd}", parent=self.root)
            self.refresh_users()
        else:
            messagebox.showerror("错误", "学生ID不存在", parent=self.root)

    def create_teacher_account(self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT id, name FROM teachers WHERE id NOT IN (SELECT teacher_id FROM users WHERE teacher_id IS NOT NULL)''')
        teachers = cursor.fetchall()
        if not teachers:
            messagebox.showinfo("提示", "所有教师都已拥有账户", parent=self.root)
            return
        teacher_list = "\n".join([f"{t[0]}: {t[1]}" for t in teachers])
        tid_str = simpledialog.askstring("创建教师账户", f"可选教师ID：\n{teacher_list}\n请输入教师ID", parent=self.root)
        if not tid_str or not tid_str.isdigit():
            return
        tid = int(tid_str)
        cursor.execute("SELECT name FROM teachers WHERE id=?", (tid,))
        tea = cursor.fetchone()
        if tea:
            default_pwd = "123456"
            username = tea[0]
            base_username = username
            counter = 1
            while True:
                cursor.execute("SELECT id FROM users WHERE username=?", (username,))
                if cursor.fetchone():
                    username = f"{base_username}{counter}"
                    counter += 1
                else:
                    break
            cursor.execute("INSERT INTO users (username, password, role, teacher_id) VALUES (?,?,?,?)",
                           (username, default_pwd, 'teacher', tid))
            self.conn.commit()
            messagebox.showinfo("成功", f"已为教师 {tea[0]} 创建账户\n用户名: {username}\n初始密码: {default_pwd}", parent=self.root)
            self.refresh_users()
        else:
            messagebox.showerror("错误", "教师ID不存在", parent=self.root)


if __name__ == "__main__":
    login_root = tk.Tk()
    app = LoginWindow(login_root)
    login_root.mainloop()