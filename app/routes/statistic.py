from flask import Blueprint, request
from sqlalchemy import text
from datetime import datetime
from app.db import db
from app.models import VInventoryShortageWarning, VBookInventory

statistic_bp = Blueprint('statistic', __name__)


@statistic_bp.route('/')
def statistic_hello():
    """测试 statistic 蓝图是否生效"""
    return 'statistic module OK'


@statistic_bp.route('/stock/select', methods=['GET'])
def stock_select():
    """图书库存视图查询 - 连接图书基础信息表、库存表"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        limit = request.args.get('limit', 50, type=int)
        sort_field = request.args.get('sort', 'quantity')
        sort_dir = request.args.get('dir', 'asc')

        # 验证limit范围
        if limit <= 0 or limit > 500:
            limit = 50

        # 验证排序字段
        valid_sort_fields = ['isbn', 'title', 'author', 'publisher', 'price', 'quantity']
        if sort_field not in valid_sort_fields:
            sort_field = 'quantity'

        # 验证排序方向
        if sort_dir not in ['asc', 'desc']:
            sort_dir = 'asc'

        # 构建基础查询
        query = VBookInventory.query

        # 关键词搜索（支持图书名称和ISBN搜索）
        if keyword:
            keyword_pattern = f'%{keyword}%'
            query = query.filter(
                db.or_(
                    VBookInventory.title.like(keyword_pattern),
                    VBookInventory.isbn.like(keyword_pattern),
                    VBookInventory.author.like(keyword_pattern),
                    VBookInventory.publisher.like(keyword_pattern)
                )
            )

        # 获取总数
        total_count = query.count()

        # 构建排序
        sort_column = getattr(VBookInventory, sort_field, VBookInventory.quantity)
        if sort_dir == 'desc':
            sort_column = sort_column.desc()

        # 应用排序和分页
        inventory_records = query.order_by(sort_column).limit(limit).all()

        # 构建返回数据
        inventory_list = []
        for record in inventory_records:
            inventory_list.append({
                'isbn': record.isbn,
                'title': record.title,
                'author': record.author,
                'publisher': record.publisher,
                'price': float(record.price) if record.price else 0.0,
                'quantity': record.quantity
            })

        return {
            "code": 200,
            "msg": "Success.",
            "data": {
                "count": total_count,
                "list": inventory_list
            }
        }, 200

    except Exception as e:
        return {
            "code": 400,
            "msg": f"Fail.Reason:{str(e)}",
        }, 201


@statistic_bp.route('/stock/shortage', methods=['GET'])
def stock_shortage():
    """库存紧张预警视图 - 获取急需补货的图书列表"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '').strip()
        limit = request.args.get('limit', 20, type=int)

        # 验证limit范围
        if limit <= 0 or limit > 100:
            limit = 20

        # 构建基础查询
        query = VInventoryShortageWarning.query

        # 关键词搜索
        if keyword:
            keyword_pattern = f'%{keyword}%'
            query = query.filter(
                db.or_(
                    VInventoryShortageWarning.title.like(keyword_pattern),
                    VInventoryShortageWarning.isbn.like(keyword_pattern),
                    VInventoryShortageWarning.author.like(keyword_pattern),
                    VInventoryShortageWarning.publisher.like(keyword_pattern)
                )
            )

        # 获取总数
        total_count = query.count()

        # 应用分页（默认按库存数量升序）
        shortage_records = query.order_by(
            VInventoryShortageWarning.quantity.asc()
        ).limit(limit).all()

        # 构建返回数据
        shortage_list = []
        for record in shortage_records:
            shortage_list.append({
                'isbn': record.isbn,
                'title': record.title,
                'author': record.author,
                'publisher': record.publisher,
                'price': float(record.price) if record.price else 0.0,
                'quantity': record.quantity,
                'last_month_sales': record.last_month_sales
            })

        return {
            "code": 200,
            "msg": "Success.",
            "data": {
                "count": total_count,
                "list": shortage_list
            }
        }, 200

    except Exception as e:
        return {
            "code": 400,
            "msg": f"Fail.Reason:{str(e)}",
        }, 201


