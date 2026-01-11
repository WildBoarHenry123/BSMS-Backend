from app.db import db
from datetime import datetime


# 角色表
class Role(db.Model):
    __tablename__ = 't_role'

    role_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='角色ID')
    role_name = db.Column(db.String(20), nullable=False, comment='角色名称')

    # 与用户的关联
    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.role_name}>'


# 用户表
class User(db.Model):
    __tablename__ = 't_user'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户编号')
    username = db.Column(db.String(30), nullable=False, comment='用户名')
    password = db.Column(db.String(64), nullable=False, comment='加密密码')
    role_id = db.Column(db.Integer, db.ForeignKey('t_role.role_id'), nullable=False, comment='所属角色ID')

    # 关联关系
    tokens = db.relationship('Token', backref='user', lazy=True, cascade='all, delete-orphan')
    purchases = db.relationship('Purchase', backref='operator', lazy=True)
    orders = db.relationship('Order', backref='seller', lazy=True)
    returns = db.relationship('Return', backref='processor', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


# 用户令牌表
class Token(db.Model):
    __tablename__ = 't_token'

    token_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='令牌ID')
    user_id = db.Column(db.Integer, db.ForeignKey('t_user.user_id', ondelete='CASCADE'), nullable=False,
                        comment='用户ID')
    token = db.Column(db.String(255), nullable=False, comment='Token值')
    expire_time = db.Column(db.DateTime, nullable=False, comment='过期时间')

    def __repr__(self):
        return f'<Token {self.token[:10]}...>'


# 图书基础信息表
class Book(db.Model):
    __tablename__ = 't_book'

    isbn = db.Column(db.String(13), primary_key=True, comment='ISBN号')
    title = db.Column(db.String(100), nullable=False, comment='图书名称')
    author = db.Column(db.String(50), nullable=True, comment='作者')
    publisher = db.Column(db.String(50), nullable=True, comment='出版社')
    price = db.Column(db.Numeric(8, 2), nullable=False, comment='定价')

    # 关联关系
    stock = db.relationship('Stock', backref='book', uselist=False, lazy=True, cascade='all, delete-orphan')
    supply_infos = db.relationship('SupplyInfo', backref='book', lazy=True)
    purchases = db.relationship('Purchase', backref='book', lazy=True)
    order_details = db.relationship('OrderDetail', backref='book', lazy=True)
    return_details = db.relationship('ReturnDetail', backref='book', lazy=True)

    def __repr__(self):
        return f'<Book {self.title} - {self.isbn}>'


# 图书库存表
class Stock(db.Model):
    __tablename__ = 't_stock'

    isbn = db.Column(db.String(13), db.ForeignKey('t_book.isbn', ondelete='CASCADE'), primary_key=True,
                     comment='ISBN号')
    quantity = db.Column(db.Integer, nullable=False, default=0, comment='当前库存量')

    def __repr__(self):
        return f'<Stock {self.isbn}: {self.quantity}>'


# 供应商表
class Supplier(db.Model):
    __tablename__ = 't_supplier'

    supplier_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='供应商编号')
    supplier_name = db.Column(db.String(100), nullable=False, comment='供应商名称')

    # 关联关系
    supply_infos = db.relationship('SupplyInfo', backref='supplier', lazy=True)
    purchases = db.relationship('Purchase', backref='supplier', lazy=True)

    def __repr__(self):
        return f'<Supplier {self.supplier_name}>'


# 供货报价表
class SupplyInfo(db.Model):
    __tablename__ = 't_supply_info'

    supplier_id = db.Column(db.Integer, db.ForeignKey('t_supplier.supplier_id'), primary_key=True, comment='供应商编号')
    isbn = db.Column(db.String(13), db.ForeignKey('t_book.isbn'), primary_key=True, comment='图书ISBN')
    supply_price = db.Column(db.Numeric(8, 2), nullable=False, comment='供货价')

    def __repr__(self):
        return f'<SupplyInfo {self.supplier_id}-{self.isbn}: ¥{self.supply_price}>'


