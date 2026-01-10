from flask import Blueprint, request
from sqlalchemy import text, cast, String
from app.db import db
import time
import random
from datetime import datetime
from app.models import VSalesRecords

order_bp = Blueprint('order', __name__)


@order_bp.route('/')
def order_hello():
    """测试 order 蓝图是否生效"""
    return 'order module OK'


@order_bp.route('/select', methods=['GET'])
def order_select():
    """销售订单视图查询 - 连接销售订单表、销售明细表、图书信息表、系统用户表"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        start_time = request.args.get('start_time', '').strip()
        end_time = request.args.get('end_time', '').strip()
        limit = request.args.get('limit', 100, type=int)
        sort_field = request.args.get('sort', 'order_time')
        sort_dir = request.args.get('dir', 'desc')  # 默认按时间降序

        # 验证limit范围
        if limit <= 0 or limit > 1000:
            limit = 100

        # 验证排序字段
        valid_sort_fields = ['order_id', 'order_time', 'user_id',
                             'username', 'isbn', 'title', 'order_qty',
                             'order_price', 'total_amount']
        if sort_field not in valid_sort_fields:
            sort_field = 'order_time'

        # 验证排序方向
        if sort_dir not in ['asc', 'desc']:
            sort_dir = 'desc'

        # 构建基础查询
        query = VSalesRecords.query

        # 关键词搜索（支持多字段搜索）
        if keyword:
            keyword_pattern = f'%{keyword}%'
            query = query.filter(
                db.or_(
                    VSalesRecords.username.like(keyword_pattern),
                    VSalesRecords.title.like(keyword_pattern),
                    VSalesRecords.isbn.like(keyword_pattern),
                    cast(VSalesRecords.order_id, String).like(keyword_pattern),
                    cast(VSalesRecords.user_id, String).like(keyword_pattern),
                    cast(VSalesRecords.total_amount, String).like(keyword_pattern)
                )
            )

        # 时间范围过滤
        if start_time:
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(VSalesRecords.order_time >= start_dt)
            except ValueError:
                # 尝试其他格式
                try:
                    start_dt = datetime.strptime(start_time, '%Y-%m-%d')
                    query = query.filter(VSalesRecords.order_time >= start_dt)
                except ValueError:
                    pass  # 如果格式错误，忽略时间过滤

        if end_time:
            try:
                end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(VSalesRecords.order_time <= end_dt)
            except ValueError:
                try:
                    end_dt = datetime.strptime(end_time, '%Y-%m-%d')
                    # 设置到当天的23:59:59
                    end_dt = datetime.combine(end_dt.date(), datetime.max.time())
                    query = query.filter(VSalesRecords.order_time <= end_dt)
                except ValueError:
                    pass  # 如果格式错误，忽略时间过滤

        # 获取总数
        total_count = query.count()

        # 构建排序
        sort_column = getattr(VSalesRecords, sort_field, VSalesRecords.order_time)
        if sort_dir == 'desc':
            sort_column = sort_column.desc()

        # 应用排序和分页
        sales_records = query.order_by(sort_column).limit(limit).all()

        # 按订单ID分组，组装成订单结构
        orders_dict = {}
        for record in sales_records:
            order_id = record.order_id

            if order_id not in orders_dict:
                # 创建订单基础信息
                orders_dict[order_id] = {
                    'order_id': order_id,
                    'order_time': record.order_time.strftime('%Y-%m-%d %H:%M:%S') if record.order_time else None,
                    'user_id': record.user_id,
                    'username': record.username,
                    'total_amount': float(record.total_amount) if record.total_amount else 0.0,
                    'details': []
                }

            # 添加订单明细
            orders_dict[order_id]['details'].append({
                'isbn': record.isbn,
                'title': record.title,
                'author': record.author,
                'publisher': record.publisher,
                'order_price': float(record.order_price) if record.order_price else 0.0,
                'order_qty': record.order_qty
            })

        # 转换为列表
        orders_list = list(orders_dict.values())

        return {
            "code": 200,
            "msg": "Success.",
            "data": {
                "count": total_count,
                "list": orders_list
            }
        }, 200

    except Exception as e:
        return {
            "code": 400,
            "msg": f"Fail.Reason:{str(e)}",
        }, 201

# ========= 登记销售接口 ==========
# def generate_order_id():
#     """生成唯一订单ID"""
#     # 基础部分：年月日时分秒
#     base_id = int(datetime.now().strftime("%Y%m%d%H%M%S"))
#
#     # 添加随机部分（0-999）
#     for _ in range(10):  # 尝试10次
#         candidate_id = base_id * 1000 + random.randint(0, 999)
#
#         # 检查是否已存在
#         exists = db.session.execute(
#             text("SELECT COUNT(*) FROM t_order WHERE order_id = :order_id"),
#             {"order_id": candidate_id}
#         ).scalar()
#
#         if not exists:
#             return candidate_id
#
#     # 如果所有尝试都失败，使用时间戳+进程ID
#     return int(time.time() * 1000) * 100 + random.randint(1000, 9999)
#
# @order_bp.route('/insert', methods=['POST'])
# def order_insert():
#     data = request.get_json()
#     user_id = data.get('user_id')
#     details = data.get('details', [])
#
#     if not user_id or not details:
#         return {"code": 400, "msg": "user_id and details are required"}, 400
#
#     try:
#         # 生成唯一订单ID
#         order_id = generate_order_id()
#
#         # 创建订单
#         db.session.execute(
#             text("INSERT INTO t_order (order_id, order_time, user_id) VALUES (:order_id, NOW(), :user_id)"),
#             {"order_id": order_id, "user_id": user_id}
#         )
#
#
#         db.session.commit()
#         return {
#             "code": 200,
#             "msg": "成功",
#             "data": {
#                 "order_id": order_id,
#                 "user_id": user_id,
#                 "total_items": len(details)
#             }
#         }, 200
#
#     except Exception as e:
#         db.session.rollback()
#         return {"code": 400, "msg": f"Fail.Reason:{str(e)}"}, 400
