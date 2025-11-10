# Microservices Testing with CI/CD Pipeline

A demonstration of automated testing in a microservices architecture using GitHub Actions CI/CD.

## Architecture

Three simple Flask microservices:
- **User Service** (port 5001) - Manages user data
- **Product Service** (port 5002) - Manages product inventory
- **Order Service** (port 5003) - Processes orders, calls User and Product services

## Testing Strategy

Each service has **unit tests** that run automatically via GitHub Actions:
- Tests business logic in isolation
- Uses mocks for external dependencies
- Fast execution, no network calls

## CI/CD Pipeline

The pipeline (`.github/workflows/ci-tests.yml`) runs on every push:

1. Tests each service independently in parallel
2. If all tests pass ✅ → Pipeline succeeds
3. If any test fails ❌ → Pipeline fails and blocks merge

## Demo Scenarios

### Scenario 1: Non-Breaking Change ✅
Make a harmless change (add comment, format code):
```bash
# Edit any service file, add a comment or whitespace
git add .
git commit -m "Add documentation comment"
git push
```
**Result:** All tests pass, pipeline succeeds

### Scenario 2: Breaking Change ❌
Introduce a bug (change return value, break logic):
```bash
# Example: Break user validation in user-service/app.py
# Change: return jsonify({"valid": True, ...})
# To:     return jsonify({"valid": "broken", ...})
git add .
git commit -m "Break user validation"
git push
```
**Result:** Tests fail, pipeline blocks merge

## Running Tests Locally

```bash
# Test individual services
cd user-service && python -m pytest tests/test_unit.py -v
cd product-service && python -m pytest tests/test_unit.py -v
cd order-service && python -m pytest tests/test_unit.py -v
```

## Key Takeaway

**Automated testing catches bugs before they reach production.** The CI/CD pipeline acts as a quality gate, ensuring only working code is merged.