# 进货记录表
class Purchase(db.Model):
    __tablename__ = 't_purchase'

    purchase_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='进货单号')
    supplier_id = db.Column(db.Integer, db.ForeignKey('t_supplier.supplier_id'), nullable=False, comment='供应商编号')
    isbn = db.Column(db.String(13), db.ForeignKey('t_book.isbn'), nullable=False, comment='图书ISBN')
    purchase_qty = db.Column(db.Integer, nullable=False, comment='进货数量')
    purchase_price = db.Column(db.Numeric(8, 2), nullable=False, comment='进货单价')
    purchase_time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='进货时间')
    user_id = db.Column(db.Integer, db.ForeignKey('t_user.user_id'), nullable=False, comment='经手人ID')

    def __repr__(self):
        return f'<Purchase {self.purchase_id}: {self.isbn} x{self.purchase_qty}>'


# 销售订单表
class Order(db.Model):
    __tablename__ = 't_order'

    order_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='订单编号')
    order_time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='销售时间')
    user_id = db.Column(db.Integer, db.ForeignKey('t_user.user_id'), nullable=False, comment='经手人ID')

    # 关联关系
    order_details = db.relationship('OrderDetail', backref='order', lazy=True, cascade='all, delete-orphan')
    returns = db.relationship('Return', backref='original_order', lazy=True)

    def __repr__(self):
        return f'<Order {self.order_id}>'


# 销售明细表
class OrderDetail(db.Model):
    __tablename__ = 't_order_detail'

    order_id = db.Column(db.BigInteger, db.ForeignKey('t_order.order_id'), primary_key=True, comment='订单编号')
    isbn = db.Column(db.String(13), db.ForeignKey('t_book.isbn'), primary_key=True, comment='图书ISBN')
    order_qty = db.Column(db.Integer, nullable=False, comment='购买数量')
    order_price = db.Column(db.Numeric(8, 2), nullable=False, comment='成交单价')

    def __repr__(self):
        return f'<OrderDetail Order:{self.order_id}, Book:{self.isbn}>'


