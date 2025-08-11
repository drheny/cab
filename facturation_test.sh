#!/bin/bash
"""
Enhanced Facturation Endpoints Testing using curl
Testing all 8 new facturation endpoints with comprehensive validation
"""

# Configuration
BACKEND_URL="https://e095a16b-4f79-4d50-8576-cad954291484.preview.emergentagent.com"
API_BASE="${BACKEND_URL}/api"
AUTH_HEADER="Authorization: Bearer auto-login-token"

echo "🚀 ENHANCED FACTURATION ENDPOINTS TESTING"
echo "============================================================"
echo "Backend URL: $BACKEND_URL"
echo "Testing Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Initialize demo data
echo "ℹ️  Initializing demo data..."
curl -s -H "$AUTH_HEADER" "$API_BASE/init-demo" > /dev/null
echo "✅ Demo data initialized"
echo ""

# Get patient IDs for testing
echo "ℹ️  Fetching patient IDs..."
PATIENT_RESPONSE=$(curl -s -H "$AUTH_HEADER" "$API_BASE/patients?limit=5")
PATIENT_ID=$(echo "$PATIENT_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "✅ Found patient ID: $PATIENT_ID"
echo ""

# Test results array
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local test_name="$1"
    local endpoint="$2"
    local expected_fields="$3"
    
    echo "============================================================"
    echo "🧪 TESTING: $test_name"
    echo "============================================================"
    echo "📡 GET $API_BASE$endpoint"
    
    # Make request
    RESPONSE=$(curl -s -H "$AUTH_HEADER" "$API_BASE$endpoint")
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -H "$AUTH_HEADER" "$API_BASE$endpoint")
    
    echo "   Status: $HTTP_CODE"
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ $test_name endpoint working!"
        
        # Check if response is valid JSON
        if echo "$RESPONSE" | jq . > /dev/null 2>&1; then
            echo "✅ Valid JSON response"
            
            # Check required fields
            IFS=',' read -ra FIELDS <<< "$expected_fields"
            for field in "${FIELDS[@]}"; do
                if echo "$RESPONSE" | jq -e ".$field" > /dev/null 2>&1; then
                    VALUE=$(echo "$RESPONSE" | jq -r ".$field")
                    echo "✅ ✓ $field: $VALUE"
                else
                    echo "❌ ✗ Missing field: $field"
                fi
            done
            
            # Show sample response (first 200 chars)
            echo "📄 Sample response:"
            echo "$RESPONSE" | jq . | head -10
            
            PASSED=$((PASSED + 1))
        else
            echo "❌ Invalid JSON response"
            echo "Response: $RESPONSE"
            FAILED=$((FAILED + 1))
        fi
    else
        echo "❌ $test_name endpoint failed!"
        echo "   Error: $RESPONSE"
        FAILED=$((FAILED + 1))
    fi
    echo ""
}

# Test 1: Enhanced Stats
test_endpoint "Enhanced Facturation Stats" "/facturation/enhanced-stats" "recette_jour,recette_mois,recette_annee,nouveaux_patients_annee"

# Test 2: Daily Payments
test_endpoint "Daily Payments" "/facturation/daily-payments?date=2025-01-28" "date,payments,totals"

# Test 3: Monthly Stats
test_endpoint "Monthly Statistics" "/facturation/monthly-stats?year=2025&month=1" "year,month,recette_mois,nb_visites,nb_controles"

# Test 4: Yearly Stats
test_endpoint "Yearly Statistics" "/facturation/yearly-stats?year=2025" "year,recette_annee,nb_visites,nb_controles"

# Test 5: Patient Payments (using found patient ID)
if [ -n "$PATIENT_ID" ]; then
    test_endpoint "Patient Payments" "/facturation/patient-payments?patient_id=$PATIENT_ID" "patient,payments,total_paye,nb_payments"
else
    echo "============================================================"
    echo "🧪 TESTING: Patient Payments"
    echo "============================================================"
    echo "❌ No patient ID available for testing"
    FAILED=$((FAILED + 1))
    echo ""
fi

# Test 6: Top Patients
test_endpoint "Top Profitable Patients" "/facturation/top-patients?limit=10" "top_patients,total_analyzed"

# Test 7: Evolution Graphs
test_endpoint "Evolution Graphs" "/facturation/evolution-graphs?period=month&year=2025" "period,year,evolution"

# Test 8: Predictive Analysis
test_endpoint "Predictive Analysis" "/facturation/predictive-analysis" "ai_analysis,historical_data,peak_months,trough_months"

# Final Results
echo "============================================================"
echo "🧪 TESTING: FINAL TEST RESULTS"
echo "============================================================"

TOTAL=$((PASSED + FAILED))
SUCCESS_RATE=$(echo "scale=1; $PASSED * 100 / $TOTAL" | bc -l)

echo "📊 SUMMARY:"
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo "📈 Success Rate: ${SUCCESS_RATE}%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED! Enhanced facturation endpoints are working correctly."
    exit 0
else
    echo "⚠️  $FAILED test(s) failed. Please check the implementation."
    exit 1
fi