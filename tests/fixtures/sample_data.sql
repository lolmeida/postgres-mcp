-- Sample data for PostgreSQL MCP integration tests

-- Insert sample users
INSERT INTO public.users (name, email, active)
VALUES 
    ('Test User 1', 'user1@example.com', true),
    ('Test User 2', 'user2@example.com', true),
    ('Test User 3', 'user3@example.com', false),
    ('Test User 4', 'user4@example.com', true),
    ('Test User 5', 'user5@example.com', false);

-- Insert sample products with various data types
INSERT INTO public.products (name, description, price, inventory, categories, attributes, location, active)
VALUES 
    ('Product 1', 'This is product 1', 19.99, 100, ARRAY['electronics', 'gadgets'], 
     '{"color": "black", "weight": 1.5, "dimensions": {"width": 10, "height": 5}}', 
     point(40.7128, -74.0060), true),
    
    ('Product 2', 'This is product 2', 29.99, 50, ARRAY['home', 'kitchen'], 
     '{"color": "white", "material": "ceramic"}', 
     point(34.0522, -118.2437), true),
     
    ('Product 3', 'This is product 3', 9.99, 0, ARRAY['office', 'supplies'], 
     '{"color": "blue", "size": "medium"}', 
     point(51.5074, -0.1278), false),
     
    ('Product 4', 'This is product 4', 49.99, 25, ARRAY['electronics', 'computers'], 
     '{"color": "silver", "storage": "1TB", "memory": "16GB"}', 
     point(37.7749, -122.4194), true),
     
    ('Product 5', 'This is product 5', 14.99, 75, ARRAY['clothing', 'accessories'], 
     '{"color": "red", "size": "large", "material": "cotton"}', 
     point(52.5200, 13.4050), true);

-- Insert sample orders
INSERT INTO public.orders (user_id, total_amount, status, items)
VALUES 
    (1, 49.97, 'completed', '[
        {"product_id": 1, "quantity": 2, "price": 19.99},
        {"product_id": 3, "quantity": 1, "price": 9.99}
    ]'),
    
    (2, 29.99, 'pending', '[
        {"product_id": 2, "quantity": 1, "price": 29.99}
    ]'),
    
    (1, 64.98, 'processing', '[
        {"product_id": 4, "quantity": 1, "price": 49.99},
        {"product_id": 5, "quantity": 1, "price": 14.99}
    ]'),
    
    (3, 19.99, 'cancelled', '[
        {"product_id": 1, "quantity": 1, "price": 19.99}
    ]'),
    
    (4, 39.98, 'completed', '[
        {"product_id": 3, "quantity": 4, "price": 9.99}
    ]');

-- Insert data in test_schema
INSERT INTO test_schema.test_table (name, value)
VALUES 
    ('Test 1', 100),
    ('Test 2', 200),
    ('Test 3', 300); 