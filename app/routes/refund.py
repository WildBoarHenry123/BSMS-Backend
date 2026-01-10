from flask import Blueprint, request
from sqlalchemy import text, cast, String
import random, time
from datetime import datetime
from app.db import db
from app.models import VReturnRecords

refund_bp = Blueprint('refund', __name__)


# ========== 退货订单视图接口 ==========
@refund_bp.route('/select', methods=['GET'])
def refund_select():
    """退货订单视图查询"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        start_time = request.args.get('start_time', '').strip()
        end_time = request.args.get('end_time', '').strip()
        limit = request.args.get('limit', 100, type=int)
        sort_field = request.args.get('sort', 'return_time')
        sort_dir = request.args.get('dir', 'desc')  # 默认按时间降序

        # 验证limit范围
        if limit <= 0 or limit > 1000:
            limit = 100

        # 验证排序字段
        valid_sort_fields = ['return_id', 'order_id', 'return_time', 'user_id',
                             'username', 'isbn', 'title', 'return_qty',
                             'refund_price', 'total_amount']
        if sort_field not in valid_sort_fields:
            sort_field = 'return_time'

        # 验证排序方向
        if sort_dir not in ['asc', 'desc']:
            sort_dir = 'desc'

        # 构建基础查询
        query = VReturnRecords.query

        # 关键词搜索（支持多字段搜索）
        if keyword:
            keyword_pattern = f'%{keyword}%'
            query = query.filter(
                db.or_(
                    VReturnRecords.username.like(keyword_pattern),
                    VReturnRecords.title.like(keyword_pattern),
                    VReturnRecords.isbn.like(keyword_pattern),
                    VReturnRecords.reason.like(keyword_pattern),
                    cast(VReturnRecords.return_id, String).like(keyword_pattern),
                    cast(VReturnRecords.order_id, String).like(keyword_pattern),
                    cast(VReturnRecords.user_id, String).like(keyword_pattern),
                    cast(VReturnRecords.total_amount, String).like(keyword_pattern)
                )
            )

        # 时间范围过滤
        if start_time:
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(VReturnRecords.return_time >= start_dt)
            except ValueError:
                # 尝试其他格式
                try:
                    start_dt = datetime.strptime(start_time, '%Y-%m-%d')
                    query = query.filter(VReturnRecords.return_time >= start_dt)
                except ValueError:
                    pass  # 如果格式错误，忽略时间过滤

        if end_time:
            try:
                end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                query = query.filter(VReturnRecords.return_time <= end_dt)
            except ValueError:
                try:
                    end_dt = datetime.strptime(end_time, '%Y-%m-%d')
                    # 设置到当天的23:59:59
                    end_dt = datetime.combine(end_dt.date(), datetime.max.time())
                    query = query.filter(VReturnRecords.return_time <= end_dt)
                except ValueError:
                    pass  # 如果格式错误，忽略时间过滤

        # 获取总数
        total_count = query.count()

        # 构建排序
        sort_column = getattr(VReturnRecords, sort_field, VReturnRecords.return_time)
        if sort_dir == 'desc':
            sort_column = sort_column.desc()

        # 应用排序和分页
        refund_records = query.order_by(sort_column).limit(limit).all()

        # 按退货单ID分组，组装成退货单结构
        refunds_dict = {}
        for record in refund_records:
            return_id = record.return_id

            if return_id not in refunds_dict:
                # 创建退货单基础信息
                refunds_dict[return_id] = {
                    'return_id': return_id,
                    'order_id': record.order_id,
                    'return_time': record.return_time.strftime('%Y-%m-%d %H:%M:%S') if record.return_time else None,
                    'reason': record.reason,
                    'user_id': record.user_id,
                    'username': record.username,
                    'total_amount': float(record.total_amount) if record.total_amount else 0.0,
                    'details': []
                }

            # 添加退货单明细
            refunds_dict[return_id]['details'].append({
                'isbn': record.isbn,
                'title': record.title,
                'author': record.author,
                'publisher': record.publisher,
                'refund_price': float(record.refund_price) if record.refund_price else 0.0,
                'return_qty': record.return_qty
            })

        # 转换为列表
        refunds_list = list(refunds_dict.values())

        return {
            "code": 200,
            "msg": "Success.",
            "data": {
                "count": total_count,
                "list": refunds_list
            }
        }, 200

    except Exception as e:
        return {
            "code": 400,
            "msg": f"Fail.Reason:{str(e)}",
        }, 201
    
# ========= 登记退货接口 ==========
def generate_return_id():
    """生成唯一退货单ID"""
    base_id = int(datetime.now().strftime("%Y%m%d%H%M%S"))
    for _ in range(10):
        candidate_id = base_id * 1000 + random.randint(0, 999)
        exists = db.session.execute(
            text("SELECT COUNT(*) FROM t_return WHERE return_id = :return_id"),
            {"return_id": candidate_id}
        ).scalar()
        if not exists:
            return candidate_id
    return int(time.time() * 1000) * 100 + random.randint(1000, 9999)

@refund_bp.route('/insert', methods=['POST'])
def return_insert():
    data = request.get_json(silent=True) or {}
    order_id = data.get('order_id')
    user_id = data.get('user_id')
    reason = data.get('reason', '')
    details = data.get('details', [])

    if not order_id or not user_id or not details:
        return {"code": 400, "msg": "order_id, user_id, and details are required"}, 400

    try:
        for item in details:
            isbn = item.get('isbn')
            return_qty = item.get('return_qty')

            if not isbn or return_qty is None:
                return {"code": 400, "msg": "Each detail must contain isbn and return_qty"}, 400
            try:
                return_qty = int(return_qty)
            except (TypeError, ValueError):
                return {"code": 400, "msg": "return_qty must be an integer"}, 400
            if return_qty <= 0:
                return {"code": 400, "msg": "return_qty must be > 0"}, 400

            # 生成唯一退货单ID
            return_id = generate_return_id()

            # 调用存储过程
            db.session.execute(
                text("CALL proc_return_book(:return_id, :order_id, :isbn, :qty, :reason, :user_id)"),
                {
                    "return_id": return_id,
                    "order_id": order_id,
                    "isbn": isbn,
                    "qty": return_qty,
                    "reason": reason,
                    "user_id": user_id
                }
            )

        db.session.commit()
        return {
            "code": 200,
            "msg": "成功",
            "data": {
                "order_id": order_id,
                "user_id": user_id,
                "total_items": len(details)
            }
        }, 200

    except Exception as e:
        db.session.rollback()
        err_text = str(e)
        #解析存储过程 SIGNAL 错误，返回提示
        if "return quantity exceeds sold quantity" in err_text:
            return {"code": 400, "msg": "退货数量超过已售数量"}, 400
        if "order detail not found" in err_text:
            return {"code": 400, "msg": "订单明细不存在"}, 400
        return {"code": 400, "msg": f"Fail.Reason:{err_text}"}, 400

    
