import mysql.connector
from mysql.connector import Error
import datetime
import re
import sys  # 添加缺失的sys模块导入

# 数据库配置
DB_CONFIG = {
    'user': 'root',
    'password': 'password',  # 默认密码，请根据您的MySQL设置修改
    'host': 'localhost',
    'raise_on_warnings': True
}

# 数据库名称
DATABASE_NAME = 'LibrarySystem'


def initialize_database():
    """创建数据库和所有表结构"""
    try:
        # 连接到MySQL服务器（不带数据库）
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("正在创建数据库...")
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}")
        cursor.execute(f"USE {DATABASE_NAME}")

        print("正在创建表结构...")
        # 创建员工表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Employee (
            EmployeeID VARCHAR(20) PRIMARY KEY,
            Name VARCHAR(50) NOT NULL,
            Phone VARCHAR(20),
            Email VARCHAR(100) NOT NULL
        )
        """)

        # 创建书目表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Catalogue (
            ISBN VARCHAR(20) PRIMARY KEY,
            Title VARCHAR(200) NOT NULL,
            Author VARCHAR(100) NOT NULL,
            Publisher VARCHAR(100),
            PublishDate DATE,
            TotalCopies INT DEFAULT 0
        )
        """)

        # 创建图书表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Book (
            BookID VARCHAR(20) PRIMARY KEY,
            ISBN VARCHAR(20) NOT NULL,
            Location VARCHAR(50) NOT NULL,
            Status ENUM('未借出', '已借出', '已预约', '不外借') DEFAULT '未借出',
            FOREIGN KEY (ISBN) REFERENCES Catalogue(ISBN) ON DELETE CASCADE
        )
        """)

        # 创建借阅记录表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Borrow (
            BorrowID INT AUTO_INCREMENT PRIMARY KEY,
            EmployeeID VARCHAR(20) NOT NULL,
            BookID VARCHAR(20) NOT NULL,
            BorrowDate DATE NOT NULL,
            ReturnDate DATE,
            LibrarianID VARCHAR(20) NOT NULL,
            FOREIGN KEY (EmployeeID) REFERENCES Employee(EmployeeID),
            FOREIGN KEY (BookID) REFERENCES Book(BookID),
            FOREIGN KEY (LibrarianID) REFERENCES Employee(EmployeeID)
        )
        """)

        # 创建预约记录表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Reservation (
            ReservationID INT AUTO_INCREMENT PRIMARY KEY,
            EmployeeID VARCHAR(20) NOT NULL,
            ISBN VARCHAR(20) NOT NULL,
            ReserveDate DATE NOT NULL,
            ExpiryDate DATE NOT NULL,
            BookID VARCHAR(20) DEFAULT NULL,
            FOREIGN KEY (EmployeeID) REFERENCES Employee(EmployeeID),
            FOREIGN KEY (ISBN) REFERENCES Catalogue(ISBN),
            FOREIGN KEY (BookID) REFERENCES Book(BookID)
        )
        """)

        # 创建系统设置表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS SystemSetting (
            SettingID INT PRIMARY KEY DEFAULT 1,
            FineRate DECIMAL(5,2) NOT NULL DEFAULT 0.50,
            MaxBorrowDays INT NOT NULL DEFAULT 60,
            MaxReserveDays INT NOT NULL DEFAULT 7,
            CHECK (SettingID = 1)
        )
        """)

        print("添加初始数据...")
        # 添加初始员工
        cursor.execute("""
        INSERT IGNORE INTO Employee (EmployeeID, Name, Phone, Email) VALUES
        ('EMP001', '张三', '13800138000', 'zhangsan@example.com'),
        ('ADM001', '管理员', '13900139000', 'admin@example.com')
        """)

        # 添加初始书目
        cursor.execute("""
        INSERT IGNORE INTO Catalogue (ISBN, Title, Author, Publisher, PublishDate, TotalCopies) VALUES
        ('9787111636664', 'Python编程：从入门到实践', 'Eric Matthes', '人民邮电出版社', '2020-01-01', 3),
        ('9787121416014', '深入理解计算机系统', 'Randal E.Bryant', '电子工业出版社', '2019-03-01', 2)
        """)

        # 添加初始图书
        cursor.execute("""
        INSERT IGNORE INTO Book (BookID, ISBN, Location, Status) VALUES
        ('BK001', '9787111636664', 'A区1排', '未借出'),
        ('BK002', '9787111636664', 'A区1排', '未借出'),
        ('BK003', '9787121416014', 'B区2排', '未借出')
        """)

        # 初始化系统设置
        cursor.execute("""
        INSERT IGNORE INTO SystemSetting (SettingID, FineRate, MaxBorrowDays, MaxReserveDays) 
        VALUES (1, 0.50, 60, 7)
        """)

        conn.commit()
        print("数据库初始化成功!")
        return True

    except Error as e:
        print(f"数据库初始化失败: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def connect_to_db():
    """连接到数据库"""
    try:
        # 使用数据库配置
        config = DB_CONFIG.copy()
        config['database'] = DATABASE_NAME

        conn = mysql.connector.connect(**config)
        return conn
    except Error as e:
        # 如果错误是数据库不存在，尝试初始化
        if "Unknown database" in str(e):
            print("数据库不存在，正在初始化...")
            if initialize_database():
                # 再次尝试连接
                return connect_to_db()
            else:
                print("数据库初始化失败，请检查错误信息")
                return None
        else:
            print(f"数据库连接错误: {e}")
            return None


def display_main_menu():
    """显示主菜单"""
    print("\n===== 图书管理系统 =====")
    print("1. 图书入库")
    print("2. 图书借阅")
    print("3. 图书归还")
    print("4. 图书预约")
    print("5. 查看所有图书")
    print("6. 查看我的借阅")
    print("7. 查看我的预约")
    print("8. 系统设置")
    print("9. 退出系统")
    choice = input("请选择操作 (1-9): ")
    return choice


def display_identity_menu():
    """显示身份选择菜单"""
    print("\n===== 身份选择 =====")
    print("1. 员工")
    print("2. 管理员")
    print("3. 退出")
    choice = input("请选择身份 (1-3): ")
    return choice


def get_identity_info():
    """获取身份信息"""
    identity_choice = display_identity_menu()

    if identity_choice == '3':
        return None

    employee_id = input("请输入您的工号: ")

    if identity_choice == '1':
        return {'EmployeeID': employee_id, 'is_admin': False}
    elif identity_choice == '2':
        return {'EmployeeID': employee_id, 'is_admin': True}
    else:
        print("无效选择")
        return None


def add_book(conn, librarian_id):
    """图书入库管理"""
    print("\n--- 图书入库 ---")

    # 获取图书信息
    isbn = input("输入ISBN号: ")
    title = input("输入书名: ")
    author = input("输入作者: ")
    publisher = input("输入出版商: ")
    publish_date = input("输入出版日期(YYYY-MM-DD): ")

    # 验证日期格式
    if not re.match(r'\d{4}-\d{2}-\d{2}', publish_date):
        print("日期格式错误，请使用YYYY-MM-DD格式")
        return

    book_id = input("输入图书ID: ")
    location = input("输入存放位置: ")
    status = input("输入图书状态(未借出/已借出/已预约/不外借): ")

    try:
        cursor = conn.cursor()

        # 检查书目是否存在
        cursor.execute("SELECT * FROM Catalogue WHERE ISBN = %s", (isbn,))
        catalogue_exists = cursor.fetchone()

        if not catalogue_exists:
            # 创建新书目
            cursor.execute(
                "INSERT INTO Catalogue (ISBN, Title, Author, Publisher, PublishDate) "
                "VALUES (%s, %s, %s, %s, %s)",
                (isbn, title, author, publisher, publish_date)
            )
            print(f"新书目 {title} 已创建")

        # 添加图书
        cursor.execute(
            "INSERT INTO Book (BookID, ISBN, Location, Status) "
            "VALUES (%s, %s, %s, %s)",
            (book_id, isbn, location, status)
        )

        # 更新书目册数
        cursor.execute(
            "UPDATE Catalogue SET TotalCopies = TotalCopies + 1 WHERE ISBN = %s",
            (isbn,)
        )

        conn.commit()
        print(f"图书 {book_id} 入库成功!")

    except Error as e:
        print(f"入库失败: {e}")
        conn.rollback()
    finally:
        cursor.close()


def borrow_book(conn, employee_id):
    """图书借阅管理"""
    print("\n--- 图书借阅 ---")
    book_id = input("输入要借阅的图书ID: ")

    # 管理员需要输入管理员ID
    librarian_id = input("输入处理此借阅的管理员ID: ") if employee_id != 'admin' else employee_id

    try:
        cursor = conn.cursor()

        # 检查该员工当前借阅数量
        cursor.execute(
            "SELECT COUNT(*) FROM Borrow WHERE EmployeeID = %s AND ReturnDate IS NULL",
            (employee_id,)
        )
        current_borrow_count = cursor.fetchone()[0]

        if current_borrow_count >= 10:
            print("错误：已达到最大借阅数量(10本)")
            return

        # 检查图书状态
        cursor.execute("SELECT Status FROM Book WHERE BookID = %s", (book_id,))
        book_status = cursor.fetchone()

        if not book_status:
            print("错误：图书不存在")
            return

        if book_status[0] != "未借出":
            print(f"错误：图书当前状态为 {book_status[0]}，无法借阅")
            return

        # 创建借阅记录
        borrow_date = datetime.date.today()
        cursor.execute(
            "INSERT INTO Borrow (EmployeeID, BookID, BorrowDate, LibrarianID) "
            "VALUES (%s, %s, %s, %s)",
            (employee_id, book_id, borrow_date, librarian_id)
        )

        # 更新图书状态
        cursor.execute(
            "UPDATE Book SET Status = '已借出' WHERE BookID = %s",
            (book_id,)
        )

        conn.commit()
        print(f"图书 {book_id} 借阅成功!")

    except Error as e:
        print(f"借阅失败: {e}")
        conn.rollback()
    finally:
        cursor.close()


def return_book(conn, employee_id):
    """图书归还管理"""
    print("\n--- 图书归还 ---")
    book_id = input("输入要归还的图书ID: ")

    try:
        cursor = conn.cursor()

        # 获取借阅记录
        cursor.execute(
            "SELECT BorrowID, BorrowDate FROM Borrow "
            "WHERE BookID = %s AND EmployeeID = %s AND ReturnDate IS NULL",
            (book_id, employee_id)
        )
        borrow_record = cursor.fetchone()

        if not borrow_record:
            print("错误：没有找到未归还的借阅记录")
            return

        borrow_id, borrow_date = borrow_record
        return_date = datetime.date.today()

        # 更新归还日期
        cursor.execute(
            "UPDATE Borrow SET ReturnDate = %s WHERE BorrowID = %s",
            (return_date, borrow_id)
        )

        # 获取系统设置
        cursor.execute("SELECT FineRate, MaxBorrowDays FROM SystemSetting")
        result = cursor.fetchone()
        if result:
            fine_rate, max_borrow_days = result
        else:
            # 默认值
            fine_rate = 0.5
            max_borrow_days = 60

        # 计算罚金（如果超期）
        due_date = borrow_date + datetime.timedelta(days=max_borrow_days)
        if return_date > due_date:
            overdue_days = (return_date - due_date).days
            fine = overdue_days * fine_rate
            print(f"警告：超期归还！罚金: {fine:.2f}元")
        else:
            fine = 0

        # 检查是否有预约
        cursor.execute(
            "SELECT ReservationID FROM Reservation "
            "WHERE BookID IS NULL AND ISBN = (SELECT ISBN FROM Book WHERE BookID = %s) "
            "AND ExpiryDate > %s",
            (book_id, return_date)
        )
        reservation = cursor.fetchone()

        if reservation:
            # 分配给预约
            cursor.execute(
                "UPDATE Reservation SET BookID = %s WHERE ReservationID = %s",
                (book_id, reservation[0])
            )
            cursor.execute(
                "UPDATE Book SET Status = '已预约' WHERE BookID = %s",
                (book_id,)
            )
            print("该书已被预约，状态设为'已预约'")
        else:
            # 设为未借出
            cursor.execute(
                "UPDATE Book SET Status = '未借出' WHERE BookID = %s",
                (book_id,)
            )

        conn.commit()
        print(f"图书 {book_id} 归还成功!")

    except Error as e:
        print(f"归还失败: {e}")
        conn.rollback()
    finally:
        cursor.close()


def make_reservation(conn, employee_id):
    """图书预约管理"""
    print("\n--- 图书预约 ---")
    isbn = input("输入要预约的图书ISBN号: ")

    try:
        cursor = conn.cursor()

        # 检查是否有可借图书
        cursor.execute(
            "SELECT 1 FROM Book WHERE ISBN = %s AND Status = '未借出'",
            (isbn,)
        )
        if cursor.fetchone():
            print("存在可借图书，请直接借阅")
            return

        # 检查是否已预约过同一书目
        cursor.execute(
            "SELECT 1 FROM Reservation "
            "WHERE EmployeeID = %s AND ISBN = %s AND ExpiryDate > %s",
            (employee_id, isbn, datetime.date.today())
        )
        if cursor.fetchone():
            print("您已预约过该图书")
            return

        # 获取系统设置
        cursor.execute("SELECT MaxReserveDays FROM SystemSetting")
        result = cursor.fetchone()
        max_reserve_days = result[0] if result else 7

        # 创建预约记录
        reserve_date = datetime.date.today()
        expiry_date = reserve_date + datetime.timedelta(days=max_reserve_days)

        cursor.execute(
            "INSERT INTO Reservation (EmployeeID, ISBN, ReserveDate, ExpiryDate) "
            "VALUES (%s, %s, %s, %s)",
            (employee_id, isbn, reserve_date, expiry_date)
        )

        conn.commit()
        print(f"图书 {isbn} 预约成功! 有效期至 {expiry_date}")

    except Error as极狐
    print(f"预约失败: {e}")
    conn.rollback()

finally:
cursor.close()


def list_books(conn):
    """查看所有图书"""
    try:
        cursor = conn.cursor(dictionary=True)

        # 查询所有图书信息
        cursor.execute(
            "SELECT b.BookID, c.Title, c.Author, b.Location, b.Status, c.ISBN "
            "FROM Book b JOIN Catalogue c ON b.ISBN = c.ISBN"
        )
        books = cursor.fetchall()

        if not books:
            print("没有找到图书信息")
            return

        print("\n--- 所有图书列表 ---")
        print(f"{'图书ID':<10} {'书名':<25} {'作者':<15} {'位置':<15} {'状态':<10} {'ISBN'}")
        print("-" * 80)
        for book in books:
            print(f"{book['BookID']:<10} {book['Title']:<25} {book['Author']:<15} "
                  f"{book['Location']:<15} {极狐'Status']: < 10} {book['ISBN']}")

    except Error as e:
        print(f"查询失败: {e}")
    finally:
        cursor.close()


def my_borrows(conn, employee_id):
    """查看我的借阅"""
    try:
        cursor = conn.cursor(dictionary=True)

        # 查询当前借阅
        cursor.execute(
            "SELECT b.BookID, c.Title, br.BorrowDate, br.ReturnDate "
            "FROM Borrow br "
            "JOIN Book b ON br.BookID = b.BookID "
            "JOIN Catalogue c ON b.ISBN = c.ISBN "
            "WHERE br.EmployeeID = %s AND br.ReturnDate IS NULL",
            (employee_id,)
        )
        current_borrows = cursor.fetchall()

        # 查询历史借阅
        cursor.execute(
            "SELECT b.BookID, c.Title, br.BorrowDate, br.ReturnDate "
            "FROM Borrow br "
            "JOIN Book b ON br.BookID = b.BookID "
            "JOIN Catalogue c ON b.ISBN = c.ISBN "
            "WHERE br.EmployeeID = %极狐 AND br.ReturnDate IS NOT NULL",
            (employee_id,)
        )
        history_borrows = cursor.fetchall()

        # 显示当前借阅
        print("\n--- 当前借阅 ---")
        if current_borrows:
            print(f"{'图书ID':<10} {'书名':<25} {'借阅日期':<15} {'状态'}")
            print("-" * 60)
            for borrow in current_borrows:
                print(f"{borrow['BookID']:<10} {borrow['Title']:<25} "
                      f"{borrow['BorrowDate']} {'未归还'}")
        else:
            print("没有当前借阅")

        # 显示历史借阅
        print("\n--- 历史借阅 ---")
        if history_borrows:
            print(f"{'图书ID':<10} {'书名':<25} {'借阅日期':<15} {'归还日期'}")
            print("-" * 60)
            for borrow in history_borrows:
                print(f"{borrow['BookID']:<10} {borrow['Title']:<25} "
                      f"{borrow['BorrowDate']} {borrow['ReturnDate']}")
        else:
            print("没有历史借阅记录")

    except Error as e:
        print(f"查询失败: {e}")
    finally:
        cursor.close()


def my_reservations(conn, employee_id):
    """查看我的预约"""
    try:
        cursor = conn.cursor(dictionary=True)

        # 查询有效预约
        cursor.execute(
            "SELECT r.ReservationID, c.Title, r.ReserveDate, r.ExpiryDate, r.BookID "
            "FROM Reservation r "
            "JOIN Catalogue c ON r.ISBN = c.ISBN "
            "WHERE r.EmployeeID = %s AND r.ExpiryDate > %s",
            (employee_id, datetime.date.today())
        )
        active_reservations = cursor.fetchall()

        print("\n--- 我的预约 ---")
        if active_reservations:
            print(f"{'预约ID':<10} {'书名':<25} {'预约日期':<15} {'有效期至':<15} {'状态'}")
            print("-" * 70)
            for res in active_reservations:
                status = "已分配" if res['BookID'] else "等待中"
                print(f"{res['ReservationID']:<10} {res['Title']:<25} "
                      f"{res['ReserveDate']} {res['ExpiryDate']} {status}")
        else:
            print("没有有效预约")

    except Error as e:
        print(f"查询失败: {e}")
    finally:
        cursor.close()


def system_settings(conn):
    """系统设置管理"""
    print("\n--- 系统设置 ---")
    try:
        cursor = conn.cursor(dictionary=True)

        # 获取当前设置
        cursor.execute("SELECT * FROM SystemSetting")
        settings = cursor.fetchone()

        if settings:
            print("当前系统设置:")
            print(f"1. 罚金单价: {settings['FineRate']}元/天")
            print(f"2. 最长借阅天数: {settings['MaxBorrowDays']}天")
            print(f"3. 最长预约天数: {settings['MaxReserveDays']}天")
        else:
            # 初始化默认设置
            print("使用默认系统设置")
            settings = {'FineRate': 0.5, 'MaxBorrowDays': 60, 'MaxReserveDays': 7}
            cursor.execute(
                "INSERT INTO SystemSetting (SettingID, FineRate, MaxBorrowDays, MaxReserveDays) "
                "VALUES (1, 0.5, 60, 7)"
            )
            conn.commit()

        choice = input("是否修改设置? (y/n): ").lower()
        if choice != 'y':
            return

        # 更新设置
        fine_rate = float(input("输入新的罚金单价: "))
        max_borrow_days = int(input("输入新的最长借阅天数: "))
        max_reserve_days = int(input("输入新的最长预约天数: "))

        if settings:  # 更新现有设置
            cursor.execute(
                "UPDATE SystemSetting SET FineRate = %s, MaxBorrowDays = %s, MaxReserveDays = %s "
                "WHERE SettingID = 1",
                (fine_rate, max_borrow_days, max_reserve_days)
            )
        else:  # 插入新设置
            cursor.execute(
                "INSERT INTO SystemSetting (SettingID, FineRate, MaxBorrowDays, MaxReserveDays) "
                "VALUES (1, %s, %s, %s)",
                (fine_rate, max_borrow_days, max_reserve_days)
            )

        conn.commit()
        print("系统设置已更新!")

    except Error as e:
        print(f"设置更新失败: {e}")
        conn.rollback()
    finally:
        cursor.close()


def main():
    # 显示欢迎信息
    print("\n===== 欢迎使用图书管理系统 =====")

    # 连接到数据库（如果不存在会自动创建）
    conn = connect_to_db()
    if not conn:
        print("数据库连接失败，系统退出")
        return

    # 获取身份信息
    identity_info = get_identity_info()
    if not identity_info:
        print("系统退出")
        return

    employee_id = identity_info['EmployeeID']
    is_admin = identity_info['is_admin']

    # 显示欢迎消息
    role = "管理员" if is_admin else "员工"
    print(f"\n欢迎 {employee_id} ({role}) 使用图书管理系统!")

    try:
        while True:
            choice = display_main_menu()

            # 处理管理功能权限
            if choice == '1':  # 图书入库
                if is_admin:
                    add_book(conn, employee_id)
                else:
                    print("无权限: 仅管理员可以进行图书入库")
            elif choice == '2':  # 图书借阅
                borrow_book(conn, employee_id)
            elif choice == '3':  # 图书归还
                return_book(conn, employee_id)
            elif choice == '4':  # 图书预约
                make_reservation(conn, employee_id)
            elif choice == '5':  # 查看所有图书
                list_books(conn)
            elif choice == '6':  # 查看我的借阅
                my_borrows(conn, employee_id)
            elif choice == '7':  # 查看我的预约
                my_reservations(conn, employee_id)
            elif choice == '8':  # 系统设置
                if is_admin:
                    system_settings(conn)
                else:
                    print("无权限: 仅管理员可以进行系统设置")
            elif choice == '9':  # 退出系统
                print("感谢使用图书管理系统，再见！")
                break
            else:
                print("无效选择，请重新输入")

    except KeyboardInterrupt:
        print("\n操作已取消，退出系统")
    except Error as e:
        print(f"发生数据库错误: {e}")
    finally:
        if conn:
            conn.close()


def setup_instructions():
    """显示安装说明"""
    print("===== 图书管理系统安装指南 =====")
    print("1. 确保已安装MySQL服务器")
    print("2. 修改程序中的数据库配置：")
    print("   - 打开此Python文件")
    print("   - 找到 'DB_CONFIG' 变量")
    print("   - 修改 'user' 和 'password' 为您的MySQL凭据")
    print("3. 运行程序：python library_system.py")
    print("4. 首次运行时会自动创建数据库和表结构")
    print("5. 使用以下初始账号：")
    print("   - 员工工号: EMP001")
    print("   - 管理员工号: ADM001")
    print("\n注意：请确保MySQL服务正在运行")


if __name__ == "__main__":
    # 检查是否显示安装说明
    if len(sys.argv) > 1 and sys.argv[1] == '--setup':
        setup_instructions()
    else:
        main()