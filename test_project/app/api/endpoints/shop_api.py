from datetime import date

from fastapi import APIRouter, Request, Response

from fastpg import OrderBy, Prefetch, ReturnType, OnConflict
from fastpg.db import ASYNC_DB_WRITE

from app.schemas.shop import (
    Category,
    Product,
    Customer,
    Order,
    OrderItem,
    Department,
    Employee,
    Coupon,
)


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


@router.get('/products', status_code=200)
async def get_products(
    response:Response,
):
    return await Product.async_queryset.all()


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


@router.get('/products/categories', status_code=200)
async def get_categories(
    response:Response,
):
    return await Category.async_queryset.all()


@router.post('/transactions/commit', status_code=200)
async def create_department_and_employee_with_commit(request: Request):
    payload = await request.json()

    transaction = await ASYNC_DB_WRITE.transaction()
    try:
        department = await Department.async_queryset.with_transaction(transaction).create(
            name=payload.get('department_name', 'Transactional Ops'),
            location=payload.get('department_location', 'Remote'),
        )

        employee = await Employee.async_queryset.with_transaction(transaction).create(
            department_id=department.id,
            name=payload.get('employee_name', 'Committed Employee'),
            email=payload.get('employee_email', 'committed.employee@example.com'),
            salary=payload.get('employee_salary', 75000),
            hire_date=date.today(),
        )
    except Exception as exc:
        await transaction.rollback()
        raise exc
    else:
        await transaction.commit()

    return {
        'department': department,
        'employee': employee,
    }


@router.post('/transactions/rollback', status_code=200)
async def create_department_and_employee_with_rollback(request: Request):
    payload = await request.json()

    transaction = await ASYNC_DB_WRITE.transaction()
    try:
        department = await Department.async_queryset.with_transaction(transaction).create(
            name=payload.get('department_name', 'Rollback Ops'),
            location=payload.get('department_location', 'Unknown'),
        )

        await Employee.async_queryset.with_transaction(transaction).create(
            department_id=department.id,
            name=payload.get('employee_name', 'Will Rollback'),
            email=payload.get('employee_email', 'rollback.employee@example.com'),
            salary=payload.get('employee_salary', 60000),
            hire_date=date.today(),
        )

        # Trigger a failure so we can test rollback behaviour
        raise ValueError('Forcing rollback for transaction demo')
    except Exception as exc:
        await transaction.rollback()
        return {
            'rolled_back': True,
            'error': str(exc),
        }


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
