from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
import uuid
import json

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Cabinet Médical API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/cabinet_medical")
client = MongoClient(MONGO_URL)
db = client.cabinet_medical

# Collections
patients_collection = db.patients
appointments_collection = db.appointments
consultations_collection = db.consultations
payments_collection = db.payments
users_collection = db.users

# Security
security = HTTPBearer()

# Models
class ParentInfo(BaseModel):
    nom: str = ""
    telephone: str = ""
    fonction: str = ""

class ConsultationInfo(BaseModel):
    date: str
    type: str  # "visite" ou "controle"
    id_consultation: str

class Patient(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    prenom: str
    date_naissance: str = ""
    age: str = ""  # calculé automatiquement
    adresse: str = ""
    pere: ParentInfo = Field(default_factory=ParentInfo)
    mere: ParentInfo = Field(default_factory=ParentInfo)
    numero_whatsapp: str = ""
    lien_whatsapp: str = ""  # généré automatiquement
    notes: str = ""
    antecedents: str = ""
    consultations: List[ConsultationInfo] = []
    date_premiere_consultation: str = ""
    date_derniere_consultation: str = ""
    # Garder les anciens champs pour compatibilité
    sexe: str = ""
    telephone: str = ""
    nom_parent: str = ""
    telephone_parent: str = ""
    assurance: str = ""
    numero_assurance: str = ""
    allergies: str = ""
    photo_url: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    date: str
    heure: str
    type_rdv: str  # "visite" ou "controle"
    statut: str = "absent"  # absent, attente, en_cours, termine
    salle: str = ""  # salle1, salle2
    motif: str = ""
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Consultation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    appointment_id: str
    date: str
    duree: int = 0  # en minutes
    poids: float = 0.0
    taille: float = 0.0
    pc: float = 0.0  # périmètre crânien
    observations: str = ""
    traitement: str = ""
    bilan: str = ""
    relance_date: str = ""
    created_at: datetime = Field(default_factory=datetime.now)

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    appointment_id: str
    montant: float
    type_paiement: str  # "espece", "carte", "cheque"
    statut: str = "non_paye"  # "paye", "non_paye"
    date: str
    created_at: datetime = Field(default_factory=datetime.now)

# Helper functions
def calculate_age(date_naissance: str) -> str:
    """Calculate age from birth date in format '2 ans, 3 mois, 15 jours'"""
    if not date_naissance:
        return ""
    
    try:
        birth_date = datetime.strptime(date_naissance, "%Y-%m-%d")
        today = datetime.now()
        
        # Calculate differences
        years = today.year - birth_date.year
        months = today.month - birth_date.month
        days = today.day - birth_date.day
        
        # Adjust for negative days
        if days < 0:
            months -= 1
            # Get last day of previous month
            if today.month == 1:
                last_month = 12
                last_year = today.year - 1
            else:
                last_month = today.month - 1
                last_year = today.year
            
            from calendar import monthrange
            days += monthrange(last_year, last_month)[1]
        
        # Adjust for negative months
        if months < 0:
            years -= 1
            months += 12
        
        # Format result
        age_parts = []
        if years > 0:
            age_parts.append(f"{years} an{'s' if years > 1 else ''}")
        if months > 0:
            age_parts.append(f"{months} mois")
        if days > 0:
            age_parts.append(f"{days} jour{'s' if days > 1 else ''}")
        
        return ", ".join(age_parts) if age_parts else "0 jour"
    except ValueError:
        return ""

def generate_whatsapp_link(numero: str) -> str:
    """Generate WhatsApp link from phone number"""
    if not numero:
        return ""
    
    # Remove all non-digit characters
    clean_number = ''.join(filter(str.isdigit, numero))
    
    # Validate Tunisia format (216xxxxxxxx)
    if clean_number.startswith('216') and len(clean_number) == 11:
        return f"https://wa.me/{clean_number}"
    
    return ""

def update_patient_computed_fields(patient_dict: dict) -> dict:
    """Update computed fields for patient"""
    # Calculate age
    if patient_dict.get('date_naissance'):
        patient_dict['age'] = calculate_age(patient_dict['date_naissance'])
    
    # Generate WhatsApp link
    if patient_dict.get('numero_whatsapp'):
        patient_dict['lien_whatsapp'] = generate_whatsapp_link(patient_dict['numero_whatsapp'])
    
    # Update consultation dates
    if patient_dict.get('consultations'):
        dates = [c.get('date') for c in patient_dict['consultations'] if c.get('date')]
        if dates:
            sorted_dates = sorted(dates)
            patient_dict['date_premiere_consultation'] = sorted_dates[0]
            patient_dict['date_derniere_consultation'] = sorted_dates[-1]
    
    return patient_dict

def create_demo_data():
    """Create demo data for testing"""
    
    # Demo patients
    demo_patients = [
        {
            "id": "patient1",
            "nom": "Ben Ahmed",
            "prenom": "Yassine",
            "date_naissance": "2020-05-15",
            "sexe": "M",
            "telephone": "0612345678",
            "adresse": "123 Rue de la Paix, Casablanca",
            "nom_parent": "Ahmed Ben Ahmed",
            "telephone_parent": "0612345678",
            "assurance": "CNSS",
            "numero_assurance": "123456789",
            "allergies": "Aucune",
            "antecedents": "Aucun"
        },
        {
            "id": "patient2",
            "nom": "Alami",
            "prenom": "Lina",
            "date_naissance": "2019-03-22",
            "sexe": "F",
            "telephone": "0687654321",
            "adresse": "456 Avenue Mohammed V, Rabat",
            "nom_parent": "Fatima Alami",
            "telephone_parent": "0687654321",
            "assurance": "CNOPS",
            "numero_assurance": "987654321",
            "allergies": "Pénicilline",
            "antecedents": "Eczéma"
        },
        {
            "id": "patient3",
            "nom": "Tazi",
            "prenom": "Omar",
            "date_naissance": "2021-08-10",
            "sexe": "M",
            "telephone": "0611223344",
            "adresse": "789 Rue Hassan II, Fès",
            "nom_parent": "Khalid Tazi",
            "telephone_parent": "0611223344",
            "assurance": "",
            "numero_assurance": "",
            "allergies": "",
            "antecedents": ""
        }
    ]

    # Demo appointments
    today = datetime.now()
    demo_appointments = [
        {
            "id": "appt1",
            "patient_id": "patient1",
            "date": today.strftime("%Y-%m-%d"),
            "heure": "09:00",
            "type_rdv": "visite",
            "statut": "attente",
            "salle": "salle1",
            "motif": "Fièvre",
            "notes": ""
        },
        {
            "id": "appt2",
            "patient_id": "patient2",
            "date": today.strftime("%Y-%m-%d"),
            "heure": "10:30",
            "type_rdv": "controle",
            "statut": "absent",
            "salle": "",
            "motif": "Contrôle vaccination",
            "notes": ""
        },
        {
            "id": "appt3",
            "patient_id": "patient3",
            "date": today.strftime("%Y-%m-%d"),
            "heure": "14:00",
            "type_rdv": "visite",
            "statut": "termine",
            "salle": "salle2",
            "motif": "Consultation générale",
            "notes": ""
        }
    ]

    # Clear existing data
    patients_collection.delete_many({})
    appointments_collection.delete_many({})
    consultations_collection.delete_many({})
    payments_collection.delete_many({})

    # Insert demo data
    for patient in demo_patients:
        patient['created_at'] = datetime.now()
        patient['updated_at'] = datetime.now()
        patients_collection.insert_one(patient)

    for appointment in demo_appointments:
        appointment['created_at'] = datetime.now()
        appointment['updated_at'] = datetime.now()
        appointments_collection.insert_one(appointment)

    # Demo consultations
    demo_consultations = [
        {
            "id": "cons1",
            "patient_id": "patient3",
            "appointment_id": "appt3",
            "date": today.strftime("%Y-%m-%d"),
            "duree": 20,
            "poids": 12.5,
            "taille": 85.0,
            "pc": 47.0,
            "observations": "Enfant en bonne santé, développement normal",
            "traitement": "Aucun traitement nécessaire",
            "bilan": "RAS",
            "relance_date": "",
            "created_at": datetime.now()
        }
    ]

    for consultation in demo_consultations:
        consultations_collection.insert_one(consultation)

    # Demo payments
    demo_payments = [
        {
            "id": "pay1",
            "patient_id": "patient3",
            "appointment_id": "appt3",
            "montant": 300.0,
            "type_paiement": "espece",
            "statut": "paye",
            "date": today.strftime("%Y-%m-%d"),
            "created_at": datetime.now()
        }
    ]

    for payment in demo_payments:
        payments_collection.insert_one(payment)

# API Routes
@app.get("/")
async def root():
    return {"message": "Cabinet Médical API"}

@app.get("/api/init-demo")
async def init_demo():
    """Initialize demo data"""
    create_demo_data()
    return {"message": "Demo data created successfully"}

@app.get("/api/dashboard")
async def get_dashboard():
    """Get dashboard statistics"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Get today's appointments
    today_appointments = list(appointments_collection.find({"date": today}))
    total_rdv = len(today_appointments)
    
    # Count by status
    rdv_restants = len([a for a in today_appointments if a["statut"] == "absent"])
    rdv_attente = len([a for a in today_appointments if a["statut"] == "attente"])
    rdv_en_cours = len([a for a in today_appointments if a["statut"] == "en_cours"])
    rdv_termines = len([a for a in today_appointments if a["statut"] == "termine"])
    
    # Get today's payments
    today_payments = list(payments_collection.find({"date": today, "statut": "paye"}))
    recette_jour = sum([p["montant"] for p in today_payments])
    
    # Get patient count
    total_patients = patients_collection.count_documents({})
    
    return {
        "total_rdv": total_rdv,
        "rdv_restants": rdv_restants,
        "rdv_attente": rdv_attente,
        "rdv_en_cours": rdv_en_cours,
        "rdv_termines": rdv_termines,
        "recette_jour": recette_jour,
        "total_patients": total_patients,
        "duree_attente_moyenne": 15  # Mock data
    }

@app.get("/api/patients")
async def get_patients(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str = Query("", description="Search by name or birth date")
):
    """Get patients with pagination and search"""
    # Build search query
    query = {}
    if search:
        search_regex = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"nom": search_regex},
            {"prenom": search_regex},
            {"date_naissance": search_regex}
        ]
    
    # Count total documents
    total_count = patients_collection.count_documents(query)
    
    # Calculate pagination
    skip = (page - 1) * limit
    
    # Get patients with pagination
    patients = list(patients_collection.find(query, {"_id": 0})
                   .skip(skip)
                   .limit(limit)
                   .sort("nom", 1))
    
    # Update computed fields for each patient
    for patient in patients:
        patient = update_patient_computed_fields(patient)
    
    return {
        "patients": patients,
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit
    }

@app.get("/api/patients/count")
async def get_patients_count():
    """Get total number of patients"""
    count = patients_collection.count_documents({})
    return {"count": count}

@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    """Get patient by ID"""
    patient = patients_collection.find_one({"id": patient_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Update computed fields
    patient = update_patient_computed_fields(patient)
    
    return patient

@app.get("/api/patients/{patient_id}/consultations")
async def get_patient_consultations_full(patient_id: str):
    """Get full consultation details for a patient"""
    patient = patients_collection.find_one({"id": patient_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get consultations from consultations collection
    consultations = list(consultations_collection.find({"patient_id": patient_id}, {"_id": 0}))
    
    # Get appointments to get type information
    appointments = list(appointments_collection.find({"patient_id": patient_id}, {"_id": 0}))
    
    # Combine consultation and appointment data
    result = []
    for consultation in consultations:
        appointment = next((a for a in appointments if a["id"] == consultation.get("appointment_id")), None)
        result.append({
            "id": consultation["id"],
            "date": consultation["date"],
            "type": appointment["type_rdv"] if appointment else "visite",
            "duree": consultation.get("duree", 0),
            "observations": consultation.get("observations", ""),
            "traitement": consultation.get("traitement", ""),
            "bilan": consultation.get("bilan", "")
        })
    
    # Sort by date (most recent first)
    result.sort(key=lambda x: x["date"], reverse=True)
    
    return result

@app.post("/api/patients")
async def create_patient(patient: Patient):
    """Create new patient"""
    patient_dict = patient.dict()
    
    # Update computed fields
    patient_dict = update_patient_computed_fields(patient_dict)
    
    # Insert into database
    patients_collection.insert_one(patient_dict)
    return {"message": "Patient created successfully", "patient_id": patient.id}

@app.put("/api/patients/{patient_id}")
async def update_patient(patient_id: str, patient: Patient):
    """Update patient"""
    patient_dict = patient.dict()
    patient_dict["updated_at"] = datetime.now()
    
    # Update computed fields
    patient_dict = update_patient_computed_fields(patient_dict)
    
    result = patients_collection.update_one(
        {"id": patient_id}, 
        {"$set": patient_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"message": "Patient updated successfully"}

@app.delete("/api/patients/{patient_id}")
async def delete_patient(patient_id: str):
    """Delete patient"""
    result = patients_collection.delete_one({"id": patient_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"message": "Patient deleted successfully"}

@app.get("/api/appointments")
async def get_appointments(date: Optional[str] = None):
    """Get appointments, optionally filtered by date"""
    query = {}
    if date:
        query["date"] = date
    
    appointments = list(appointments_collection.find(query, {"_id": 0}))
    
    # Get patient info for each appointment
    for appointment in appointments:
        patient = patients_collection.find_one({"id": appointment["patient_id"]}, {"_id": 0})
        if patient:
            appointment["patient"] = patient
    
    return appointments

@app.get("/api/appointments/today")
async def get_today_appointments():
    """Get today's appointments"""
    today = datetime.now().strftime("%Y-%m-%d")
    return await get_appointments(date=today)

@app.post("/api/appointments")
async def create_appointment(appointment: Appointment):
    """Create new appointment"""
    appointment_dict = appointment.dict()
    appointments_collection.insert_one(appointment_dict)
    return {"message": "Appointment created successfully", "appointment_id": appointment.id}

@app.put("/api/appointments/{appointment_id}")
async def update_appointment(appointment_id: str, appointment: Appointment):
    """Update appointment"""
    appointment_dict = appointment.dict()
    appointment_dict["updated_at"] = datetime.now()
    result = appointments_collection.update_one(
        {"id": appointment_id}, 
        {"$set": appointment_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment updated successfully"}

@app.delete("/api/appointments/{appointment_id}")
async def delete_appointment(appointment_id: str):
    """Delete appointment"""
    result = appointments_collection.delete_one({"id": appointment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment deleted successfully"}

@app.get("/api/consultations")
async def get_consultations():
    """Get all consultations"""
    consultations = list(consultations_collection.find({}, {"_id": 0}))
    return consultations

@app.get("/api/consultations/patient/{patient_id}")
async def get_patient_consultations(patient_id: str):
    """Get consultations for a specific patient"""
    consultations = list(consultations_collection.find({"patient_id": patient_id}, {"_id": 0}))
    return consultations

@app.post("/api/consultations")
async def create_consultation(consultation: Consultation):
    """Create new consultation"""
    consultation_dict = consultation.dict()
    consultations_collection.insert_one(consultation_dict)
    return {"message": "Consultation created successfully", "consultation_id": consultation.id}

@app.get("/api/payments")
async def get_payments():
    """Get all payments"""
    payments = list(payments_collection.find({}, {"_id": 0}))
    return payments

@app.post("/api/payments")
async def create_payment(payment: Payment):
    """Create new payment"""
    payment_dict = payment.dict()
    payments_collection.insert_one(payment_dict)
    return {"message": "Payment created successfully", "payment_id": payment.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)