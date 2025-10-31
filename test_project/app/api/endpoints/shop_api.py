from fastapi import APIRouter, Response

from fastpg import OrderBy

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
async def modules(
    response:Response,
    department:str|None = None,
    salary:float|None = None,
):
    employees = Employee.async_queryset.select_related('department')
    if salary or department:
        if salary:
            employees = employees.filter(salary__gte=salary)
        if department:
            employees = employees.filter_related(department=department).filter(salary__gte=0)
    else:
        employees = employees.all()
    return await employees.order_by(salary=OrderBy.DESCENDING)


@router.get('/products', status_code=200)
async def modules(
    response:Response,
):
    return await Product.async_queryset.all()


@router.get('/customers', status_code=200)
async def modules(
    response:Response,
):
    return await Customer.async_queryset.all()


@router.get('/orders', status_code=200)
async def modules(
    response:Response,
):
    return await OrderItem.async_queryset.select_related('order', 'product').all()
