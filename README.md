# Microservices Testing Demo with CI/CD

**Demo project showing automated testing in microservices: Unit, Integration, and E2E tests with CI/CD pipeline.**

## Architecture

- **User Service** (5001) - User management
- **Product Service** (5002) - Product inventory
- **Order Service** (5003) - Order processing (calls User & Product services)

## Test Types

1. **Unit Tests** - Test individual functions in isolation
2. **Integration Tests** - Test service workflows with HTTP calls
3. **E2E Tests** - Test complete flows across all services

## How to Present This Demo

### 1. Show Tests Passing ✅

Run all tests locally:
```bash
# Unit tests (fast, isolated)
cd user-service && python -m pytest tests/test_unit.py -v
cd product-service && python -m pytest tests/test_unit.py -v
cd order-service && python -m pytest tests/test_unit.py -v

# Integration tests (service workflows)
cd user-service && python -m pytest tests/test_integration.py -v
cd product-service && python -m pytest tests/test_integration.py -v
cd order-service && python -m pytest tests/test_integration.py -v
```

Push to trigger CI/CD pipeline - all tests pass ✅

### 2. Show Tests Failing ❌

**Pick ONE service to demonstrate failure:**

#### Option A: User Service
Edit `user-service/app.py` - comment out the working function (lines 84-96) and uncomment the broken version (lines 103-114)

#### Option B: Product Service
Edit `product-service/app.py` - comment out the working function (lines 127-141) and uncomment the broken version (lines 148-161)

#### Option C: Order Service
Edit `order-service/app.py` - comment out the working function (lines 122-138) and uncomment the broken version (lines 145-159)

**Then:**
```bash
# Run tests locally to see failures
cd <service-you-modified> && python -m pytest tests/test_unit.py -v

# Commit and push
git add .
git commit -m "Demo: introduce bug to show test failure"
git push
```

CI/CD pipeline fails ❌ - shows exactly which tests caught the bugs!

### 3. Key Points to Emphasize

- **Unit tests** catch bugs in business logic (wrong types, incorrect calculations)
- **Integration tests** verify service workflows (create → retrieve → validate)
- **E2E tests** ensure the complete system works together
- **CI/CD pipeline** blocks bad code from being merged
- Tests run automatically on every push
- Fast feedback loop for developers

## Quick Test Commands

```bash
# All unit tests
python -m pytest */tests/test_unit.py -v

# All integration tests
python -m pytest */tests/test_integration.py -v

# E2E tests (requires services running)
python -m pytest tests/test_e2e.py -v
```

## CI/CD Pipeline

`.github/workflows/ci-tests.yml` runs:
- Unit tests (all services in parallel)
- Integration tests (all services in parallel)
- E2E tests (full system test)
- Only passes if ALL tests pass

---

**TL;DR for Presentation:**
1. Show all tests passing (green pipeline)
2. Uncomment broken function in any service
3. Push and show pipeline failing with clear error messages
4. Explain how this prevents bugs in production
