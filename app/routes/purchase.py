from flask import Blueprint, request
from app.models import VPurchaseRecord
from app.db import db
from sqlalchemy import text, cast, String
from datetime import datetime
import time

purchase_bp = Blueprint('purchase', __name__)

@purchase_bp.route('/')
def purchase_hello():
    """测试 purchase 蓝图是否生效"""
    return 'Purchase module OK'

   
# ========== 进货记录视图接口 ==========
@purchase_bp.route('/select', methods=['GET'])
def purchase_select():
    """进货记录视图查询"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        start_time = request.args.get('start_time', '').strip()
        end_time = request.args.get('end_time', '').strip()
        limit = request.args.get('limit', 100, type=int)
        sort_field = request.args.get('sort', 'purchase_time')
        sort_dir = request.args.get('dir', 'desc')  # 默认按时间降序

        # 验证limit范围
        if limit <= 0 or limit > 1000:
            limit = 100

        # 验证排序字段
        valid_sort_fields = ['purchase_id', 'purchase_time', 'supplier_id',
                             'supplier_name', 'isbn', 'title', 'purchase_qty',
                             'purchase_price', 'user_id', 'username']
        if sort_field not in valid_sort_fields:
            sort_field = 'purchase_time'

        # 验证排序方向
        if sort_dir not in ['asc', 'desc']:
            sort_dir = 'desc'

        query = VPurchaseRecord.query

        # 关键词搜索（支持多字段搜索）
        if keyword:
            keyword_pattern = f'%{keyword}%'
            query = query.filter(
                db.or_(
                    VPurchaseRecord.supplier_name.like(keyword_pattern),
                    VPurchaseRecord.title.like(keyword_pattern),
                    VPurchaseRecord.isbn.like(keyword_pattern),
                    cast(VPurchaseRecord.purchase_id, String).like(keyword_pattern),
                    cast(VPurchaseRecord.user_id, String).like(keyword_pattern),
                    VPurchaseRecord.username.like(keyword_pattern)
                )
            )

        # 时间范围过滤
        if start_time:
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(VPurchaseRecord.purchase_time >= start_dt)
            except ValueError:
                # 尝试其他格式
                try:
                    start_dt = datetime.strptime(start_time, '%Y-%m-%d')
                    query = query.filter(VPurchaseRecord.purchase_time >= start_dt)
                except ValueError:
                    pass  # 如果格式错误，忽略时间过滤

        if end_time:
            try:
                end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(VPurchaseRecord.purchase_time <= end_dt)
            except ValueError:
                try:
                    end_dt = datetime.strptime(end_time, '%Y-%m-%d')
                    # 设置到当天的23:59:59
                    end_dt = datetime.combine(end_dt.date(), datetime.max.time())
                    query = query.filter(VPurchaseRecord.purchase_time <= end_dt)
                except ValueError:
                    pass  # 如果格式错误，忽略时间过滤

        # 获取总数
        total_count = query.count()

        # 构建排序
        sort_column = getattr(VPurchaseRecord, sort_field, VPurchaseRecord.purchase_time)
        if sort_dir == 'desc':
            sort_column = sort_column.desc()

        # 应用排序和分页
        purchase_records = query.order_by(sort_column).limit(limit).all()

        # 构建返回数据
        purchase_list = []
        for record in purchase_records:
            purchase_list.append(record.to_dict())

        return {
            "code": 200,
            "msg": "Success.",
            "data": {
                "count": total_count,
                "list": purchase_list
            }
        }, 200

    except Exception as e:
        return {
            "code": 400,
            "msg": f"Fail.Reason:{str(e)}",
        }, 201
    

# ========= 登记进货接口 ==========

# @purchase_bp.route('/insert', methods=['POST'])
# def purchase_insert():
#     """
#     登记进货接口
#     请求 JSON: { "supplier_id": int, "isbn": str, "purchase_qty": int, "user_id": int }
#     返回: {"code":200, "msg":"成功"} 或 错误信息
#     """
#     try:
#         data = request.get_json(silent=True) or {}
#         supplier_id = data.get("supplier_id")
#         isbn = data.get("isbn")
#         purchase_qty = data.get("purchase_qty")
#         user_id = data.get("user_id")
#
#         # 参数校验
#         if not all([supplier_id, isbn, purchase_qty, user_id]):
#             return {"code": 400, "msg": "缺少必填参数: supplier_id, isbn, purchase_qty, user_id"}, 201
#
#         try:
#             supplier_id = int(supplier_id)
#             purchase_qty = int(purchase_qty)
#             user_id = int(user_id)
#         except ValueError:
#             return {"code": 400, "msg": "supplier_id, purchase_qty, user_id 必须为整数"}, 201
#
#         if purchase_qty <= 0:
#             return {"code": 400, "msg": "purchase_qty 必须大于0"}, 201
#
#         # 1. 获取供货价（优先 t_supply_info）
#         row = db.session.execute(
#             text("SELECT supply_price FROM t_supply_info WHERE supplier_id = :sid AND isbn = :isbn"),
#             {"sid": supplier_id, "isbn": isbn}
#         ).fetchone()
#
#         if row and row[0] is not None:
#             purchase_price = row[0]
#         else:
#             # 回退到图书定价
#             row2 = db.session.execute(
#                 text("SELECT price FROM t_book WHERE isbn = :isbn"),
#                 {"isbn": isbn}
#             ).fetchone()
#             if row2 and row2[0] is not None:
#                 purchase_price = row2[0]
#             else:
#                 return {"code": 400, "msg": "未找到供货价或图书定价，无法确定进货价格"}, 201
#
#         # 2. 调用存储过程
#         db.session.execute(
#             text("CALL proc_purchase_book(:supplier_id, :isbn, :qty, :price, :user_id)"),
#             {
#                 "supplier_id": supplier_id,
#                 "isbn": isbn,
#                 "qty": purchase_qty,
#                 "price": purchase_price,
#                 "user_id": user_id
#             }
#         )
#         db.session.commit()
#
#         #查询最新库存和最近进货记录，用于调试
#         stock_row = db.session.execute(
#             text("SELECT quantity FROM t_stock WHERE isbn = :isbn"),
#             {"isbn": isbn}
#         ).fetchone()
#
#         purchase_row = db.session.execute(
#             text("""
#                 SELECT * FROM t_purchase
#                 WHERE isbn = :isbn
#                 ORDER BY purchase_time DESC
#                 LIMIT 1
#             """),
#             {"isbn": isbn}
#         ).fetchone()
#
#         return {
#             "code": 200,
#             "msg": "成功",
#             "data": {
#                 "new_stock": stock_row[0] if stock_row else None,
#                 "latest_purchase": dict(purchase_row._mapping) if purchase_row else None
#             }
#         }, 200
#
#     except Exception as e:
#         try:
#             db.session.rollback()
#         except Exception:
#             pass
#         return {"code": 400, "msg": f"Fail.Reason:{e}"}, 201

    