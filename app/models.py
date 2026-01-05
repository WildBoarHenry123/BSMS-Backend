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

    purchase_id = db.Column(db.BigInteger, primary_key=True, comment='进货单号')
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

    order_id = db.Column(db.BigInteger, primary_key=True, comment='订单编号')
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

    return_id = db.Column(db.BigInteger, primary_key=True, comment='退货单号')
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