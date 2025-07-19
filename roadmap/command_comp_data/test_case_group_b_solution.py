# Simple debugging task for A/B testing - FIXED
def process_data(items):
    results = []
    for item in items:
        if item > 0:
            results.append(item * 2)
        else:
            results.append(item * -1)  # Fixed: multiply by -1 instead of dividing by 0
    return results

# Test with this data
test_data = [1, 2, -1, 3, 0, 4]
print("Processing:", test_data)
print("Result:", process_data(test_data))