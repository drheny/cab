import requests
import time
import os
from dotenv import load_dotenv
import statistics

# Load environment variables
load_dotenv('/app/frontend/.env')

def test_search_performance():
    backend_url = os.getenv('REACT_APP_BACKEND_URL')
    print(f"Testing search performance at: {backend_url}")
    
    # Initialize demo data
    try:
        response = requests.get(f"{backend_url}/api/init-demo")
        print(f"Demo data init: {response.status_code}")
    except Exception as e:
        print(f"Demo init error: {e}")
    
    # Test individual search queries
    search_terms = ["L", "Li", "Lin", "Lina"]
    response_times = []
    
    print("\nTesting individual search queries:")
    for term in search_terms:
        start_time = time.time()
        try:
            response = requests.get(f"{backend_url}/api/patients?search={term}")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Search '{term}': {response_time:.1f}ms - {len(data['patients'])} results - Status: {response.status_code}")
            else:
                print(f"Search '{term}': {response_time:.1f}ms - Status: {response.status_code}")
                
        except Exception as e:
            print(f"Search '{term}': ERROR - {e}")
    
    if response_times:
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        print(f"\nPerformance Summary:")
        print(f"Average: {avg_time:.1f}ms")
        print(f"Maximum: {max_time:.1f}ms")
        print(f"All times: {[f'{t:.1f}ms' for t in response_times]}")

if __name__ == "__main__":
    test_search_performance()