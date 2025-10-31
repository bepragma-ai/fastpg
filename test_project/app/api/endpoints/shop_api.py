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
    salary:float|None = None,
):
    employees = Employee.async_queryset.select_related('department')
    if salary:
        return await employees.filter(salary__gte=salary).order_by(salary=OrderBy.DESCENDING)
    else:
        return await employees.all().order_by(salary=OrderBy.DESCENDING)


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
    return await Order.async_queryset.all()
