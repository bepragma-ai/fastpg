from fastapi import APIRouter, Response

from fastpg import OrderBy, Prefetch, ReturnType

from app.schemas.shop import (
    Product,
    Customer,
    Order,
    OrderItem,
    Department,
    Employee,
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


@router.get('/products', status_code=200)
async def get_products(
    response:Response,
):
    return await Product.async_queryset.all()


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