# 退货订单表
class Return(db.Model):
    __tablename__ = 't_return'

    return_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='退货单号')
    order_id = db.Column(db.BigInteger, db.ForeignKey('t_order.order_id'), nullable=False, comment='原订单编号')
    reason = db.Column(db.String(255), nullable=True, comment='退货原因')
    return_time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='退货时间')
    user_id = db.Column(db.Integer, db.ForeignKey('t_user.user_id'), nullable=False, comment='处理人ID')

    # 关联关系
    return_details = db.relationship('ReturnDetail', backref='return_order', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Return {self.return_id} for Order:{self.order_id}>'


# 退货明细表
class ReturnDetail(db.Model):
    __tablename__ = 't_return_detail'

    return_id = db.Column(db.BigInteger, db.ForeignKey('t_return.return_id'), primary_key=True, comment='退货单号')
    isbn = db.Column(db.String(13), db.ForeignKey('t_book.isbn'), primary_key=True, comment='图书ISBN')
    return_qty = db.Column(db.Integer, nullable=False, comment='退货数量')

    def __repr__(self):
        return f'<ReturnDetail Return:{self.return_id}, Book:{self.isbn}>'
    

# 供货信息视图模型
class VSupplyInfo(db.Model):
    __tablename__ = 'v_supply_info'
    __table_args__ = (
        db.PrimaryKeyConstraint('supplier_id', 'isbn', name='pk_v_supply_info'),
        {'info': {'is_view': True}}  # 标记为视图
    )
    
    supplier_id = db.Column(db.Integer, nullable=False, comment='供应商编号')
    supplier_name = db.Column(db.String(100), nullable=False, comment='供应商名称')
    isbn = db.Column(db.String(13), nullable=False, comment='图书ISBN')
    title = db.Column(db.String(100), nullable=False, comment='图书名称')
    author = db.Column(db.String(50), nullable=True, comment='作者')
    publisher = db.Column(db.String(50), nullable=True, comment='出版社')
    supply_price = db.Column(db.Numeric(8, 2), nullable=False, comment='供货价')
    
    def to_dict(self):
        return {
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'publisher': self.publisher,
            'supply_price': float(self.supply_price) if self.supply_price else 0.0
        }
    
    def __repr__(self):
        return f'<VSupplyInfo {self.supplier_name}: {self.title} - ¥{self.supply_price}>'
    
# 进货记录视图模型
class VPurchaseRecord(db.Model):
    __tablename__ = 'v_purchase_record'
    
    # 使用 purchase_id 作为主键
    __table_args__ = (
        {'info': {'is_view': True}}  # 标记为视图
    )
    
    purchase_id = db.Column(db.BigInteger, primary_key=True, comment='进货单号')
    purchase_time = db.Column(db.DateTime, nullable=False, comment='进货时间')
    supplier_id = db.Column(db.Integer, nullable=False, comment='供应商编号')
    supplier_name = db.Column(db.String(100), nullable=False, comment='供应商名称')
    isbn = db.Column(db.String(13), nullable=False, comment='图书ISBN')
    title = db.Column(db.String(100), nullable=False, comment='图书名称')
    purchase_qty = db.Column(db.Integer, nullable=False, comment='进货数量')
    purchase_price = db.Column(db.Numeric(8, 2), nullable=False, comment='进货单价')
    user_id = db.Column(db.Integer, nullable=False, comment='经手人ID')
    username = db.Column(db.String(30), nullable=False, comment='经手人用户名')
    
    def to_dict(self):
        return {
            'purchase_id': self.purchase_id,
            'purchase_time': self.purchase_time.strftime('%Y-%m-%d %H:%M:%S') if self.purchase_time else None,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'isbn': self.isbn,
            'title': self.title,
            'purchase_qty': self.purchase_qty,
            'purchase_price': float(self.purchase_price) if self.purchase_price else 0.0,
            'user_id': self.user_id,
            'username': self.username
        }
    
    def __repr__(self):
        return f'<VPurchaseRecord {self.purchase_id}: {self.title} x{self.purchase_qty}>'
    
# 图书库存视图模型
class VBookInventory(db.Model):
    __tablename__ = 'v_book_inventory'
    
    # 使用 isbn 作为主键
    __table_args__ = (
        {'info': {'is_view': True}}  # 标记为视图
    )
    
    isbn = db.Column(db.String(13), primary_key=True, comment='ISBN号')
    title = db.Column(db.String(100), nullable=False, comment='图书名称')
    author = db.Column(db.String(50), nullable=True, comment='作者')
    publisher = db.Column(db.String(50), nullable=True, comment='出版社')
    price = db.Column(db.Numeric(8, 2), nullable=False, comment='定价')
    quantity = db.Column(db.Integer, nullable=False, comment='当前库存量')
    
    @property
    def stock_status(self):
        """库存状态"""
        if self.quantity <= 0:
            return '缺货'
        elif self.quantity <= 5:
            return '库存紧张'
        elif self.quantity <= 20:
            return '库存充足'
        else:
            return '库存充裕'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'publisher': self.publisher,
            'price': float(self.price) if self.price else 0.0,
            'quantity': self.quantity,
            'stock_status': self.stock_status
        }
    
    def __repr__(self):
        return f'<VBookInventory {self.title}: {self.quantity}本>'

# 库存紧张预警视图模型
class VInventoryShortageWarning(db.Model):
    __tablename__ = 'v_inventory_shortage_warning'
    
    # 使用 isbn 作为主键
    __table_args__ = (
        {'info': {'is_view': True}}  # 标记为视图
    )
    
    isbn = db.Column(db.String(13), primary_key=True, comment='ISBN号')
    title = db.Column(db.String(100), nullable=False, comment='图书名称')
    author = db.Column(db.String(50), nullable=True, comment='作者')
    publisher = db.Column(db.String(50), nullable=True, comment='出版社')
    price = db.Column(db.Numeric(8, 2), nullable=False, comment='定价')
    quantity = db.Column(db.Integer, nullable=False, comment='当前库存量')
    last_month_sales = db.Column(db.Integer, nullable=False, comment='上月销量')
    
    @property
    def months_of_supply(self):
        """库存可支撑月数"""
        if self.last_month_sales == 0:
            return float('inf')  # 无限
        return self.quantity / self.last_month_sales
    
    @property
    def warning_level(self):
        """预警级别"""
        if self.quantity == 0:
            return 'critical'  # 严重缺货
        elif self.months_of_supply <= 0.5:
            return 'high'  # 高风险
        elif self.months_of_supply <= 1:
            return 'medium'  # 中风险
        else:
            return 'low'  # 低风险
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'publisher': self.publisher,
            'price': float(self.price) if self.price else 0.0,
            'quantity': self.quantity,
            'last_month_sales': self.last_month_sales,
            'months_of_supply': round(self.months_of_supply, 2) if self.months_of_supply != float('inf') else '充足',
            'warning_level': self.warning_level
        }
    
    def __repr__(self):
        return f'<VInventoryShortageWarning {self.title}: 库存{self.quantity}, 上月销量{self.last_month_sales}>'


