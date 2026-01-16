from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Response

from fastpg import (
    OrderBy,
    Prefetch,
    ReturnType,
    OnConflict,
)
from fastpg import CONNECTION_MANAGER

from app.schemas.shop import (
    Category,
    Product,
    Customer,
    Order,
    OrderItem,
    Department,
    Employee,
    Coupon,
    OfferTypes,
)

import pytz
IST_TZ = pytz.timezone("Asia/Kolkata")


router = APIRouter()


@router.get('/employees', status_code=200)
async def get_employees(
    response:Response,
    department:str|None = None,
    salary:float|None = None,
):
    employees = Employee.async_queryset.select_related('department').all()
    if salary or department:
        if salary:
            employees = employees.filter(salary__gte=salary)
        if department:
            employees = employees.filter_related(department__name=department)
    return await employees.order_by(salary=OrderBy.DESCENDING)


@router.get('/employee', status_code=200)
async def get_employee(
    response:Response,
    id:int,
):
    return await Employee.async_queryset.select_related('department').get(id=id)


@router.get('/departments', status_code=200)
async def get_departments(
    response:Response,
):
    departments = await Department.async_queryset.prefetch_related(
        Prefetch('employees', Employee.async_queryset.all())
    ).all().return_as(ReturnType.DICT)
    return departments


@router.get('/department', status_code=200)
async def get_department(
    response:Response,
    id:int,
):
    departments = await Department.async_queryset.prefetch_related(
        Prefetch('employees', Employee.async_queryset.filter(salary__gte=0))
    ).get(id=id).return_as(ReturnType.MODEL_INSTANCE)
    return departments


@router.post('/department/create', status_code=200)
async def create_department_with_employees(
    request:Request,
    response:Response,
):
    data = await request.json()
    department_data = data['department']
    employees_data = data['employees']

    async def __create_without_txn(department_data, employees_data):
        # Only department gets created if this function has errors
        department = await Department.async_queryset.create(**department_data)
        for emp in employees_data:
            # emp['department_id'] = department.id  # Comment this line to create an error mid txn
            await Employee.async_queryset.create(**emp)
        return department

    async def __create_with_txn(department_data, employees_data):
        async with CONNECTION_MANAGER.transaction():
            department = await Department.async_queryset.create(**department_data)
            for emp in employees_data:
                # emp['department_id'] = department.id  # Comment this line to create an error mid txn
                await Employee.async_queryset.create(**emp)
            return department
    
    @CONNECTION_MANAGER.transaction()
    async def __create_with_decorator_txn(department_data, employees_data):
        department = await Department.async_queryset.create(**department_data)
        for emp in employees_data:
            # emp['department_id'] = department.id  # Comment this line to create an error mid txn
            await Employee.async_queryset.create(**emp)
        return department
    
    async def __create_with_try_catch_txn(department_data, employees_data):
        transaction = await CONNECTION_MANAGER.transaction()
        try:
            department = await Department.async_queryset.create(**department_data)
            for emp in employees_data:
                # emp['department_id'] = department.id  # Comment this line to create an error mid txn
                await Employee.async_queryset.create(**emp)
        except Exception as e:
            await transaction.rollback()
            raise e
        else:
            await transaction.commit()
        return department
    
    # department = await __create_without_txn(department_data, employees_data)
    # department = await __create_with_txn(department_data, employees_data)
    # department = await __create_with_decorator_txn(department_data, employees_data)
    department = await __create_with_try_catch_txn(department_data, employees_data)

    return await Department.async_queryset.prefetch_related(
        Prefetch('employees', Employee.async_queryset.all())
    ).get(id=department.id).return_as(ReturnType.DICT)


@router.get('/products', status_code=200)
async def get_products(
    response:Response,
    id:int|None=None,
):
    if id:
        return await Product.async_queryset.get(id=id)
    return await Product.async_queryset.all().order_by(id=OrderBy.ASCENDING)


@router.get('/products/categories', status_code=200)
async def get_categories(
    response:Response,
):
    return await Category.async_queryset.all()


@router.post('/products', status_code=200)
async def create_products_in_bulk(
    request:Request,
    response:Response,
):
    products_batch = await request.json()
    # await Product.async_queryset.bulk_create(
    #     products_batch, on_conflict=OnConflict.DO_NOTHING)
    await Product.async_queryset.bulk_create(
        products_batch, on_conflict=OnConflict.UPDATE,
        conflict_target=['sku'],
        update_fields=['name', 'category_id', 'price', 'stock_quantity'])
    return {}


