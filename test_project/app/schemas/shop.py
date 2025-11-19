from __future__ import annotations
from datetime import date

from enum import Enum

from fastpg import DatabaseModel, Relation

import pytz
IST_TZ = pytz.timezone("Asia/Kolkata")


class Category(DatabaseModel):
    id:int|None = None
    name:str
    description:str

    class Meta:
        db_table = 'categories'
        primary_key = 'id'
        auto_generated_fields = ['id']


class Product(DatabaseModel):
    id:int|None = None
    sku:str
    name:str
    category_id:int|None = None
    price:float
    stock_quantity:int

    class Meta:
        db_table = 'products'
        primary_key = 'id'
        auto_generated_fields = ['id']
        relations = {
            'category': Relation(Category, foreign_field='order_id'),
        }


class Customer(DatabaseModel):
    id:int|None = None
    name:str
    email:str
    phone:str
    city:str
    registration_date:date

    class Meta:
        db_table = 'customers'
        primary_key = 'id'
        auto_generated_fields = ['id']
        auto_now_add_fields = ['created_at']


class Order(DatabaseModel):
    id:int|None = None
    customer_id:int
    order_date:date
    total_amount:float
    status:str

    class Meta:
        db_table = 'orders'
        primary_key = 'id'
        auto_generated_fields = ['id']


class OrderItem(DatabaseModel):
    id:int|None = None
    order_id:int
    product_id:int
    quantity:int
    unit_price:float

    class Meta:
        db_table = 'order_items'
        primary_key = 'id'
        auto_generated_fields = ['id']
        relations = {
            'order': Relation(Order, foreign_field='order_id'),
            'product': Relation(Product, foreign_field='product_id'),
        }


class Department(DatabaseModel):
    id:int|None = None
    name:str
    location:str

    class Meta:
        db_table = 'departments'
        primary_key = 'id'
        auto_generated_fields = ['id']


class Employee(DatabaseModel):
    id:int|None = None
    department_id:int|None
    name:str
    email:str
    salary:float
    hire_date:date

    class Meta:
        db_table = 'employees'
        primary_key = 'id'
        auto_generated_fields = ['id']
        relations = {
            'department': Relation(Department, foreign_field='department_id'),
        }


class CouponTypes(str, Enum):
    PERCENTAGE = 'percentage'
    FIXED = 'fixed'


class Coupon(DatabaseModel):
    code:str
    value:float
    value_type:CouponTypes

    class Meta:
        db_table = 'coupons'
        primary_key = 'code'