# 销售订单视图模型
class VSalesRecords(db.Model):
    __tablename__ = 'v_sales_records'

    # 使用 (order_id, isbn) 作为复合主键
    __table_args__ = (
        db.PrimaryKeyConstraint('order_id', 'isbn', name='pk_v_sales_records'),
        {'info': {'is_view': True}}  # 标记为视图
    )

    order_id = db.Column(db.BigInteger, nullable=False, comment='订单编号')
    order_time = db.Column(db.DateTime, nullable=False, comment='销售时间')
    user_id = db.Column(db.Integer, nullable=False, comment='经手人ID')
    username = db.Column(db.String(30), nullable=False, comment='经手人用户名')
    isbn = db.Column(db.String(13), nullable=False, comment='图书ISBN')
    title = db.Column(db.String(100), nullable=False, comment='图书名称')
    author = db.Column(db.String(50), nullable=True, comment='作者')
    publisher = db.Column(db.String(50), nullable=True, comment='出版社')
    order_qty = db.Column(db.Integer, nullable=False, comment='购买数量')
    order_price = db.Column(db.Numeric(8, 2), nullable=False, comment='成交单价')
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='订单总金额')

    def to_dict(self):
        """转换为字典格式"""
        result = {
            'order_id': self.order_id,
            'order_time': self.order_time.strftime('%Y-%m-%d %H:%M:%S') if self.order_time else None,
            'user_id': self.user_id,
            'username': self.username,
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'publisher': self.publisher,
            'order_qty': self.order_qty,
            'order_price': float(self.order_price) if self.order_price else 0.0,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0
        }
        return result

    def __repr__(self):
        return f'<VSalesRecords 订单{self.order_id}: {self.title} x{self.order_qty}>'


# 退货订单视图模型
class VReturnRecords(db.Model):
    __tablename__ = 'v_return_records'

    # 使用 (return_id, isbn) 作为复合主键
    __table_args__ = (
        db.PrimaryKeyConstraint('return_id', 'isbn', name='pk_v_return_records'),
        {'info': {'is_view': True}}  # 标记为视图
    )

    return_id = db.Column(db.BigInteger, nullable=False, comment='退货单号')
    order_id = db.Column(db.BigInteger, nullable=False, comment='原订单编号')
    return_time = db.Column(db.DateTime, nullable=False, comment='退货时间')
    reason = db.Column(db.String(255), nullable=True, comment='退货原因')
    user_id = db.Column(db.Integer, nullable=False, comment='处理人ID')
    username = db.Column(db.String(30), nullable=False, comment='处理人用户名')
    isbn = db.Column(db.String(13), nullable=False, comment='图书ISBN')
    title = db.Column(db.String(100), nullable=False, comment='图书名称')
    author = db.Column(db.String(50), nullable=True, comment='作者')
    publisher = db.Column(db.String(50), nullable=True, comment='出版社')
    return_qty = db.Column(db.Integer, nullable=False, comment='退货数量')
    refund_price = db.Column(db.Numeric(8, 2), nullable=False, comment='退款单价')
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='退货单总金额')

    def to_dict(self):
        """转换为字典格式"""
        result = {
            'return_id': self.return_id,
            'order_id': self.order_id,
            'return_time': self.return_time.strftime('%Y-%m-%d %H:%M:%S') if self.return_time else None,
            'reason': self.reason,
            'user_id': self.user_id,
            'username': self.username,
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'publisher': self.publisher,
            'return_qty': self.return_qty,
            'refund_price': float(self.refund_price) if self.refund_price else 0.0,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0
        }
        return result

    def __repr__(self):
        return f'<VReturnRecords 退货单{self.return_id}: {self.title} x{self.return_qty}>'