# ========== 日榜接口 ==========
@statistic_bp.route('/sales/rank/daily', methods=['GET'])
def daily_rank():
    from datetime import datetime
    from decimal import Decimal

    date_str = request.args.get('date')
    limit = request.args.get('limit', 10, type=int)
    sort_by = request.args.get('sort_by', 'qty')

    if not date_str:
        return {"code": 400, "msg": "date参数必填"}, 400

    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return {"code": 400, "msg": "date参数格式应为YYYY-MM-DD"}, 400

    if sort_by not in ('qty', 'amount'):
        return {"code": 400, "msg": "sort_by参数只能是qty或amount"}, 400

    try:
        rows = db.session.execute(
            text("CALL proc_daily_rank(:p_date)"),
            {"p_date": date_str}
        ).mappings().all()

        if not rows:
            return {
                "code": 200,
                "msg": "成功",
                "data": {"count": 0, "list": []}
            }, 200

        data_list = []

        for row in rows:
            book = db.session.execute(
                text("""
                    SELECT author, publisher, price
                    FROM t_book
                    WHERE isbn = :isbn
                """),
                {"isbn": row['isbn']}
            ).mappings().first()

            total_sales_amount = Decimal('0.00')
            if book and book['price'] is not None:
                total_sales_amount = Decimal(row['total_sold']) * book['price']

            data_list.append({
                "isbn": row['isbn'],
                "title": row['title'],
                "author": book['author'] if book else None,
                "publisher": book['publisher'] if book else None,
                "price": float(book['price']) if book else None,
                "total_sold_qty": row['total_sold'],
                "total_sales_amount": float(total_sales_amount)
            })

        # 排序
        key_map = {
            "qty": lambda x: x['total_sold_qty'],
            "amount": lambda x: x['total_sales_amount']
        }
        data_list.sort(key=key_map[sort_by], reverse=True)

        ranked = []
        for idx, item in enumerate(data_list[:limit], start=1):
            item['rank'] = idx
            ranked.append(item)

        return {
            "code": 200,
            "msg": "成功",
            "data": {
                "count": len(ranked),
                "list": ranked
            }
        }, 200

    except Exception as e:
        return {"code": 400, "msg": f"Fail.Reason:{str(e)}"}, 400


# ========== 月榜接口 ==========
@statistic_bp.route('/sales/rank/monthly', methods=['GET'])
def monthly_rank():
    import re
    from decimal import Decimal

    month_str = request.args.get('month')
    limit = request.args.get('limit', 10, type=int)
    sort_by = request.args.get('sort_by', 'qty')

    if not month_str:
        return {"code": 400, "msg": "month参数必填"}, 400

    if not re.match(r'^\d{4}-\d{2}$', month_str):
        return {"code": 400, "msg": "month参数格式应为YYYY-MM"}, 400

    if sort_by not in ('qty', 'amount'):
        return {"code": 400, "msg": "sort_by参数只能是qty或amount"}, 400

    year, month = map(int, month_str.split('-'))

    try:
        rows = db.session.execute(
            text("CALL proc_monthly_rank(:p_year, :p_month)"),
            {"p_year": year, "p_month": month}
        ).mappings().all()

        if not rows:
            return {
                "code": 200,
                "msg": "成功",
                "data": {"count": 0, "list": []}
            }, 200

        data_list = []

        for row in rows:
            book = db.session.execute(
                text("""
                    SELECT author, publisher, price
                    FROM t_book
                    WHERE isbn = :isbn
                """),
                {"isbn": row['isbn']}
            ).mappings().first()

            total_sales_amount = Decimal('0.00')
            if book and book['price'] is not None:
                total_sales_amount = Decimal(row['total_sold']) * book['price']

            data_list.append({
                "isbn": row['isbn'],
                "title": row['title'],
                "author": book['author'] if book else None,
                "publisher": book['publisher'] if book else None,
                "price": float(book['price']) if book else None,
                "total_sold_qty": row['total_sold'],
                "total_sales_amount": float(total_sales_amount)
            })

        # 排序
        key_map = {
            "qty": lambda x: x['total_sold_qty'],
            "amount": lambda x: x['total_sales_amount']
        }
        data_list.sort(key=key_map[sort_by], reverse=True)

        ranked = []
        for idx, item in enumerate(data_list[:limit], start=1):
            item['rank'] = idx
            ranked.append(item)

        return {
            "code": 200,
            "msg": "成功",
            "data": {
                "count": len(ranked),
                "list": ranked
            }
        }, 200

    except Exception as e:
        return {"code": 400, "msg": f"Fail.Reason:{str(e)}"}, 400
