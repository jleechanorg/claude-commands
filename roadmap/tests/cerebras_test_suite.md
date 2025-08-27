# Cerebras Code Generation Test Suite

## Overview
This document defines a comprehensive test suite for evaluating the Cerebras direct script's code generation capabilities across various programming tasks and complexity levels, including the newly added --light mode functionality.

## Test Categories

### 1. Basic Functions
Simple, single-purpose functions that demonstrate core programming concepts.

### 2. Data Structures & Algorithms
Implementation of common data structures and algorithms with optimization techniques.

### 3. Web Development
Full-stack web applications, APIs, and frontend components.

### 4. Database Integration
Database models, queries, and ORM usage patterns.

### 5. Testing & Validation
Unit tests, integration tests, and validation logic.

### 6. System Design
Complete system implementations with multiple components.

### 7. Mode Comparison Tests
Tests to compare default mode vs light mode functionality.

## Test Matrix

| Category | Task | Description | Expected Complexity |
|----------|------|-------------|---------------------|
| Basic Functions | 1 | Simple addition function | 10-20 lines |
| Basic Functions | 2 | String reversal function | 10-20 lines |
| Basic Functions | 3 | Palindrome checker | 15-25 lines |
| Data Structures | 4 | Stack implementation | 30-50 lines |
| Data Structures | 5 | Queue implementation | 30-50 lines |
| Data Structures | 6 | Binary search tree | 80-120 lines |
| Algorithms | 7 | Fibonacci with memoization | 40-60 lines |
| Algorithms | 8 | Sorting algorithm (merge sort) | 30-50 lines |
| Algorithms | 9 | Search algorithm (binary search) | 20-30 lines |
| Web Development | 10 | Flask REST API endpoint | 25-40 lines |
| Web Development | 11 | React component (product card) | 30-50 lines |
| Web Development | 12 | Simple HTML page with CSS | 50-80 lines |
| Database Integration | 13 | SQLAlchemy User model | 30-50 lines |
| Database Integration | 14 | Database migration script | 40-60 lines |
| Database Integration | 15 | CRUD operations with SQLite | 60-100 lines |
| Testing | 16 | Pytest unit tests for Calculator | 40-60 lines |
| Testing | 17 | Integration test for Auth system | 50-80 lines |
| Testing | 18 | Mock data generation utility | 30-50 lines |
| System Design | 19 | E-commerce product catalog | 150-250 lines |
| System Design | 20 | User authentication system | 100-200 lines |
| Mode Comparison | 21 | Amazon MVP Design Document | 100-200 lines |
| Mode Comparison | 22 | Default Mode vs Light Mode Performance | 10-20 lines |
| Mode Comparison | 23 | Security Filtering Test | 10-20 lines |

## Detailed Test Prompts

### Basic Functions

1. **Simple Addition Function**
   ```
   Write a Python function that takes two numbers as parameters and returns their sum. Include type hints and a docstring with examples.
   ```

2. **String Reversal Function**
   ```
   Create a Python function that reverses a string. Handle edge cases like empty strings and None values. Include comprehensive documentation.
   ```

3. **Palindrome Checker**
   ```
   Write a Python function that checks if a given string is a palindrome. Ignore case, spaces, and punctuation. Include error handling and examples.
   ```

### Data Structures & Algorithms

4. **Stack Implementation**
   ```
   Implement a Stack data structure in Python with push, pop, peek, and is_empty methods. Include proper error handling for edge cases.
   ```

5. **Queue Implementation**
   ```
   Create a Queue class in Python with enqueue, dequeue, front, rear, and is_empty methods. Use a circular buffer approach for efficiency.
   ```

6. **Binary Search Tree**
   ```
   Implement a complete Binary Search Tree in Python with insert, delete, search, and traversal methods. Include proper node structure and error handling.
   ```

7. **Fibonacci with Memoization**
   ```
   Write a Python function to calculate Fibonacci numbers using memoization for optimization. Include performance comparison with naive recursive approach.
   ```

8. **Merge Sort Algorithm**
   ```
   Implement merge sort algorithm in Python. Include detailed comments explaining the divide and conquer approach. Add example usage.
   ```

9. **Binary Search Algorithm**
   ```
   Create a binary search function in Python that works with sorted lists. Include time complexity analysis and edge case handling.
   ```

### Web Development

10. **Flask REST API Endpoint**
    ```
    Write a Flask REST API endpoint for user registration that validates email format and password strength. Return appropriate HTTP status codes.
    ```

11. **React Product Card Component**
    ```
    Create a React component for a product card that displays image, title, price, and rating. Use functional components with hooks.
    ```

12. **HTML Page with CSS**
    ```
    Generate a complete HTML page with embedded CSS for a product listing page. Include responsive design and modern UI elements.
    ```

### Database Integration

13. **SQLAlchemy User Model**
    ```
    Create a SQLAlchemy User model with fields for id, username, email, password_hash, and created_at. Include validation and relationship examples.
    ```

14. **Database Migration Script**
    ```
    Write a Python script using Alembic to create a migration that adds a 'last_login' field to the User table. Include downgrade functionality.
    ```

15. **CRUD Operations with SQLite**
    ```
    Implement complete CRUD operations in Python for a Product entity using SQLite. Include proper error handling and connection management.
    ```

### Testing

16. **Pytest Unit Tests for Calculator**
    ```
    Write comprehensive pytest unit tests for a Calculator class with add, subtract, multiply, and divide methods. Include edge cases and error conditions.
    ```

17. **Integration Test for Auth System**
    ```
    Create an integration test for a user authentication system that tests registration, login, and session management flows.
    ```

18. **Mock Data Generation Utility**
    ```
    Write a Python utility function that generates mock user data for testing purposes. Include realistic names, emails, and addresses.
    ```

### System Design

19. **E-commerce Product Catalog**
    ```
    Design a complete e-commerce product catalog system in Python with Product, Category, and Inventory classes. Include search and filter functionality.
    ```

20. **User Authentication System**
    ```
    Create a complete user authentication system with registration, login, password reset, and session management. Use secure password hashing.
    ```

### Mode Comparison Tests

21. **Amazon MVP Design Document**
    ```
    Create a comprehensive design document for an Amazon.com MVP replication including user management, product catalog, shopping cart, checkout process, and admin panel. Focus on core e-commerce functionality with a simplified feature set.
    ```

22. **Default Mode vs Light Mode Performance**
    ```
    Compare the performance of the cerebras script in default mode versus light mode by measuring response times and code quality for the same prompt.
    ```

23. **Security Filtering Test**
    ```
    Test the security filtering behavior in default mode vs --light mode with a prompt that contains backticks, which are normally blocked by the security filter.
    ```

## Execution Instructions

To run the full test suite:
```bash
# Run all tests with default parameters
./run_cerebras_test_suite.sh

# Run all tests with light mode (no system prompts and no security filtering)
./run_cerebras_test_suite.sh --light

# Run all enhancement tests
./run_all_cerebras_tests.sh
```

## Evaluation Criteria

1. **Generation Time**: Measure and compare response times
2. **Code Quality**: Check for proper structure, documentation, and error handling
3. **Functionality**: Verify that generated code works as expected
4. **Completeness**: Ensure all requested features are implemented
5. **Best Practices**: Evaluate adherence to language-specific conventions
6. **Mode Behavior**: Verify that --light mode correctly skips system prompts and security filtering