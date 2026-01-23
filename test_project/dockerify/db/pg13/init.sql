-- Test Database for JOIN Operations
-- This database contains multiple related tables for testing all types of joins

-- Drop tables if they exist
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS coupons;

-- Departments table (added created_at)
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Employees table (with optional department reference)
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    department_id INTEGER REFERENCES departments(id),
    salary DECIMAL(10, 2),
    hire_date DATE
);

-- Categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Products table (added created_at)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(200) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    price DECIMAL(10, 2),
    stock_quantity INTEGER DEFAULT 0,
    properties JSONB,
    has_offer BOOLEAN DEFAULT FALSE,
    offer_type VARCHAR(20) CHECK (offer_type IN ('percent', 'fixed')),
    offer_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    city VARCHAR(100),
    registration_date DATE
);

-- Orders table (references customers)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date DATE NOT NULL,
    total_amount DECIMAL(10, 2),
    status VARCHAR(50)
);

-- Order Items table (many-to-many relationship between orders and products)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2)
);

-- Sales Reports table
CREATE TABLE coupons (
    code VARCHAR(100) NOT NULL PRIMARY KEY,
    value DECIMAL(10, 2) NOT NULL,
    value_type VARCHAR(100) NOT NULL
);

-- Insert Departments (created_at will auto-populate)
INSERT INTO departments (name, location) VALUES
('Engineering', 'San Francisco'),
('Marketing', 'New York'),
('Sales', 'Chicago'),
('HR', 'Boston');
-- Note: IT department has no employees (for testing LEFT/RIGHT joins)

-- Insert Employees (some without departments)
INSERT INTO employees (name, email, department_id, salary, hire_date) VALUES
('Alice Johnson', 'alice@example.com', 1, 95000, '2022-01-15'),
('Bob Smith', 'bob@example.com', 1, 85000, '2022-03-20'),
('Carol White', 'carol@example.com', 2, 70000, '2021-06-10'),
('David Brown', 'david@example.com', 3, 65000, '2023-02-01'),
('Eve Davis', 'eve@example.com', NULL, 60000, '2023-05-15'),
('Frank Miller', 'frank@example.com', NULL, 55000, '2023-08-20');

-- Insert Categories
INSERT INTO categories (name, description) VALUES
('Electronics', 'Electronic devices and accessories'),
('Books', 'Physical and digital books'),
('Clothing', 'Apparel and accessories'),
('Home & Garden', 'Home improvement and gardening');

-- Insert Products (created_at will auto-populate)
INSERT INTO products (sku, name, category_id, price, stock_quantity, properties, has_offer, offer_type, offer_expires_at) VALUES
('ELEC-LAP-001', 'Laptop', 1, 999.99, 50, '{"brand": "TechPro", "warranty_years": 2, "features": ["16GB RAM", "512GB SSD", "Intel i7"]}', TRUE, 'percent', '2024-12-31 23:59:59+00'),
('ELEC-PHN-002', 'Smartphone', 1, 699.99, 100, '{"brand": "SmartTech", "color": "Midnight Blue", "screen_size": "6.5 inches"}', TRUE, 'fixed', '2024-12-25 23:59:59+00'),
('ELEC-AUD-003', 'Headphones', 1, 149.99, 200, '{"type": "wireless", "noise_cancelling": true, "battery_hours": 30}', FALSE, NULL, NULL),
('BOOK-SQL-001', 'SQL Mastery Book', 2, 45.99, 30, '{"author": "Jane Database", "pages": 450, "edition": 3}', TRUE, 'percent', '2025-01-15 23:59:59+00'),
('BOOK-PYT-002', 'Python Guide', 2, 39.99, 25, '{"author": "John Coder", "level": "intermediate", "isbn": "978-1234567890"}', FALSE, NULL, NULL),
('CLTH-TSH-001', 'T-Shirt', 3, 19.99, 500, '{"sizes": ["S", "M", "L", "XL"], "material": "100% cotton", "colors": ["black", "white", "blue"]}', TRUE, 'fixed', '2024-12-20 23:59:59+00'),
('CLTH-JNS-002', 'Jeans', 3, 49.99, 150, '{"fit": "slim", "material": "denim", "wash": "dark blue"}', FALSE, NULL, NULL),
('BOOK-NOV-003', 'Mystery Novel', NULL, 12.99, 75, '{"author": "A. Mystery", "genre": "thriller", "bestseller": true}', TRUE, 'percent', '2025-02-01 23:59:59+00'),
('HOME-LMP-001', 'Desk Lamp', NULL, 29.99, 80, '{"wattage": 40, "adjustable": true, "bulb_type": "LED"}', FALSE, NULL, NULL);

-- Insert Customers
INSERT INTO customers (name, email, phone, city, registration_date) VALUES
('John Doe', 'john@example.com', '555-0101', 'Seattle', '2023-01-10'),
('Jane Smith', 'jane@example.com', '555-0102', 'Portland', '2023-02-15'),
('Mike Johnson', 'mike@example.com', '555-0103', 'Denver', '2023-03-20'),
('Sarah Williams', 'sarah@example.com', '555-0104', 'Austin', '2023-04-25'),
('Tom Brown', 'tom@example.com', '555-0105', 'Miami', '2023-05-30');
-- Note: Customer with id 5 (Tom Brown) has no orders (for testing joins)

-- Insert Orders (not all customers have orders)
INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES
(1, '2024-01-15', 1149.98, 'completed'),
(1, '2024-02-20', 45.99, 'completed'),
(2, '2024-02-10', 699.99, 'completed'),
(2, '2024-03-15', 199.98, 'shipped'),
(3, '2024-03-01', 999.99, 'processing'),
(4, '2024-03-20', 69.98, 'completed');

-- Insert Order Items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
-- Order 1 items
(1, 1, 1, 999.99),
(1, 3, 1, 149.99),
-- Order 2 items
(2, 4, 1, 45.99),
-- Order 3 items
(3, 2, 1, 699.99),
-- Order 4 items
(4, 6, 10, 19.99),
-- Order 5 items
(5, 1, 1, 999.99),
-- Order 6 items
(6, 7, 1, 49.99),
(6, 6, 1, 19.99);

-- Create some useful indexes
CREATE INDEX idx_employees_dept ON employees(department_id);
CREATE INDEX idx_products_cat ON products(category_id);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- Display summary
SELECT 'Database initialized successfully!' as message;
SELECT 'Tables created: departments, employees, categories, products, customers, orders, order_items' as info;
