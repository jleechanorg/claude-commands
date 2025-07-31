# Simple debugging task for A/B testing
def process_data(items):
    results = []
    for item in items:
        if item > 0:
            results.append(item * 2)
        else:
            results.append(item)  # Fixed: return unchanged instead of division by zero
    return results


# Test with this data
test_data = [1, 2, -1, 3, 0, 4]
print("Processing:", test_data)
print("Result:", process_data(test_data))