@router.post('/products/update-or-create', status_code=200)
async def update_or_create_product(
    request:Request,
    response:Response,
):
    data = await request.json()
    
    id = data['id']
    sku = data['sku']
    del data['id']
    del data['sku']

    product, created = await Product.async_queryset.update_or_create(
        id=id, sku=sku,
        defaults=data)
    return {
        'product': product,
        'created': created
    }
    

@router.post('/products/update-stock-qtty', status_code=200)
async def update_product_stock_qtty(
    request:Request,
):
    data = await request.json()
    product_id = data['product_id']
    quick_action = data['quick_action']  # Options None, "add", "sub", "mul", "div"
    value = data['value']

    # Demonstrating update suffixes
    if quick_action == 'add':
        updated = await Product.async_queryset.filter(id=product_id).update(stock_quantity__add=value)
    elif quick_action == 'sub':
        updated = await Product.async_queryset.filter(id=product_id).update(stock_quantity__sub=value)
    elif quick_action == 'mul':
        updated = await Product.async_queryset.filter(id=product_id).update(stock_quantity__mul=value)
    elif quick_action == 'div':
        updated = await Product.async_queryset.filter(id=product_id).update(stock_quantity__div=value)
    else:
        updated = await Product.async_queryset.filter(id=product_id).update(stock_quantity=value)
    return {'updated': updated}


@router.post('/products/update-properties', status_code=200)
async def update_product_properties(
    request:Request,
):
    data = await request.json()
    product_id = data['product_id']
    action = data['action']  # Options: "set_key", "remove_key", "reset"
    value = data['value']

    if action == 'set_key':
        key = data['key']
        update_vals = {}
        update_vals[f'properties__jsonb_set__{key}'] = value
        updated = await Product.async_queryset.filter(id=product_id).update(**update_vals)
    elif action == 'remove_key':
        key = data['key']
        updated = await Product.async_queryset.filter(id=product_id).update(properties__jsonb_remove=key)
    elif action == 'reset':
        updated = await Product.async_queryset.filter(id=product_id).update(properties__jsonb=value)
    return {'updated': updated}


@router.post('/products/update-offer', status_code=200)
async def update_product_offer(
    request:Request,
):
    data = await request.json()
    product_id = data['product_id']
    action = data['action']  # Options: "reset", "extend", "shorten"
    value = data['value']

    if action == 'reset':
        updated = await Product.async_queryset.filter(id=product_id).update(
            has_offer=True,
            offer_type=OfferTypes.PERCENTAGE,
            offer_expires_at=datetime.now().astimezone(IST_TZ) + timedelta(days=value))
    elif action == 'extend':
        updated = await Product.async_queryset.filter(id=product_id, offer_expires_at__isnull=False).update(
            has_offer=True,
            offer_type=OfferTypes.PERCENTAGE,
            offer_expires_at__add_time=value)
    elif action == 'shorten':
        updated = await Product.async_queryset.filter(id=product_id, offer_expires_at__isnull=False).update(
            has_offer=True,
            offer_type=OfferTypes.PERCENTAGE,
            offer_expires_at__sub_time=value)
    return {'updated': updated}


@router.get('/customers', status_code=200)
async def get_customers(
    response:Response,
):
    return await Customer.async_queryset.all()


@router.get('/orders', status_code=200)
async def get_orders(
    response:Response,
):
    orders = await Order.async_queryset.prefetch_related(
        Prefetch('line_items', OrderItem.async_queryset.select_related('product').all())
    ).all()
    return orders


@router.get('/order', status_code=200)
async def get_order(
    response:Response,
    id:int,
):
    order = await Order.async_queryset.prefetch_related(
        Prefetch('line_items', OrderItem.async_queryset.select_related('product').all())
    ).get(id=id)
    return order


@router.post('/coupons/get_or_create', status_code=200)
async def get_or_create_coupon(
    coupon:Coupon,
    response:Response,
):
    coupon, created = await Coupon.async_queryset.get_or_create(
        code=coupon.code,
        defaults={
            'value': coupon.value,
            'value_type': coupon.value_type
        })
    return {
        'coupon': coupon,
        'newly_created': created
    }
