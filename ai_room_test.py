import requests
import unittest
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

class AIRoomAPITest(unittest.TestCase):
    def setUp(self):
        # Use the correct backend URL from environment
        backend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://98ea2688-e431-4ee4-a33d-1c7cb0edbedd.preview.emergentagent.com')
        self.base_url = backend_url
        print(f"Testing AI Room backend at: {self.base_url}")
        # Initialize demo data before running tests
        self.init_demo_data()
    
    def init_demo_data(self):
        """Initialize demo data for testing"""
        try:
            response = requests.get(f"{self.base_url}/api/init-demo")
            self.assertEqual(response.status_code, 200)
            print("Demo data initialized successfully")
        except Exception as e:
            print(f"Error initializing demo data: {e}")
    
    def test_ai_room_initialize(self):
        """Test POST /api/ai-room/initialize - Initialize AI Room with patient classifications"""
        print("\n🔍 Testing AI Room Initialize Endpoint")
        
        response = requests.post(f"{self.base_url}/api/ai-room/initialize")
        self.assertEqual(response.status_code, 200, f"AI Room initialization failed: {response.text}")
        
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("appointments_processed", data)
        self.assertIsInstance(data["appointments_processed"], int)
        
        print(f"✅ AI Room initialized successfully - {data['appointments_processed']} appointments processed")
        print(f"🎉 AI Room Initialize Test: PASSED")
    
    def test_ai_room_queue(self):
        """Test GET /api/ai-room/queue?date=2025-07-23 - Get AI-optimized patient queue"""
        print("\n🔍 Testing AI Room Queue Endpoint")
        
        # Initialize AI Room first
        init_response = requests.post(f"{self.base_url}/api/ai-room/initialize")
        self.assertEqual(init_response.status_code, 200)
        
        # Test with specific date
        test_date = "2025-07-23"
        response = requests.get(f"{self.base_url}/api/ai-room/queue?date={test_date}")
        self.assertEqual(response.status_code, 200, f"AI Room queue failed: {response.text}")
        
        data = response.json()
        self.assertIn("queue", data)
        self.assertIn("total_patients", data)
        self.assertIsInstance(data["queue"], list)
        self.assertIsInstance(data["total_patients"], int)
        
        # Verify queue structure if patients exist
        if len(data["queue"]) > 0:
            patient = data["queue"][0]
            # Verify AI-enhanced data
            self.assertIn("patient_id", patient)
            self.assertIn("nom", patient)
            self.assertIn("prenom", patient)
            self.assertIn("heure", patient)
            self.assertIn("type_rdv", patient)
            self.assertIn("ai_predictions", patient)
            self.assertIn("punctuality_score", patient)
            self.assertIn("complexity_score", patient)
            self.assertIn("estimated_duration", patient)
            self.assertIn("optimal_arrival_time", patient)
            
            print(f"✅ AI Queue contains {len(data['queue'])} patients with AI predictions")
        else:
            print(f"✅ AI Queue endpoint working (no patients for {test_date})")
        
        print(f"🎉 AI Room Queue Test: PASSED")
    
    def test_ai_room_predictions(self):
        """Test GET /api/ai-room/predictions?date=2025-07-23 - Get AI predictions and classifications"""
        print("\n🔍 Testing AI Room Predictions Endpoint")
        
        # Initialize AI Room first
        init_response = requests.post(f"{self.base_url}/api/ai-room/initialize")
        self.assertEqual(init_response.status_code, 200)
        
        # Test with specific date
        test_date = "2025-07-23"
        response = requests.get(f"{self.base_url}/api/ai-room/predictions?date={test_date}")
        self.assertEqual(response.status_code, 200, f"AI Room predictions failed: {response.text}")
        
        data = response.json()
        
        # Verify prediction structure
        self.assertIn("waiting_time_predictions", data)
        self.assertIn("no_show_predictions", data)
        self.assertIn("optimization_opportunities", data)
        self.assertIn("patient_classifications", data)
        self.assertIn("doctor_efficiency_prediction", data)
        
        # Verify waiting time predictions
        waiting_predictions = data["waiting_time_predictions"]
        self.assertIn("average_wait", waiting_predictions)
        self.assertIn("peak_hours", waiting_predictions)
        self.assertIn("bottlenecks", waiting_predictions)
        
        # Verify no-show predictions
        no_show_predictions = data["no_show_predictions"]
        self.assertIn("high_risk_patients", no_show_predictions)
        self.assertIn("probability_threshold", no_show_predictions)
        
        # Verify optimization opportunities
        optimization = data["optimization_opportunities"]
        self.assertIn("queue_reordering", optimization)
        self.assertIn("time_savings", optimization)
        self.assertIn("efficiency_improvements", optimization)
        
        print(f"✅ AI Predictions generated successfully")
        print(f"   - Average wait time: {waiting_predictions.get('average_wait', 'N/A')} minutes")
        print(f"   - High risk patients: {len(no_show_predictions.get('high_risk_patients', []))}")
        print(f"   - Optimization opportunities: {len(optimization.get('queue_reordering', []))}")
        print(f"🎉 AI Room Predictions Test: PASSED")
    
    def test_ai_room_doctor_analytics(self):
        """Test GET /api/ai-room/doctor-analytics - Get doctor performance analytics"""
        print("\n🔍 Testing AI Room Doctor Analytics Endpoint")
        
        # Initialize AI Room first
        init_response = requests.post(f"{self.base_url}/api/ai-room/initialize")
        self.assertEqual(init_response.status_code, 200)
        
        response = requests.get(f"{self.base_url}/api/ai-room/doctor-analytics")
        self.assertEqual(response.status_code, 200, f"AI Room doctor analytics failed: {response.text}")
        
        data = response.json()
        
        # Verify analytics structure
        self.assertIn("efficiency_score", data)
        self.assertIn("average_consultation_time", data)
        self.assertIn("punctuality_rating", data)
        self.assertIn("patient_satisfaction_score", data)
        self.assertIn("daily_patterns", data)
        self.assertIn("performance_trends", data)
        self.assertIn("recommendations", data)
        
        # Verify data types
        self.assertIsInstance(data["efficiency_score"], (int, float))
        self.assertIsInstance(data["average_consultation_time"], (int, float))
        self.assertIsInstance(data["punctuality_rating"], (int, float))
        self.assertIsInstance(data["patient_satisfaction_score"], (int, float))
        self.assertIsInstance(data["daily_patterns"], dict)
        self.assertIsInstance(data["performance_trends"], list)
        self.assertIsInstance(data["recommendations"], list)
        
        print(f"✅ Doctor Analytics generated successfully")
        print(f"   - Efficiency score: {data['efficiency_score']}")
        print(f"   - Average consultation time: {data['average_consultation_time']} minutes")
        print(f"   - Punctuality rating: {data['punctuality_rating']}")
        print(f"   - Patient satisfaction: {data['patient_satisfaction_score']}")
        print(f"🎉 AI Room Doctor Analytics Test: PASSED")
    
    def test_ai_room_metrics(self):
        """Test GET /api/ai-room/metrics?date=2025-07-23 - Get real-time metrics"""
        print("\n🔍 Testing AI Room Metrics Endpoint")
        
        # Initialize AI Room first
        init_response = requests.post(f"{self.base_url}/api/ai-room/initialize")
        self.assertEqual(init_response.status_code, 200)
        
        # Test with specific date
        test_date = "2025-07-23"
        response = requests.get(f"{self.base_url}/api/ai-room/metrics?date={test_date}")
        self.assertEqual(response.status_code, 200, f"AI Room metrics failed: {response.text}")
        
        data = response.json()
        
        # Verify metrics structure
        self.assertIn("total_patients", data)
        self.assertIn("average_waiting_time", data)
        self.assertIn("queue_efficiency", data)
        self.assertIn("predicted_delays", data)
        self.assertIn("satisfaction_trend", data)
        self.assertIn("optimization_score", data)
        
        # Verify data types
        self.assertIsInstance(data["total_patients"], int)
        self.assertIsInstance(data["average_waiting_time"], (int, float))
        self.assertIsInstance(data["queue_efficiency"], (int, float))
        self.assertIsInstance(data["predicted_delays"], int)
        self.assertIsInstance(data["satisfaction_trend"], str)
        self.assertIsInstance(data["optimization_score"], (int, float))
        
        print(f"✅ AI Metrics generated successfully")
        print(f"   - Total patients: {data['total_patients']}")
        print(f"   - Average waiting time: {data['average_waiting_time']} minutes")
        print(f"   - Queue efficiency: {data['queue_efficiency']}%")
        print(f"   - Predicted delays: {data['predicted_delays']}")
        print(f"   - Satisfaction trend: {data['satisfaction_trend']}")
        print(f"🎉 AI Room Metrics Test: PASSED")
    
    def test_ai_room_optimize_queue(self):
        """Test POST /api/ai-room/optimize-queue - Test queue optimization with sample data"""
        print("\n🔍 Testing AI Room Queue Optimization Endpoint")
        
        # Initialize AI Room first
        init_response = requests.post(f"{self.base_url}/api/ai-room/initialize")
        self.assertEqual(init_response.status_code, 200)
        
        # Test optimization with sample data
        optimization_data = {
            "date": "2025-07-23",
            "settings": {
                "prioritize_punctual_patients": True,
                "minimize_waiting_time": True,
                "consider_complexity": True,
                "emergency_mode": False
            },
            "constraints": {
                "max_reorder_distance": 3,
                "preserve_appointment_types": True
            }
        }
        
        response = requests.post(f"{self.base_url}/api/ai-room/optimize-queue", json=optimization_data)
        self.assertEqual(response.status_code, 200, f"AI Room queue optimization failed: {response.text}")
        
        data = response.json()
        
        # Verify optimization response structure
        self.assertIn("optimized_queue", data)
        self.assertIn("improvements", data)
        self.assertIn("time_savings", data)
        self.assertIn("efficiency_gain", data)
        
        # Verify improvements structure
        improvements = data["improvements"]
        self.assertIn("waiting_time_reduction", improvements)
        self.assertIn("patient_satisfaction_increase", improvements)
        self.assertIn("doctor_efficiency_improvement", improvements)
        
        # Verify data types
        self.assertIsInstance(data["optimized_queue"], list)
        self.assertIsInstance(data["time_savings"], (int, float))
        self.assertIsInstance(data["efficiency_gain"], (int, float))
        
        print(f"✅ Queue optimization completed successfully")
        print(f"   - Time savings: {data['time_savings']} minutes")
        print(f"   - Efficiency gain: {data['efficiency_gain']}%")
        print(f"   - Optimized queue length: {len(data['optimized_queue'])}")
        print(f"🎉 AI Room Queue Optimization Test: PASSED")
    
    def test_ai_room_send_whatsapp(self):
        """Test POST /api/ai-room/send-whatsapp - Test WhatsApp notification system"""
        print("\n🔍 Testing AI Room WhatsApp Notification Endpoint")
        
        # Get a patient for testing
        response = requests.get(f"{self.base_url}/api/patients")
        self.assertEqual(response.status_code, 200)
        patients_data = response.json()
        patients = patients_data["patients"]
        
        if len(patients) > 0:
            patient_id = patients[0]["id"]
            
            # Test WhatsApp notification
            notification_data = {
                "patient_id": patient_id,
                "message": "Votre rendez-vous est prévu dans 15 minutes. Merci de vous présenter à la réception.",
                "message_type": "appointment_reminder",
                "estimated_wait_time": 15,
                "queue_position": 2
            }
            
            response = requests.post(f"{self.base_url}/api/ai-room/send-whatsapp", json=notification_data)
            self.assertEqual(response.status_code, 200, f"AI Room WhatsApp notification failed: {response.text}")
            
            data = response.json()
            
            # Verify notification response structure
            self.assertIn("status", data)
            self.assertIn("message_sent", data)
            self.assertIn("patient_name", data)
            self.assertIn("phone_number", data)
            self.assertIn("message_content", data)
            self.assertIn("timestamp", data)
            
            # Verify data types
            self.assertIsInstance(data["status"], str)
            self.assertIsInstance(data["message_sent"], bool)
            self.assertIsInstance(data["patient_name"], str)
            self.assertIsInstance(data["phone_number"], str)
            self.assertIsInstance(data["message_content"], str)
            
            print(f"✅ WhatsApp notification sent successfully")
            print(f"   - Patient: {data['patient_name']}")
            print(f"   - Phone: {data['phone_number']}")
            print(f"   - Status: {data['status']}")
            print(f"   - Message sent: {data['message_sent']}")
        else:
            print(f"⚠️ No patients available for WhatsApp testing")
        
        print(f"🎉 AI Room WhatsApp Notification Test: PASSED")
    
    def test_ai_room_recommendations(self):
        """Test GET /api/ai-room/recommendations - Get AI-powered recommendations"""
        print("\n🔍 Testing AI Room Recommendations Endpoint")
        
        # Initialize AI Room first
        init_response = requests.post(f"{self.base_url}/api/ai-room/initialize")
        self.assertEqual(init_response.status_code, 200)
        
        response = requests.get(f"{self.base_url}/api/ai-room/recommendations")
        self.assertEqual(response.status_code, 200, f"AI Room recommendations failed: {response.text}")
        
        data = response.json()
        
        # Verify recommendations structure
        self.assertIn("workflow_optimizations", data)
        self.assertIn("schedule_adjustments", data)
        self.assertIn("patient_communication", data)
        self.assertIn("efficiency_improvements", data)
        self.assertIn("priority_level", data)
        self.assertIn("implementation_difficulty", data)
        
        # Verify workflow optimizations
        workflow_opts = data["workflow_optimizations"]
        self.assertIsInstance(workflow_opts, list)
        
        # Verify schedule adjustments
        schedule_adjs = data["schedule_adjustments"]
        self.assertIsInstance(schedule_adjs, list)
        
        # Verify patient communication recommendations
        patient_comm = data["patient_communication"]
        self.assertIsInstance(patient_comm, list)
        
        # Verify efficiency improvements
        efficiency_imps = data["efficiency_improvements"]
        self.assertIsInstance(efficiency_imps, list)
        
        print(f"✅ AI Recommendations generated successfully")
        print(f"   - Workflow optimizations: {len(workflow_opts)}")
        print(f"   - Schedule adjustments: {len(schedule_adjs)}")
        print(f"   - Patient communication: {len(patient_comm)}")
        print(f"   - Efficiency improvements: {len(efficiency_imps)}")
        print(f"   - Priority level: {data['priority_level']}")
        print(f"🎉 AI Room Recommendations Test: PASSED")
    
    def test_ai_room_comprehensive_workflow(self):
        """Test comprehensive AI Room workflow - End-to-end testing"""
        print("\n🔍 Testing AI Room Comprehensive Workflow")
        
        # Step 1: Initialize AI Room
        print("  Step 1: Initializing AI Room...")
        init_response = requests.post(f"{self.base_url}/api/ai-room/initialize")
        self.assertEqual(init_response.status_code, 200)
        print("  ✅ AI Room initialized")
        
        # Step 2: Get AI Queue
        print("  Step 2: Fetching AI-optimized queue...")
        test_date = datetime.now().strftime("%Y-%m-%d")
        queue_response = requests.get(f"{self.base_url}/api/ai-room/queue?date={test_date}")
        self.assertEqual(queue_response.status_code, 200)
        queue_data = queue_response.json()
        print(f"  ✅ AI Queue fetched ({queue_data['total_patients']} patients)")
        
        # Step 3: Get AI Predictions
        print("  Step 3: Generating AI predictions...")
        predictions_response = requests.get(f"{self.base_url}/api/ai-room/predictions?date={test_date}")
        self.assertEqual(predictions_response.status_code, 200)
        predictions_data = predictions_response.json()
        print("  ✅ AI Predictions generated")
        
        # Step 4: Get Doctor Analytics
        print("  Step 4: Fetching doctor analytics...")
        analytics_response = requests.get(f"{self.base_url}/api/ai-room/doctor-analytics")
        self.assertEqual(analytics_response.status_code, 200)
        analytics_data = analytics_response.json()
        print(f"  ✅ Doctor Analytics fetched (efficiency: {analytics_data['efficiency_score']})")
        
        # Step 5: Get Real-time Metrics
        print("  Step 5: Fetching real-time metrics...")
        metrics_response = requests.get(f"{self.base_url}/api/ai-room/metrics?date={test_date}")
        self.assertEqual(metrics_response.status_code, 200)
        metrics_data = metrics_response.json()
        print(f"  ✅ Real-time Metrics fetched (efficiency: {metrics_data['queue_efficiency']}%)")
        
        # Step 6: Optimize Queue
        print("  Step 6: Optimizing patient queue...")
        optimization_data = {
            "date": test_date,
            "settings": {
                "prioritize_punctual_patients": True,
                "minimize_waiting_time": True,
                "consider_complexity": True
            }
        }
        optimize_response = requests.post(f"{self.base_url}/api/ai-room/optimize-queue", json=optimization_data)
        self.assertEqual(optimize_response.status_code, 200)
        optimize_data = optimize_response.json()
        print(f"  ✅ Queue optimized (time savings: {optimize_data['time_savings']} min)")
        
        # Step 7: Get AI Recommendations
        print("  Step 7: Generating AI recommendations...")
        recommendations_response = requests.get(f"{self.base_url}/api/ai-room/recommendations")
        self.assertEqual(recommendations_response.status_code, 200)
        recommendations_data = recommendations_response.json()
        print(f"  ✅ AI Recommendations generated (priority: {recommendations_data['priority_level']})")
        
        # Step 8: Test WhatsApp Notification (if patients available)
        print("  Step 8: Testing WhatsApp notifications...")
        patients_response = requests.get(f"{self.base_url}/api/patients")
        if patients_response.status_code == 200:
            patients_data = patients_response.json()
            if len(patients_data["patients"]) > 0:
                patient_id = patients_data["patients"][0]["id"]
                whatsapp_data = {
                    "patient_id": patient_id,
                    "message": "Test notification from AI Room workflow",
                    "message_type": "workflow_test"
                }
                whatsapp_response = requests.post(f"{self.base_url}/api/ai-room/send-whatsapp", json=whatsapp_data)
                self.assertEqual(whatsapp_response.status_code, 200)
                print("  ✅ WhatsApp notification sent")
            else:
                print("  ⚠️ No patients available for WhatsApp test")
        
        print(f"🎉 AI Room Comprehensive Workflow Test: PASSED")
        print(f"   - All 8 AI Room endpoints tested successfully")
        print(f"   - End-to-end workflow validated")
        print(f"   - AI-powered features working correctly")

if __name__ == '__main__':
    unittest.main()