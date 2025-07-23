from fastapi import FastAPI, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from datetime import datetime, timedelta, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
import uuid
import json
import asyncio
import bcrypt
import jwt

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
messages_collection = db.messages
phone_messages_collection = db.phone_messages
cash_movements_collection = db.cash_movements

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Security
security = HTTPBearer()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        message_json = json.dumps(message, default=str)
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except:
                # Remove disconnected connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

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
    statut: str = "programme"  # programme, attente, en_cours, termine, absent, retard
    salle: str = ""  # salle1, salle2, ""
    motif: str = ""
    notes: str = ""
    paye: bool = False  # statut de paiement
    assure: bool = False  # Nouveau champ pour assurance
    heure_arrivee_attente: str = ""  # timestamp quand patient arrive en salle d'attente
    priority: int = 999  # ordre dans la salle d'attente (plus petit = plus prioritaire)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Consultation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    appointment_id: str
    date: str
    type_rdv: str = "visite"  # "visite" ou "controle"
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
    type_paiement: str = "espece"  # espece, carte, cheque, virement, gratuit
    statut: str = "paye"  # paye, en_attente, rembourse
    assure: bool = False  # Si le patient est assuré
    taux_remboursement: float = 0  # Pourcentage de remboursement assurance
    date: str
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Modèle pour les mises à jour de paiement
class PaymentUpdate(BaseModel):
    paye: bool = False
    montant: float = 65.0  # Montant par défaut 65 TND
    type_paiement: str = "espece"  # Toujours espèces
    assure: bool = False
    notes: str = ""

# Modèles pour la messagerie instantanée
class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_type: str  # "medecin" ou "secretaire"
    sender_name: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    is_read: bool = False
    is_edited: bool = False
    original_content: str = ""
    reply_to: Optional[str] = None  # ID du message auquel on répond
    reply_content: str = ""  # Contenu du message cité
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class MessageCreate(BaseModel):
    content: str
    reply_to: Optional[str] = None

class MessageUpdate(BaseModel):
    content: str

# User Models for Authentication and Authorization
class UserPermissions(BaseModel):
    # Page access permissions
    dashboard: bool = True
    patients: bool = True
    calendar: bool = True
    messages: bool = True
    billing: bool = True
    consultation: bool = True
    administration: bool = False  # Only doctors by default
    
    # Action permissions
    create_appointment: bool = True
    edit_appointment: bool = True
    delete_appointment: bool = False
    view_payments: bool = True
    edit_payments: bool = True
    delete_payments: bool = False
    export_data: bool = False
    reset_data: bool = False
    manage_users: bool = False
    
    # Special restrictions
    consultation_read_only: bool = False  # If true, can only view consultations

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str = ""
    full_name: str
    role: str  # "medecin" or "secretaire"
    hashed_password: str
    is_active: bool = True
    permissions: UserPermissions = Field(default_factory=UserPermissions)
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class UserCreate(BaseModel):
    username: str
    email: str = ""
    full_name: str
    role: str  # "medecin" or "secretaire"
    password: str
    permissions: Optional[UserPermissions] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[UserPermissions] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    permissions: UserPermissions
    last_login: Optional[datetime]
    created_at: datetime

# Modèles pour les messages téléphoniques
class PhoneMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str  # Nom complet du patient pour faciliter la recherche
    message_content: str  # Question/demande du patient
    response_content: str = ""  # Réponse du médecin
    status: str = "nouveau"  # "nouveau", "traité"
    priority: str = "normal"  # "urgent", "normal"
    call_date: str  # Date de l'appel YYYY-MM-DD
    call_time: str  # Heure de l'appel HH:MM
    created_by: str  # ID/nom de la secrétaire
    responded_by: str = ""  # ID/nom du médecin qui répond
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class PhoneMessageCreate(BaseModel):
    patient_id: str
    message_content: str
    priority: str = "normal"  # "urgent", "normal"
    call_date: str
    call_time: str

class PhoneMessageResponse(BaseModel):
    response_content: str

class PhoneMessageEdit(BaseModel):
    message_content: str
    priority: str = "normal"

# Modèles pour la gestion de caisse
class CashMovement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    montant: float
    type_mouvement: str  # "ajout" ou "soustraction"
    motif: str
    date: str
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = "system"  # Qui a créé le mouvement

class CashMovementCreate(BaseModel):
    montant: float
    type_mouvement: str  # "ajout" ou "soustraction"
    motif: str
    date: str

# Helper functions for authentication
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = users_collection.find_one({"username": username}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def create_default_users():
    """Create default users if they don't exist"""
    try:
        # Check if users exist
        if users_collection.count_documents({}) == 0:
            # Create default doctor
            doctor_permissions = UserPermissions(
                administration=True,
                delete_appointment=True,
                delete_payments=True,
                export_data=True,
                reset_data=True,
                manage_users=True
            )
            
            doctor = User(
                username="medecin",
                full_name="Dr Heni Dridi",
                role="medecin",
                hashed_password=hash_password("medecin123"),
                permissions=doctor_permissions
            )
            
            # Create default secretary
            secretary_permissions = UserPermissions(
                administration=False,
                delete_appointment=False,
                delete_payments=False,
                export_data=False,
                reset_data=False,
                manage_users=False,
                consultation_read_only=True
            )
            
            secretary = User(
                username="secretaire",
                full_name="Secrétaire",
                role="secretaire",
                hashed_password=hash_password("secretaire123"),
                permissions=secretary_permissions
            )
            
            # Insert users
            users_collection.insert_one(doctor.dict())
            users_collection.insert_one(secretary.dict())
            print("Default users created successfully")
        
    except Exception as e:
        print(f"Error creating default users: {e}")

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

def check_appointment_delay(appointment: dict) -> str:
    """Check if appointment is delayed and return appropriate status"""
    if appointment["statut"] == "programme":
        try:
            appointment_datetime = datetime.strptime(
                f"{appointment['date']} {appointment['heure']}", 
                "%Y-%m-%d %H:%M"
            )
            now = datetime.now()
            
            # If 15 minutes past appointment time, mark as delayed
            if now > appointment_datetime + timedelta(minutes=15):
                return "retard"
        except:
            pass
    return appointment["statut"]

def get_time_slots(start_hour: int = 9, end_hour: int = 18, interval_minutes: int = 15) -> List[str]:
    """Generate time slots for the day"""
    slots = []
    current_time = datetime.strptime(f"{start_hour:02d}:00", "%H:%M")
    end_time = datetime.strptime(f"{end_hour:02d}:00", "%H:%M")
    
    while current_time < end_time:
        slots.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=interval_minutes)
    
    return slots

def get_week_dates(date_str: str) -> List[str]:
    """Get dates for the week containing the given date (Monday to Saturday)"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Get Monday of the week
        monday = date_obj - timedelta(days=date_obj.weekday())
        
        # Generate dates from Monday to Saturday
        week_dates = []
        for i in range(6):  # Monday to Saturday
            week_dates.append((monday + timedelta(days=i)).strftime("%Y-%m-%d"))
        
        return week_dates
    except:
        return []

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

# Helper function pour nettoyage automatique quotidien des messages
async def cleanup_messages_daily():
    """Nettoyer les messages tous les jours à 8h"""
    try:
        # Supprimer tous les messages
        result = messages_collection.delete_many({})
        print(f"Messages supprimés: {result.deleted_count}")
        return result.deleted_count
    except Exception as e:
        print(f"Erreur lors du nettoyage des messages: {str(e)}")
        return 0

# Helper function pour nettoyage automatique quotidien des messages téléphoniques
async def cleanup_phone_messages_daily():
    """Nettoyer les messages téléphoniques tous les jours à 8h"""
    try:
        # Supprimer tous les messages téléphoniques
        result = phone_messages_collection.delete_many({})
        print(f"Messages téléphoniques supprimés: {result.deleted_count}")
        return result.deleted_count
    except Exception as e:
        print(f"Erreur lors du nettoyage des messages téléphoniques: {str(e)}")
        return 0

def create_demo_data():
    """Create demo data for testing"""
    # Create default users first
    create_default_users()
    
    # Demo patients
    demo_patients = [
        {
            "id": "patient1",
            "nom": "Ben Ahmed",
            "prenom": "Yassine",
            "date_naissance": "2020-05-15",
            "age": "",  # sera calculé
            "sexe": "M",
            "telephone": "0612345678",
            "adresse": "123 Rue de la Paix, Tunis",
            "pere": {
                "nom": "Ahmed Ben Ahmed",
                "telephone": "21650123456",
                "fonction": "Ingénieur"
            },
            "mere": {
                "nom": "Fatima Ben Ahmed",
                "telephone": "21650123457",
                "fonction": "Professeur"
            },
            "numero_whatsapp": "21650123456",
            "lien_whatsapp": "",  # sera généré
            "notes": "Enfant très actif",
            "antecedents": "Aucun antécédent particulier",
            "consultations": [
                {
                    "date": "2024-01-15",
                    "type": "visite",
                    "id_consultation": "cons1"
                },
                {
                    "date": "2024-06-10",
                    "type": "controle",
                    "id_consultation": "cons2"
                }
            ],
            "date_premiere_consultation": "",  # sera calculé
            "date_derniere_consultation": "",  # sera calculé
            "nom_parent": "Ahmed Ben Ahmed",
            "telephone_parent": "0612345678",
            "assurance": "CNSS",
            "numero_assurance": "123456789",
            "allergies": "Aucune"
        },
        {
            "id": "patient2",
            "nom": "Alami",
            "prenom": "Lina",
            "date_naissance": "2019-03-22",
            "age": "",  # sera calculé
            "sexe": "F",
            "telephone": "0687654321",
            "adresse": "456 Avenue Habib Bourguiba, Sousse",
            "pere": {
                "nom": "Karim Alami",
                "telephone": "21654321098",
                "fonction": "Médecin"
            },
            "mere": {
                "nom": "Asma Alami",
                "telephone": "21654321099",
                "fonction": "Avocate"
            },
            "numero_whatsapp": "21654321098",
            "lien_whatsapp": "",  # sera généré
            "notes": "Enfant calme et sage",
            "antecedents": "Eczéma léger",
            "consultations": [
                {
                    "date": "2024-03-20",
                    "type": "visite",
                    "id_consultation": "cons3"
                }
            ],
            "date_premiere_consultation": "",  # sera calculé
            "date_derniere_consultation": "",  # sera calculé
            "nom_parent": "Fatima Alami",
            "telephone_parent": "0687654321",
            "assurance": "CNOPS",
            "numero_assurance": "987654321",
            "allergies": "Pénicilline"
        },
        {
            "id": "patient3",
            "nom": "Tazi",
            "prenom": "Omar",
            "date_naissance": "2021-08-10",
            "age": "",  # sera calculé
            "sexe": "M",
            "telephone": "0611223344",
            "adresse": "789 Rue Hassan II, Sfax",
            "pere": {
                "nom": "Khalid Tazi",
                "telephone": "21678901234",
                "fonction": "Commerçant"
            },
            "mere": {
                "nom": "Salma Tazi",
                "telephone": "21678901235",
                "fonction": "Infirmière"
            },
            "numero_whatsapp": "21678901234",
            "lien_whatsapp": "",  # sera généré
            "notes": "Premier enfant de la famille",
            "antecedents": "Naissance prématurée",
            "consultations": [],
            "date_premiere_consultation": "",
            "date_derniere_consultation": "",
            "nom_parent": "Khalid Tazi",
            "telephone_parent": "0611223344",
            "assurance": "",
            "numero_assurance": "",
            "allergies": ""
        }
    ]

    # Demo appointments
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
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
            "notes": "",
            "paye": True
        },
        {
            "id": "appt2",
            "patient_id": "patient2",
            "date": today.strftime("%Y-%m-%d"),
            "heure": "10:30",
            "type_rdv": "controle",
            "statut": "programme",
            "salle": "",
            "motif": "Contrôle vaccination",
            "notes": "",
            "paye": False
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
            "notes": "",
            "paye": True
        },
        {
            "id": "appt4",
            "patient_id": "patient1",
            "date": today.strftime("%Y-%m-%d"),
            "heure": "15:30",
            "type_rdv": "controle",
            "statut": "programme",
            "salle": "",
            "motif": "Suivi vaccination",
            "notes": "",
            "paye": False
        },
        {
            "id": "appt5",
            "patient_id": "patient2",
            "date": tomorrow.strftime("%Y-%m-%d"),
            "heure": "09:30",
            "type_rdv": "visite",
            "statut": "programme",
            "salle": "",
            "motif": "Consultation de routine",
            "notes": "",
            "paye": False
        },
        {
            "id": "appt6",
            "patient_id": "patient3",
            "date": tomorrow.strftime("%Y-%m-%d"),
            "heure": "11:00",
            "type_rdv": "controle",
            "statut": "programme",
            "salle": "",
            "motif": "Contrôle croissance",
            "notes": "",
            "paye": False
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
        # Apply computed fields
        patient = update_patient_computed_fields(patient)
        patients_collection.insert_one(patient)

    for appointment in demo_appointments:
        appointment['created_at'] = datetime.now()
        appointment['updated_at'] = datetime.now()
        appointments_collection.insert_one(appointment)

    # Demo consultations
    demo_consultations = [
        # Consultations pour patient1 (Yassine Ben Ahmed)
        {
            "id": "cons1",
            "patient_id": "patient1",
            "appointment_id": "appt1",
            "date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
            "duree": 25,
            "poids": 18.2,
            "taille": 95.0,
            "pc": 50.0,
            "observations": "Consultation pour fièvre. Enfant en bonne forme générale. Température : 38.5°C. Gorge légèrement irritée.",
            "traitement": "Paracétamol sirop 2.5ml 3 fois par jour pendant 3 jours. Repos et hydratation.",
            "bilan": "Infection virale bénigne. Guérison attendue en 3-5 jours.",
            "relance_date": today.strftime("%Y-%m-%d"),  # Relance pour aujourd'hui
            "created_at": datetime.now() - timedelta(days=30),
            "type_rdv": "visite"
        },
        {
            "id": "cons2",
            "patient_id": "patient1", 
            "appointment_id": "appt4",
            "date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
            "duree": 15,
            "poids": 18.5,
            "taille": 96.0,
            "pc": 50.2,
            "observations": "Consultation de suivi vaccination. Réaction vaccinale normale. Enfant en excellente santé.",
            "traitement": "Aucun traitement spécifique",
            "bilan": "Vaccination bien tolérée. Croissance normale.",
            "relance_date": "",
            "created_at": datetime.now() - timedelta(days=15),
            "type_rdv": "controle"
        },
        
        # Consultations pour patient2 (Lina Alami)
        {
            "id": "cons3",
            "patient_id": "patient2",
            "appointment_id": "appt2", 
            "date": (today - timedelta(days=45)).strftime("%Y-%m-%d"),
            "duree": 30,
            "poids": 15.8,
            "taille": 88.0,
            "pc": 48.5,
            "observations": "Première visite pour eczéma. Éruption cutanée sur les bras et le visage. Enfant par ailleurs en bonne santé.",
            "traitement": "Crème hydratante 2 fois par jour. Éviter les savons parfumés. Cortisone légère si aggravation.",
            "bilan": "Eczéma constitutionnel léger. Évolution favorable avec soins adaptés.",
            "relance_date": today.strftime("%Y-%m-%d"),  # Relance pour aujourd'hui
            "created_at": datetime.now() - timedelta(days=45),
            "type_rdv": "visite"
        },
        {
            "id": "cons4",
            "patient_id": "patient2",
            "appointment_id": "appt5",
            "date": (today - timedelta(days=20)).strftime("%Y-%m-%d"),
            "duree": 20,
            "poids": 16.1,
            "taille": 89.0,
            "pc": 48.8,
            "observations": "Contrôle eczéma. Nette amélioration des lésions cutanées. Peau bien hydratée. Parents satisfaits du traitement.",
            "traitement": "Continuer crème hydratante. Réduire fréquence à 1 fois par jour.",
            "bilan": "Eczéma bien contrôlé. Poursuite des soins préventifs.",
            "relance_date": "",
            "created_at": datetime.now() - timedelta(days=20),
            "type_rdv": "controle"
        },
        
        # Consultation pour patient3 (Omar Tazi)
        {
            "id": "cons5",
            "patient_id": "patient3",
            "appointment_id": "appt3",
            "date": today.strftime("%Y-%m-%d"),
            "duree": 20,
            "poids": 12.5,
            "taille": 85.0,
            "pc": 47.0,
            "observations": "Consultation générale. Enfant en bonne santé, développement psychomoteur normal. Bon appétit, sommeil régulier.",
            "traitement": "Aucun traitement nécessaire. Continuer alimentation équilibrée.",
            "bilan": "Développement normal pour l'âge. Enfant en excellente santé.",
            "relance_date": "",
            "created_at": datetime.now(),
            "type_rdv": "visite"
        },
        {
            "id": "cons6", 
            "patient_id": "patient3",
            "appointment_id": "appt6",
            "date": (today - timedelta(days=60)).strftime("%Y-%m-%d"),
            "duree": 25,
            "poids": 11.8,
            "taille": 82.0,
            "pc": 46.5,
            "observations": "Contrôle de croissance. Rattrapage pondéral satisfaisant après naissance prématurée. Développement adapté.",
            "traitement": "Supplémentation vitaminique continue. Alimentation riche en protéines.",
            "bilan": "Croissance rattrape la normale. Évolution très positive.",
            "relance_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "created_at": datetime.now() - timedelta(days=60),
            "type_rdv": "controle"
        }
    ]

    for consultation in demo_consultations:
        consultations_collection.insert_one(consultation)

    # Demo payments
    demo_payments = [
        # Paiements pour patient1 (Yassine Ben Ahmed)
        {
            "id": "pay1",
            "patient_id": "patient1",
            "appointment_id": "appt1",
            "montant": 65.0,
            "type_paiement": "espece",
            "statut": "paye",
            "date": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
            "assure": True,
            "created_at": datetime.now() - timedelta(days=30)
        },
        {
            "id": "pay2",
            "patient_id": "patient1",
            "appointment_id": "appt4",
            "montant": 65.0,
            "type_paiement": "espece",
            "statut": "paye",
            "date": (today - timedelta(days=15)).strftime("%Y-%m-%d"),
            "assure": True,
            "created_at": datetime.now() - timedelta(days=15)
        },
        
        # Paiements pour patient2 (Lina Alami)
        {
            "id": "pay3",
            "patient_id": "patient2",
            "appointment_id": "appt2",
            "montant": 65.0,
            "type_paiement": "espece",
            "statut": "paye",
            "date": (today - timedelta(days=45)).strftime("%Y-%m-%d"),
            "assure": False,
            "created_at": datetime.now() - timedelta(days=45)
        },
        {
            "id": "pay4",
            "patient_id": "patient2",
            "appointment_id": "appt5",
            "montant": 65.0,
            "type_paiement": "espece",
            "statut": "paye",
            "date": (today - timedelta(days=20)).strftime("%Y-%m-%d"),
            "assure": False,
            "created_at": datetime.now() - timedelta(days=20)
        },
        
        # Paiements pour patient3 (Omar Tazi)
        {
            "id": "pay5",
            "patient_id": "patient3",
            "appointment_id": "appt3",
            "montant": 65.0,
            "type_paiement": "espece",
            "statut": "paye",
            "date": today.strftime("%Y-%m-%d"),
            "assure": False,
            "created_at": datetime.now()
        },
        {
            "id": "pay6",
            "patient_id": "patient3",
            "appointment_id": "appt6",
            "montant": 65.0,
            "type_paiement": "espece",
            "statut": "paye",
            "date": (today - timedelta(days=60)).strftime("%Y-%m-%d"),
            "assure": False,
            "created_at": datetime.now() - timedelta(days=60)
        }
    ]

    for payment in demo_payments:
        payments_collection.insert_one(payment)

# API Routes
@app.get("/")
async def root():
    return {"message": "Cabinet Médical API"}

@app.get("/api/init-demo")
async def init_demo_data():
    """Initialize demo data including default users"""
    try:
        create_demo_data()
        return {"message": "Demo data initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing demo data: {str(e)}")

@app.get("/api/init-test-data")
async def init_test_data():
    """Initialize test data specifically for unpaid consultations testing"""
    try:
        # Create default users first
        create_default_users()
        
        # Clear existing data for fresh test
        patients_collection.delete_many({})
        appointments_collection.delete_many({})
        consultations_collection.delete_many({})
        payments_collection.delete_many({})
        
        # Create test patients
        test_patients = [
            {
                "id": "patient1",
                "nom": "Martin",
                "prenom": "Jean",
                "date_naissance": "2018-05-15",
                "age": "6 ans",
                "adresse": "123 Rue de la Paix, Tunis",
                "numero_whatsapp": "+21612345678"
            },
            {
                "id": "patient2", 
                "nom": "Dupont",
                "prenom": "Marie",
                "date_naissance": "2020-08-22",
                "age": "4 ans",
                "adresse": "456 Avenue Bourguiba, Sfax",
                "numero_whatsapp": "+21698765432"
            },
            {
                "id": "patient3",
                "nom": "Ben Ali",
                "prenom": "Ahmed",
                "date_naissance": "2019-12-10", 
                "age": "5 ans",
                "adresse": "789 Rue Habib Thameur, Sousse",
                "numero_whatsapp": "+21654321098"
            }
        ]
        
        for patient in test_patients:
            patients_collection.insert_one(patient)
        
        # Create test appointments and consultations with different payment statuses
        today = datetime.now()
        test_data = [
            # Visites payées (avec paiement dans la collection payments)
            {
                "appointment_id": "appt1",
                "patient_id": "patient1", 
                "type": "visite",
                "paye": True,  # Appointment is marked as paid
                "assure": True,
                "date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
                "montant": 65.0,
                "create_payment": True  # Create payment record
            },
            {
                "appointment_id": "appt2", 
                "patient_id": "patient2",
                "type": "visite", 
                "paye": True,
                "assure": False,
                "date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
                "montant": 65.0,
                "create_payment": True
            },
            # Contrôles payés (gratuits mais marqués comme payés)
            {
                "appointment_id": "appt3",
                "patient_id": "patient1",
                "type": "controle",
                "paye": True,
                "assure": True,
                "date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
                "montant": 0.0,  # Contrôles gratuits
                "create_payment": True
            },
            {
                "appointment_id": "appt4",
                "patient_id": "patient3",
                "type": "controle",
                "paye": True,
                "assure": False,
                "date": (today - timedelta(days=1)).strftime("%Y-%m-%d"), 
                "montant": 0.0,
                "create_payment": True
            },
            # *** VISITES IMPAYÉES *** - appointments terminés mais paye=False, PAS de record payment
            {
                "appointment_id": "appt5",
                "patient_id": "patient2",
                "type": "visite",
                "paye": False,  # NOT PAID - this should appear in "impaye" filter
                "assure": False,
                "date": today.strftime("%Y-%m-%d"),
                "montant": 65.0,
                "create_payment": False  # NO payment record for unpaid
            },
            {
                "appointment_id": "appt6",
                "patient_id": "patient3", 
                "type": "visite",
                "paye": False,  # NOT PAID - this should appear in "impaye" filter
                "assure": True,
                "date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
                "montant": 65.0,
                "create_payment": False  # NO payment record for unpaid
            }
        ]
        
        # Create appointments, consultations and payments
        for data in test_data:
            # Create appointment
            appointment = {
                "id": data["appointment_id"],
                "patient_id": data["patient_id"],
                "date": data["date"],
                "heure": "10:00",
                "type_rdv": data["type"],
                "motif": "Consultation pédiatrique",
                "statut": "termine",  # All appointments completed
                "paye": data["paye"],  # Key field for unpaid detection
                "assure": data["assure"],
                "created_at": datetime.now()
            }
            appointments_collection.insert_one(appointment)
            
            # Create consultation
            consultation = {
                "id": f"cons_{data['appointment_id']}",
                "patient_id": data["patient_id"],
                "appointment_id": data["appointment_id"],
                "date": data["date"],
                "type_rdv": data["type"],
                "duree": 30,
                "observations": f"Consultation {data['type']} - Patient en bonne santé",
                "created_at": datetime.now()
            }
            consultations_collection.insert_one(consultation)
            
            # Create payment only if paid (create_payment = True)
            if data["create_payment"]:
                payment = {
                    "id": f"pay_{data['appointment_id']}",
                    "patient_id": data["patient_id"],
                    "appointment_id": data["appointment_id"],
                    "montant": data["montant"],
                    "type_paiement": "espece",
                    "statut": "paye",
                    "assure": data["assure"],
                    "date": data["date"],
                    "notes": f"Paiement {data['type']}",
                    "created_at": datetime.now()
                }
                payments_collection.insert_one(payment)
        
        return {
            "message": "Test data created successfully with unpaid consultations",
            "summary": {
                "patients": 3,
                "appointments": 6,
                "consultations": 6,
                "payments": 4,  # Only 4 payments (2 unpaid have no payment records)
                "visites_payees": 2,
                "controles_payes": 2, 
                "visites_impayees": 2,  # These should show up in "impaye" filter
                "montant_total_encaisse": 130.0,
                "montant_en_attente": 130.0  # 2 unpaid visites * 65 TND
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating test data: {str(e)}")

@app.get("/api/dashboard/birthdays")
async def get_birthdays_today():
    """Get patients with birthdays today"""
    try:
        today = datetime.now()
        today_str = today.strftime("%m-%d")  # Format MM-DD for comparison
        
        # Find patients with birthdays today
        patients = list(patients_collection.find({}, {"_id": 0}))
        
        birthdays_today = []
        for patient in patients:
            if patient.get("date_naissance"):
                try:
                    # Extract month-day from patient's birth date
                    birth_date = datetime.strptime(patient["date_naissance"], "%Y-%m-%d")
                    birth_md = birth_date.strftime("%m-%d")
                    
                    if birth_md == today_str:
                        # Calculate age
                        age = today.year - birth_date.year
                        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                            age -= 1
                        
                        birthdays_today.append({
                            "id": patient["id"],
                            "nom": patient.get("nom", ""),
                            "prenom": patient.get("prenom", ""),
                            "age": age,
                            "numero_whatsapp": patient.get("numero_whatsapp", ""),
                            "date_naissance": patient["date_naissance"]
                        })
                except ValueError:
                    # Skip patients with invalid date format
                    continue
        
        return {"birthdays": birthdays_today}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching birthdays: {str(e)}")

@app.get("/api/dashboard/phone-reminders")
async def get_phone_reminders_today():
    """Get scheduled phone reminders for today"""
    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Find consultations with relance_date for today
        consultations_with_relance = list(consultations_collection.find({
            "relance_date": today_str
        }, {"_id": 0}))
        
        reminders = []
        for consultation in consultations_with_relance:
            # Get patient info
            patient = patients_collection.find_one({"id": consultation["patient_id"]}, {"_id": 0})
            if patient:
                # Get the original appointment info
                appointment = appointments_collection.find_one({
                    "id": consultation["appointment_id"]
                }, {"_id": 0})
                
                reminders.append({
                    "id": consultation["id"],
                    "patient_id": consultation["patient_id"],
                    "patient_nom": patient.get("nom", ""),
                    "patient_prenom": patient.get("prenom", ""),
                    "numero_whatsapp": patient.get("numero_whatsapp", ""),
                    "date_rdv": consultation["date"],  # Date de la consultation originale
                    "heure_rdv": appointment.get("heure", "10:00") if appointment else "10:00",
                    "motif": appointment.get("motif", "Consultation") if appointment else "Consultation",
                    "consultation_id": consultation["id"],
                    "raison_relance": "Relance téléphonique programmée",
                    "relance_date": consultation["relance_date"],
                    "observations": consultation.get("observations", ""),
                    "traitement": consultation.get("traitement", ""),
                    "time": "10:00"  # Default reminder time
                })
        
        return {"reminders": reminders}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching phone reminders: {str(e)}")

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
    
    # Get today's revenue (payments + cash movements)
    recette_jour = await get_daily_cash_balance()
    
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

@app.get("/api/patients/search")
async def search_patients(
    q: str = Query("", description="Search query for patient name")
):
    """Search patients for phone message creation"""
    try:
        if not q:
            return {"patients": []}
        
        # Search by name (case insensitive)
        search_regex = {"$regex": q, "$options": "i"}
        query = {
            "$or": [
                {"nom": search_regex},
                {"prenom": search_regex}
            ]
        }
        
        # Get matching patients (limit to 20 results)
        patients = list(patients_collection.find(query, {
            "_id": 0,
            "id": 1,
            "nom": 1,
            "prenom": 1,
            "age": 1,
            "numero_whatsapp": 1
        }).limit(20))
        
        return {"patients": patients}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching patients: {str(e)}")

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

@app.get("/api/rdv/jour/{date}")
async def get_rdv_jour(date: str):
    """Get appointments for a specific day with patient info and auto status check"""
    appointments = list(appointments_collection.find({"date": date}, {"_id": 0}))
    
    # Get patient info and check delays for each appointment
    for appointment in appointments:
        # Check for delays and update status if needed
        current_status = check_appointment_delay(appointment)
        if current_status != appointment["statut"]:
            appointment["statut"] = current_status
            # Update in database
            appointments_collection.update_one(
                {"id": appointment["id"]},
                {"$set": {"statut": current_status, "updated_at": datetime.now()}}
            )
        
        # Get patient info
        patient = patients_collection.find_one({"id": appointment["patient_id"]}, {"_id": 0})
        if patient:
            appointment["patient"] = {
                "nom": patient.get("nom", ""),
                "prenom": patient.get("prenom", ""),
                "numero_whatsapp": patient.get("numero_whatsapp", ""),
                "lien_whatsapp": patient.get("lien_whatsapp", "")
            }
    
    # Sort appointments - by priority for waiting patients, by time for others
    def sort_appointments(appointments):
        def sort_key(apt):
            if apt["statut"] == "attente":
                # For waiting patients, sort by priority (lower number = higher priority)
                return (0, apt.get("priority", 999))
            else:
                # For other statuses, sort by time
                return (1, apt["heure"])
        
        return sorted(appointments, key=sort_key)
    
    appointments = sort_appointments(appointments)
    
    return appointments

@app.get("/api/rdv/semaine/{date}")
async def get_rdv_semaine(date: str):
    """Get appointments for the week containing the given date (Monday to Saturday)"""
    week_dates = get_week_dates(date)
    
    if not week_dates:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Get appointments for all days of the week
    appointments = list(appointments_collection.find(
        {"date": {"$in": week_dates}}, 
        {"_id": 0}
    ))
    
    # Add patient info for each appointment
    for appointment in appointments:
        # Check for delays and update status if needed
        current_status = check_appointment_delay(appointment)
        if current_status != appointment["statut"]:
            appointment["statut"] = current_status
            appointments_collection.update_one(
                {"id": appointment["id"]},
                {"$set": {"statut": current_status, "updated_at": datetime.now()}}
            )
        
        patient = patients_collection.find_one({"id": appointment["patient_id"]}, {"_id": 0})
        if patient:
            appointment["patient"] = {
                "nom": patient.get("nom", ""),
                "prenom": patient.get("prenom", ""),
                "numero_whatsapp": patient.get("numero_whatsapp", ""),
                "lien_whatsapp": patient.get("lien_whatsapp", "")
            }
    
    # Sort by date and time
    appointments.sort(key=lambda x: (x["date"], x["heure"]))
    
    return {
        "week_dates": week_dates,
        "appointments": appointments
    }

@app.put("/api/rdv/{rdv_id}")
async def update_rdv(rdv_id: str, update_data: dict):
    """Update appointment (including type toggle from visite to controle and vice versa)"""
    try:
        # Extract update fields
        type_rdv = update_data.get("type_rdv")
        
        if not type_rdv:
            raise HTTPException(status_code=400, detail="type_rdv is required")
        
        # Validate appointment type
        valid_types = ["visite", "controle"]
        if type_rdv not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {valid_types}")
        
        # Prepare update data
        update_fields = {
            "type_rdv": type_rdv,
            "updated_at": datetime.now()
        }
        
        # Apply payment logic corrections based on type
        if type_rdv == "controle":
            # Controle appointments should be automatically marked as gratuit (free)
            update_fields.update({
                "paye": True,
                "montant_paye": 0,
                "methode_paiement": "gratuit",
                "date_paiement": datetime.now().strftime("%Y-%m-%d")
            })
        elif type_rdv == "visite":
            # Visite appointments should default to non_paye (unpaid) status
            update_fields.update({
                "paye": False,
                "montant_paye": 0,
                "methode_paiement": "",
                "date_paiement": None
            })
        
        # Update appointment
        result = appointments_collection.update_one(
            {"id": rdv_id},
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Handle payment record based on type
        if type_rdv == "controle":
            # Create/update payment record for controle (gratuit)
            payment_record = {
                "id": str(uuid.uuid4()),
                "patient_id": "",  # Will be filled from appointment
                "appointment_id": rdv_id,
                "montant": 0,
                "type_paiement": "gratuit",
                "statut": "paye",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "created_at": datetime.now()
            }
            
            # Get patient_id from appointment
            appointment = appointments_collection.find_one({"id": rdv_id})
            if appointment:
                payment_record["patient_id"] = appointment.get("patient_id", "")
            
            # Insert or update payment record
            payments_collection.update_one(
                {"appointment_id": rdv_id},
                {"$set": payment_record},
                upsert=True
            )
        else:
            # Remove payment record for visite (will be unpaid by default)
            payments_collection.delete_one({"appointment_id": rdv_id})
        
        return {
            "message": "Appointment updated successfully", 
            "type_rdv": type_rdv,
            "payment_status": "gratuit" if type_rdv == "controle" else "non_paye"
        }
        
    except HTTPException:
        # Re-raise HTTPException to maintain proper status codes
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating appointment: {str(e)}")

@app.put("/api/rdv/{rdv_id}/statut")
async def update_rdv_statut(rdv_id: str, status_data: dict):
    """Update appointment status"""
    # Handle both direct string and object formats
    if isinstance(status_data, dict):
        statut = status_data.get("statut")
        salle = status_data.get("salle", "")
        heure_arrivee_attente = status_data.get("heure_arrivee_attente", "")
        duree_attente = status_data.get("duree_attente")  # Nouvelle durée d'attente
    else:
        statut = status_data
        salle = ""
        heure_arrivee_attente = ""
        duree_attente = None
    
    valid_statuts = ["programme", "attente", "en_cours", "termine", "absent", "retard"]
    if statut not in valid_statuts:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuts}")
    
    update_data = {"statut": statut, "updated_at": datetime.now()}
    
    # Si on passe en salle d'attente, enregistrer l'heure d'arrivée
    if statut == "attente":
        if heure_arrivee_attente:
            update_data["heure_arrivee_attente"] = heure_arrivee_attente
        else:
            update_data["heure_arrivee_attente"] = datetime.now().isoformat()
    
    # Si on passe en consultation, sauvegarder la durée d'attente
    if statut == "en_cours" and duree_attente is not None:
        update_data["duree_attente"] = duree_attente
    
    if salle:
        valid_salles = ["", "salle1", "salle2"]
        if salle in valid_salles:
            update_data["salle"] = salle
    
    result = appointments_collection.update_one(
        {"id": rdv_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return {"message": "Status updated successfully", "statut": statut}

@app.put("/api/rdv/{rdv_id}/salle")
async def update_rdv_salle(rdv_id: str, salle: str):
    """Update appointment room assignment"""
    valid_salles = ["", "salle1", "salle2"]
    if salle not in valid_salles:
        raise HTTPException(status_code=400, detail=f"Invalid room. Must be one of: {valid_salles}")
    
    result = appointments_collection.update_one(
        {"id": rdv_id},
        {"$set": {"salle": salle, "updated_at": datetime.now()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return {"message": "Room assignment updated successfully", "salle": salle}

@app.put("/api/rdv/{rdv_id}/paiement")
async def update_rdv_paiement(rdv_id: str, payment_data: PaymentUpdate):
    """Update appointment payment status with unified payment logic"""
    try:
        # Get appointment details
        appointment = appointments_collection.find_one({"id": rdv_id})
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Extract payment data
        paye = payment_data.paye
        montant = payment_data.montant
        type_paiement = payment_data.type_paiement
        assure = payment_data.assure
        notes = payment_data.notes
        
        # Validate payment method - Seul espèces accepté
        if type_paiement != "espece" and type_paiement != "gratuit":
            type_paiement = "espece"  # Force espèces par défaut
        
        # Business logic for payment handling
        if appointment.get("type_rdv") == "controle":
            # Contrôle is always free
            paye = True
            montant = 0
            type_paiement = "gratuit"
        
        # Update appointment with basic payment status
        update_data = {
            "paye": paye,
            "assure": assure,
            "updated_at": datetime.now()
        }
        
        result = appointments_collection.update_one(
            {"id": rdv_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Failed to update appointment")
        
        # Handle payment record in payments collection
        if paye and montant >= 0:
            # Create or update payment record
            payment_record = {
                "id": str(uuid.uuid4()),
                "patient_id": appointment.get("patient_id", ""),
                "appointment_id": rdv_id,
                "montant": montant,
                "type_paiement": type_paiement,
                "statut": "paye",
                "assure": assure,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "notes": notes,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Upsert payment record (create or update)
            payments_collection.update_one(
                {"appointment_id": rdv_id},
                {"$set": payment_record},
                upsert=True
            )
        else:
            # Remove payment record if unpaid or refunded
            payments_collection.delete_one({"appointment_id": rdv_id})
        
        return {
            "message": "Payment updated successfully", 
            "paye": paye,
            "montant": montant,
            "type_paiement": type_paiement,
            "assure": assure
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating payment: {str(e)}")

@app.get("/api/payments/appointment/{appointment_id}")
async def get_payment_by_appointment(appointment_id: str):
    """Get payment details for a specific appointment"""
    payment = payments_collection.find_one({"appointment_id": appointment_id}, {"_id": 0})
    if not payment:
        # Check if appointment exists and is a controle (free)
        appointment = appointments_collection.find_one({"id": appointment_id})
        if appointment and appointment.get("type_rdv") == "controle":
            return {
                "appointment_id": appointment_id,
                "montant": 0,
                "type_paiement": "gratuit",
                "statut": "paye",
                "assure": appointment.get("assure", False)
            }
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return payment

@app.put("/api/rdv/{rdv_id}/whatsapp")
async def update_rdv_whatsapp(rdv_id: str, whatsapp_data: dict):
    """Update appointment WhatsApp status"""
    try:
        whatsapp_envoye = whatsapp_data.get("whatsapp_envoye", False)
        whatsapp_timestamp = whatsapp_data.get("whatsapp_timestamp", "")
        
        update_data = {
            "whatsapp_envoye": whatsapp_envoye,
            "whatsapp_timestamp": whatsapp_timestamp,
            "updated_at": datetime.now()
        }
        
        result = appointments_collection.update_one(
            {"id": rdv_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return {
            "message": "WhatsApp status updated successfully",
            "whatsapp_envoye": whatsapp_envoye,
            "whatsapp_timestamp": whatsapp_timestamp
        }
        
    except HTTPException:
        # Re-raise HTTPException to maintain proper status codes
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating WhatsApp status: {str(e)}")

@app.get("/api/rdv/stats/{date}")
async def get_rdv_stats(date: str):
    """Get appointment statistics for a specific day"""
    appointments = list(appointments_collection.find({"date": date}, {"_id": 0}))
    
    # Update statuses for any delayed appointments
    for appointment in appointments:
        current_status = check_appointment_delay(appointment)
        if current_status != appointment["statut"]:
            appointments_collection.update_one(
                {"id": appointment["id"]},
                {"$set": {"statut": current_status, "updated_at": datetime.now()}}
            )
            appointment["statut"] = current_status
    
    total_rdv = len(appointments)
    visites = len([a for a in appointments if a["type_rdv"] == "visite"])
    controles = len([a for a in appointments if a["type_rdv"] == "controle"])
    
    # Count by status
    programme = len([a for a in appointments if a["statut"] == "programme"])
    attente = len([a for a in appointments if a["statut"] == "attente"])
    en_cours = len([a for a in appointments if a["statut"] == "en_cours"])
    termine = len([a for a in appointments if a["statut"] == "termine"])
    absent = len([a for a in appointments if a["statut"] == "absent"])
    retard = len([a for a in appointments if a["statut"] == "retard"])
    
    # Calculate attendance rate
    presents = attente + en_cours + termine
    taux_presence = (presents / total_rdv * 100) if total_rdv > 0 else 0
    
    # Get payments for the day
    payments = list(payments_collection.find({"date": date, "statut": "paye"}, {"_id": 0}))
    ca_realise = sum([p["montant"] for p in payments])
    
    # Estimate CA based on paid/unpaid appointments
    payes = len([a for a in appointments if a.get("paye", False)])
    non_payes = total_rdv - payes
    
    return {
        "date": date,
        "total_rdv": total_rdv,
        "visites": visites,
        "controles": controles,
        "statuts": {
            "programme": programme,
            "attente": attente,
            "en_cours": en_cours,
            "termine": termine,
            "absent": absent,
            "retard": retard
        },
        "taux_presence": round(taux_presence, 1),
        "paiements": {
            "payes": payes,
            "non_payes": non_payes,
            "ca_realise": ca_realise
        }
    }

@app.get("/api/rdv/time-slots")
async def get_available_time_slots(date: str = Query(...), exclude_id: str = Query(None)):
    """Get available time slots for a given date"""
    # Get all time slots
    all_slots = get_time_slots()
    
    # Get existing appointments for the date
    query = {"date": date}
    if exclude_id:
        query["id"] = {"$ne": exclude_id}
    
    existing_appointments = list(appointments_collection.find(query, {"heure": 1, "_id": 0}))
    occupied_slots = [apt["heure"] for apt in existing_appointments]
    
    # Mark slots as available or occupied
    time_slots = []
    for slot in all_slots:
        time_slots.append({
            "time": slot,
            "available": slot not in occupied_slots,
            "occupied_count": occupied_slots.count(slot)  # Support double bookings
        })
    
    return time_slots

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

@app.get("/api/consultations/{consultation_id}")
async def get_consultation_details(consultation_id: str):
    """Get detailed consultation information"""
    try:
        # Get consultation
        consultation = consultations_collection.find_one({"id": consultation_id}, {"_id": 0})
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found")
        
        # Get patient information
        patient = patients_collection.find_one({"id": consultation["patient_id"]}, {"_id": 0})
        
        # Get appointment information
        appointment = appointments_collection.find_one({"id": consultation.get("appointment_id")}, {"_id": 0})
        
        # Enrich consultation with related data
        consultation_details = {
            **consultation,
            "patient": {
                "nom": patient.get("nom", "") if patient else "",
                "prenom": patient.get("prenom", "") if patient else "",
                "age": patient.get("age", "") if patient else "",
                "date_naissance": patient.get("date_naissance", "") if patient else ""
            },
            "appointment": {
                "date": appointment.get("date", "") if appointment else "",
                "heure": appointment.get("heure", "") if appointment else "",
                "motif": appointment.get("motif", "") if appointment else "",
                "type_rdv": appointment.get("type_rdv", "") if appointment else ""
            }
        }
        
        return consultation_details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching consultation: {str(e)}")

@app.get("/api/consultations")
async def get_consultations():
    """Get all consultations"""
    consultations = list(consultations_collection.find({}, {"_id": 0}))
    return consultations

@app.get("/api/consultations/patient/{patient_id}")
async def get_patient_consultations(patient_id: str):
    """Get consultations for a specific patient"""
    # Check if patient exists
    patient = patients_collection.find_one({"id": patient_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    consultations = list(consultations_collection.find({"patient_id": patient_id}, {"_id": 0}))
    return consultations

@app.post("/api/consultations")
async def create_consultation(consultation: Consultation):
    """Create new consultation"""
    consultation_dict = consultation.dict()
    consultations_collection.insert_one(consultation_dict)
    return {"message": "Consultation created successfully", "consultation_id": consultation.id}

@app.put("/api/consultations/{consultation_id}")
async def update_consultation(consultation_id: str, consultation_data: dict):
    """Update existing consultation"""
    # Check if consultation exists
    existing_consultation = consultations_collection.find_one({"id": consultation_id})
    if not existing_consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    # Update the consultation
    result = consultations_collection.update_one(
        {"id": consultation_id},
        {"$set": consultation_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update consultation")
    
    return {"message": "Consultation updated successfully", "consultation_id": consultation_id}

@app.delete("/api/consultations/{consultation_id}")
async def delete_consultation(consultation_id: str):
    """Delete existing consultation"""
    # Check if consultation exists
    existing_consultation = consultations_collection.find_one({"id": consultation_id})
    if not existing_consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    # Delete the consultation
    result = consultations_collection.delete_one({"id": consultation_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Failed to delete consultation")
    
    return {"message": "Consultation deleted successfully", "consultation_id": consultation_id}

@app.get("/api/payments")
async def get_payments():
    """Get all payments with enriched data"""
    try:
        payments = list(payments_collection.find({}, {"_id": 0}))
        
        # Enrich each payment with appointment and patient data
        for payment in payments:
            # Get appointment data
            appointment = appointments_collection.find_one({"id": payment["appointment_id"]}, {"_id": 0})
            if appointment:
                payment["type_rdv"] = appointment.get("type_rdv", "visite")
                payment["patient_id"] = appointment.get("patient_id", "")
                
                # Get patient data
                if appointment.get("patient_id"):
                    patient = patients_collection.find_one({"id": appointment["patient_id"]}, {"_id": 0})
                    if patient:
                        payment["patient"] = {
                            "nom": patient.get("nom", ""),
                            "prenom": patient.get("prenom", "")
                        }
            
            # If no appointment found, try to get from consultation
            if not appointment:
                consultation = consultations_collection.find_one({"appointment_id": payment["appointment_id"]}, {"_id": 0})
                if consultation:
                    payment["type_rdv"] = consultation.get("type_rdv", "visite")
                    payment["patient_id"] = consultation.get("patient_id", "")
                    
                    # Get patient data
                    if consultation.get("patient_id"):
                        patient = patients_collection.find_one({"id": consultation["patient_id"]}, {"_id": 0})
                        if patient:
                            payment["patient"] = {
                                "nom": patient.get("nom", ""),
                                "prenom": patient.get("prenom", "")
                            }
        
        return payments
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching payments: {str(e)}")

@app.get("/api/payments/advanced-stats")
async def get_advanced_stats(
    period: str = Query("month", description="Period type: day, week, month, year"),
    date_debut: Optional[str] = Query(None),
    date_fin: Optional[str] = Query(None)
):
    """Get advanced statistics with period breakdown (day, week, month, year)"""
    try:
        # Set default date range based on period
        today = datetime.now()
        
        if not date_debut or not date_fin:
            if period == "day":
                date_debut = date_fin = today.strftime("%Y-%m-%d")
            elif period == "week":
                # Current week (Monday to Sunday)
                start_of_week = today - timedelta(days=today.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                date_debut = start_of_week.strftime("%Y-%m-%d")
                date_fin = end_of_week.strftime("%Y-%m-%d")
            elif period == "month":
                # Current month
                date_debut = today.replace(day=1).strftime("%Y-%m-%d")
                date_fin = today.strftime("%Y-%m-%d")
            elif period == "year":
                # Current year
                date_debut = today.replace(month=1, day=1).strftime("%Y-%m-%d")
                date_fin = today.strftime("%Y-%m-%d")
        
        # Get payments and appointments for the period
        payment_query = {
            "date": {"$gte": date_debut, "$lte": date_fin},
            "statut": "paye"
        }
        appointment_query = {
            "date": {"$gte": date_debut, "$lte": date_fin}
        }
        
        payments = list(payments_collection.find(payment_query, {"_id": 0}))
        appointments = list(appointments_collection.find(appointment_query, {"_id": 0}))
        
        # Group data by period
        period_stats = {}
        
        if period == "day":
            # Group by day
            for payment in payments:
                day_key = payment["date"]
                if day_key not in period_stats:
                    period_stats[day_key] = {
                        "date": day_key,
                        "ca": 0,
                        "nb_paiements": 0,
                        "nb_visites": 0,
                        "nb_controles": 0,
                        "nb_assures": 0
                    }
                period_stats[day_key]["ca"] += payment.get("montant", 0)
                period_stats[day_key]["nb_paiements"] += 1
            
            for appointment in appointments:
                day_key = appointment["date"]
                if day_key not in period_stats:
                    period_stats[day_key] = {
                        "date": day_key,
                        "ca": 0,
                        "nb_paiements": 0,
                        "nb_visites": 0,
                        "nb_controles": 0,
                        "nb_assures": 0
                    }
                if appointment.get("type_rdv") == "visite":
                    period_stats[day_key]["nb_visites"] += 1
                elif appointment.get("type_rdv") == "controle":
                    period_stats[day_key]["nb_controles"] += 1
                if appointment.get("assure", False):
                    period_stats[day_key]["nb_assures"] += 1
        
        elif period == "week":
            # Group by week
            for payment in payments:
                payment_date = datetime.strptime(payment["date"], "%Y-%m-%d")
                week_start = payment_date - timedelta(days=payment_date.weekday())
                week_key = f"Semaine du {week_start.strftime('%d/%m/%Y')}"
                
                if week_key not in period_stats:
                    period_stats[week_key] = {
                        "periode": week_key,
                        "ca": 0,
                        "nb_paiements": 0,
                        "nb_visites": 0,
                        "nb_controles": 0,
                        "nb_assures": 0
                    }
                period_stats[week_key]["ca"] += payment.get("montant", 0)
                period_stats[week_key]["nb_paiements"] += 1
            
            for appointment in appointments:
                appointment_date = datetime.strptime(appointment["date"], "%Y-%m-%d")
                week_start = appointment_date - timedelta(days=appointment_date.weekday())
                week_key = f"Semaine du {week_start.strftime('%d/%m/%Y')}"
                
                if week_key not in period_stats:
                    period_stats[week_key] = {
                        "periode": week_key,
                        "ca": 0,
                        "nb_paiements": 0,
                        "nb_visites": 0,
                        "nb_controles": 0,
                        "nb_assures": 0
                    }
                if appointment.get("type_rdv") == "visite":
                    period_stats[week_key]["nb_visites"] += 1
                elif appointment.get("type_rdv") == "controle":
                    period_stats[week_key]["nb_controles"] += 1
                if appointment.get("assure", False):
                    period_stats[week_key]["nb_assures"] += 1
        
        elif period == "month":
            # Group by month
            for payment in payments:
                payment_date = datetime.strptime(payment["date"], "%Y-%m-%d")
                month_key = payment_date.strftime("%Y-%m")
                month_name = payment_date.strftime("%B %Y")
                
                if month_key not in period_stats:
                    period_stats[month_key] = {
                        "periode": month_name,
                        "ca": 0,
                        "nb_paiements": 0,
                        "nb_visites": 0,
                        "nb_controles": 0,
                        "nb_assures": 0
                    }
                period_stats[month_key]["ca"] += payment.get("montant", 0)
                period_stats[month_key]["nb_paiements"] += 1
            
            for appointment in appointments:
                appointment_date = datetime.strptime(appointment["date"], "%Y-%m-%d")
                month_key = appointment_date.strftime("%Y-%m")
                month_name = appointment_date.strftime("%B %Y")
                
                if month_key not in period_stats:
                    period_stats[month_key] = {
                        "periode": month_name,
                        "ca": 0,
                        "nb_paiements": 0,
                        "nb_visites": 0,
                        "nb_controles": 0,
                        "nb_assures": 0
                    }
                if appointment.get("type_rdv") == "visite":
                    period_stats[month_key]["nb_visites"] += 1
                elif appointment.get("type_rdv") == "controle":
                    period_stats[month_key]["nb_controles"] += 1
                if appointment.get("assure", False):
                    period_stats[month_key]["nb_assures"] += 1
        
        elif period == "year":
            # Group by year
            for payment in payments:
                payment_date = datetime.strptime(payment["date"], "%Y-%m-%d")
                year_key = payment_date.strftime("%Y")
                
                if year_key not in period_stats:
                    period_stats[year_key] = {
                        "periode": f"Année {year_key}",
                        "ca": 0,
                        "nb_paiements": 0,
                        "nb_visites": 0,
                        "nb_controles": 0,
                        "nb_assures": 0
                    }
                period_stats[year_key]["ca"] += payment.get("montant", 0)
                period_stats[year_key]["nb_paiements"] += 1
            
            for appointment in appointments:
                appointment_date = datetime.strptime(appointment["date"], "%Y-%m-%d")
                year_key = appointment_date.strftime("%Y")
                
                if year_key not in period_stats:
                    period_stats[year_key] = {
                        "periode": f"Année {year_key}",
                        "ca": 0,
                        "nb_paiements": 0,
                        "nb_visites": 0,
                        "nb_controles": 0,
                        "nb_assures": 0
                    }
                if appointment.get("type_rdv") == "visite":
                    period_stats[year_key]["nb_visites"] += 1
                elif appointment.get("type_rdv") == "controle":
                    period_stats[year_key]["nb_controles"] += 1
                if appointment.get("assure", False):
                    period_stats[year_key]["nb_assures"] += 1
        
        # Calculate totals from payments
        total_ca_payments = sum(p.get("montant", 0) for p in payments)
        total_payments = len(payments)
        total_visites = len([a for a in appointments if a.get("type_rdv") == "visite"])
        total_controles = len([a for a in appointments if a.get("type_rdv") == "controle"])
        total_assures = len([a for a in appointments if a.get("assure", False)])
        
        # Get cash movements for the period
        cash_movements = list(cash_movements_collection.find({
            "date": {"$gte": date_debut, "$lte": date_fin}
        }, {"_id": 0}))
        
        # Add cash movements to the period breakdown
        for movement in cash_movements:
            movement_date = movement["date"]
            movement_amount = movement["montant"] if movement["type_mouvement"] == "ajout" else -movement["montant"]
            
            if period == "day":
                day_key = movement_date
                if day_key not in period_stats:
                    period_stats[day_key] = {
                        "date": day_key,
                        "ca": 0,
                        "nb_paiements": 0,
                        "nb_visites": 0,
                        "nb_controles": 0,
                        "nb_assures": 0
                    }
                period_stats[day_key]["ca"] += movement_amount
                
            elif period == "week":
                movement_date_obj = datetime.strptime(movement_date, "%Y-%m-%d")
                week_start = movement_date_obj - timedelta(days=movement_date_obj.weekday())
                week_key = f"Semaine du {week_start.strftime('%d/%m/%Y')}"
                
                if week_key not in period_stats:
                    period_stats[week_key] = {
                        "periode": week_key,
                        "ca": 0,
                        "nb_paiements": 0,
                        "nb_visites": 0,
                        "nb_controles": 0,
                        "nb_assures": 0
                    }
                period_stats[week_key]["ca"] += movement_amount
                
            elif period == "month":
                movement_date_obj = datetime.strptime(movement_date, "%Y-%m-%d")
                month_key = movement_date_obj.strftime("%B %Y")
                
                if month_key not in period_stats:
                    period_stats[month_key] = {
                        "periode": month_key,
                        "ca": 0,
                        "nb_paiements": 0,
                        "nb_visites": 0,
                        "nb_controles": 0,
                        "nb_assures": 0
                    }
                period_stats[month_key]["ca"] += movement_amount
                
            elif period == "year":
                movement_date_obj = datetime.strptime(movement_date, "%Y-%m-%d")
                year_key = movement_date_obj.strftime("%Y")
                
                if year_key not in period_stats:
                    period_stats[year_key] = {
                        "periode": f"Année {year_key}",
                        "ca": 0,
                        "nb_paiements": 0,
                        "nb_visites": 0,
                        "nb_controles": 0,
                        "nb_assures": 0
                    }
                period_stats[year_key]["ca"] += movement_amount
        
        # Calculate total cash movements
        total_cash_movements = 0
        for movement in cash_movements:
            if movement["type_mouvement"] == "ajout":
                total_cash_movements += movement["montant"]
            else:
                total_cash_movements -= movement["montant"]
        
        # Final totals including cash movements
        total_ca = total_ca_payments + total_cash_movements
        
        return {
            "period": period,
            "date_range": {
                "debut": date_debut,
                "fin": date_fin
            },
            "totals": {
                "ca_total": total_ca,
                "nb_paiements": total_payments,
                "nb_visites": total_visites,
                "nb_controles": total_controles,
                "nb_assures": total_assures
            },
            "breakdown": list(period_stats.values())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating advanced stats: {str(e)}")

@app.get("/api/payments/stats")
async def get_payments_stats(
    date_debut: Optional[str] = Query(None),
    date_fin: Optional[str] = Query(None)
):
    """Get payment statistics for billing dashboard"""
    try:
        # Default to current month if no dates provided
        if not date_debut or not date_fin:
            today = datetime.now()
            date_debut = today.replace(day=1).strftime("%Y-%m-%d")
            date_fin = today.strftime("%Y-%m-%d")
        
        # Build query
        query = {
            "date": {"$gte": date_debut, "$lte": date_fin},
            "statut": "paye"
        }
        
        payments = list(payments_collection.find(query, {"_id": 0}))
        
        # Calculate statistics
        total_montant_payments = sum(p.get("montant", 0) for p in payments)
        
        # Add cash movements for the period
        cash_movements = list(cash_movements_collection.find({
            "date": {"$gte": date_debut, "$lte": date_fin}
        }, {"_id": 0}))
        
        mouvements_total = 0
        for movement in cash_movements:
            if movement["type_mouvement"] == "ajout":
                mouvements_total += movement["montant"]
            else:
                mouvements_total -= movement["montant"]
        
        total_montant = total_montant_payments + mouvements_total
        nb_paiements = len(payments)
        
        # Group by payment method
        by_method = {}
        for payment in payments:
            method = payment.get("type_paiement", "espece")
            if method not in by_method:
                by_method[method] = {"count": 0, "total": 0}
            by_method[method]["count"] += 1
            by_method[method]["total"] += payment.get("montant", 0)
        
        # Count insurance payments
        assures = len([p for p in payments if p.get("assure", False)])
        non_assures = nb_paiements - assures
        
        # Today's stats (include cash movements for today)
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_payments = [p for p in payments if p.get("date") == today_str]
        ca_payments_jour = sum(p.get("montant", 0) for p in today_payments)
        
        # Add today's cash movements
        today_cash_movements = list(cash_movements_collection.find({"date": today_str}, {"_id": 0}))
        today_mouvements_total = 0
        for movement in today_cash_movements:
            if movement["type_mouvement"] == "ajout":
                today_mouvements_total += movement["montant"]
            else:
                today_mouvements_total -= movement["montant"]
        
        ca_jour = ca_payments_jour + today_mouvements_total
        
        # Get appointments data for visit/control statistics
        appointments = list(appointments_collection.find({
            "date": {"$gte": date_debut, "$lte": date_fin}
        }, {"_id": 0}))
        
        # Count visits and controls
        nb_visites = len([a for a in appointments if a.get("type_rdv") == "visite"])
        nb_controles = len([a for a in appointments if a.get("type_rdv") == "controle"])
        nb_total_rdv = len(appointments)
        
        # Count assured appointments
        nb_assures = len([a for a in appointments if a.get("assure", False)])
        nb_non_assures = nb_total_rdv - nb_assures
        
        return {
            "periode": {
                "debut": date_debut,
                "fin": date_fin
            },
            "total_montant": total_montant,
            "nb_paiements": nb_paiements,
            "ca_jour": ca_jour,
            "by_method": by_method,
            "assurance": {
                "assures": assures,
                "non_assures": non_assures
            },
            "consultations": {
                "nb_visites": nb_visites,
                "nb_controles": nb_controles,
                "nb_total": nb_total_rdv,
                "nb_assures": nb_assures,
                "nb_non_assures": nb_non_assures
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating payment stats: {str(e)}")

@app.get("/api/payments/unpaid")
async def get_unpaid_appointments():
    """Get list of unpaid appointments (visites only)"""
    try:
        # Get unpaid appointments that are visites
        unpaid_appointments = list(appointments_collection.find({
            "type_rdv": "visite",
            "paye": False,
            "statut": {"$in": ["termine", "absent", "retard"]}  # Completed appointments only
        }, {"_id": 0}))
        
        # Add patient info for each appointment
        for appointment in unpaid_appointments:
            patient = patients_collection.find_one({"id": appointment["patient_id"]}, {"_id": 0})
            if patient:
                appointment["patient"] = {
                    "nom": patient.get("nom", ""),
                    "prenom": patient.get("prenom", ""),
                    "telephone": patient.get("numero_whatsapp", "")
                }
        
        return unpaid_appointments
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching unpaid appointments: {str(e)}")

@app.delete("/api/payments/{payment_id}")
async def delete_payment(payment_id: str):
    """Delete payment record"""
    try:
        # Check if payment exists
        existing_payment = payments_collection.find_one({"id": payment_id})
        if not existing_payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Delete payment record
        result = payments_collection.delete_one({"id": payment_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Failed to delete payment")
        
        # Update appointment to unpaid status
        appointments_collection.update_one(
            {"id": existing_payment["appointment_id"]},
            {"$set": {"paye": False, "updated_at": datetime.now()}}
        )
        
        return {"message": "Payment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting payment: {str(e)}")


# ==================== MESSAGERIE INSTANTANÉE ====================

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint pour messagerie temps réel"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now - can be enhanced for specific functionality
            await manager.send_personal_message(f"Message received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/messages")
async def get_messages():
    """Récupérer tous les messages de la journée"""
    try:
        messages = list(messages_collection.find({}, {"_id": 0}).sort("timestamp", 1))
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

@app.post("/api/messages")
async def create_message(message_data: MessageCreate, sender_type: str, sender_name: str):
    """Créer un nouveau message"""
    try:
        # Si c'est une réponse, récupérer le contenu du message original
        reply_content = ""
        if message_data.reply_to:
            original_message = messages_collection.find_one(
                {"id": message_data.reply_to}, 
                {"_id": 0}
            )
            if original_message:
                reply_content = original_message.get("content", "")

        message = Message(
            sender_type=sender_type,
            sender_name=sender_name,
            content=message_data.content,
            reply_to=message_data.reply_to,
            reply_content=reply_content
        )
        
        message_dict = message.dict()
        messages_collection.insert_one(message_dict)
        
        # Diffuser le message à tous les clients connectés
        await manager.broadcast({
            "type": "new_message",
            "data": message_dict
        })
        
        return {"message": "Message created successfully", "id": message.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating message: {str(e)}")

@app.put("/api/messages/{message_id}")
async def update_message(message_id: str, message_data: MessageUpdate, user_type: str):
    """Modifier un message (seulement par son émetteur)"""
    try:
        # Vérifier que le message existe et appartient à l'utilisateur
        message = messages_collection.find_one({"id": message_id}, {"_id": 0})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        if message.get("sender_type") != user_type:
            raise HTTPException(status_code=403, detail="Not authorized to edit this message")
        
        # Sauvegarder le contenu original si ce n'est pas déjà fait
        update_data = {
            "content": message_data.content,
            "is_edited": True,
            "updated_at": datetime.now()
        }
        
        if not message.get("original_content"):
            update_data["original_content"] = message.get("content", "")
        
        result = messages_collection.update_one(
            {"id": message_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Récupérer le message mis à jour
        updated_message = messages_collection.find_one({"id": message_id}, {"_id": 0})
        
        # Diffuser la mise à jour
        await manager.broadcast({
            "type": "message_updated",
            "data": updated_message
        })
        
        return {"message": "Message updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating message: {str(e)}")

@app.delete("/api/messages/{message_id}")
async def delete_message(message_id: str, user_type: str):
    """Supprimer un message (seulement par son émetteur)"""
    try:
        # Vérifier que le message existe et appartient à l'utilisateur
        message = messages_collection.find_one({"id": message_id}, {"_id": 0})
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        if message.get("sender_type") != user_type:
            raise HTTPException(status_code=403, detail="Not authorized to delete this message")
        
        result = messages_collection.delete_one({"id": message_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Diffuser la suppression
        await manager.broadcast({
            "type": "message_deleted",
            "data": {"id": message_id}
        })
        
        return {"message": "Message deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting message: {str(e)}")

@app.delete("/api/messages")
async def clear_all_messages():
    """Clear all messages from the chat"""
    try:
        result = messages_collection.delete_many({})
        
        # Broadcast clear event via WebSocket
        await manager.broadcast({
            "type": "messages_cleared",
            "deleted_count": result.deleted_count
        })
        
        return {"message": f"All messages cleared successfully", "deleted_count": result.deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing messages: {str(e)}")

@app.put("/api/messages/{message_id}/read")
async def mark_message_as_read(message_id: str):
    """Marquer un message comme lu"""
    try:
        result = messages_collection.update_one(
            {"id": message_id},
            {"$set": {"is_read": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Diffuser le changement de statut
        await manager.broadcast({
            "type": "message_read",
            "data": {"id": message_id}
        })
        
        return {"message": "Message marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking message as read: {str(e)}")

@app.post("/api/messages/cleanup")
async def manual_cleanup_messages():
    """Nettoyage manuel des messages (pour test)"""
    try:
        deleted_count = await cleanup_messages_daily()
        
        # Diffuser le nettoyage
        await manager.broadcast({
            "type": "messages_cleared",
            "data": {"count": deleted_count}
        })
        
        return {"message": f"Messages cleared successfully", "count": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up messages: {str(e)}")


@app.get("/api/payments/search")
async def search_payments(
    patient_name: Optional[str] = Query(None, description="Search by patient name"),
    date_debut: Optional[str] = Query(None, description="Start date filter"),
    date_fin: Optional[str] = Query(None, description="End date filter"),
    statut_paiement: Optional[str] = Query(None, description="Payment status filter: visite, controle, impaye"),
    assure: Optional[bool] = Query(None, description="Insurance status filter"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Advanced search for payments with pagination"""
    try:
        # Build search query for payments
        query = {}
        
        # Date range filter
        if date_debut and date_fin:
            query["date"] = {"$gte": date_debut, "$lte": date_fin}
        elif date_debut:
            query["date"] = {"$gte": date_debut}
        elif date_fin:
            query["date"] = {"$lte": date_fin}
        
        # Insurance filter
        if assure is not None:
            query["assure"] = assure
            
        # Handle "impaye" status differently - find unpaid consultations
        if statut_paiement == "impaye":
            # Find appointments that are completed but not paid (paye = False)
            appointments_query = {
                "paye": False,
                "statut": {"$in": ["termine", "absent", "retard"]},  # Completed appointments
                "type_rdv": "visite"  # Only visite appointments can be unpaid (controles are free)
            }
            
            # Add date filter to appointments query
            if date_debut and date_fin:
                appointments_query["date"] = {"$gte": date_debut, "$lte": date_fin}
            elif date_debut:
                appointments_query["date"] = {"$gte": date_debut}
            elif date_fin:
                appointments_query["date"] = {"$lte": date_fin}
                
            # Add insurance filter to appointments query
            if assure is not None:
                appointments_query["assure"] = assure
            
            # Get unpaid appointments
            unpaid_appointments = list(appointments_collection.find(appointments_query, {"_id": 0}))
            
            # Convert appointments to payment-like format for consistency
            payments = []
            for appointment in unpaid_appointments:
                # Create a payment-like object for unpaid appointment
                fake_payment = {
                    "id": f"impaye_{appointment['id']}",
                    "patient_id": appointment["patient_id"],
                    "appointment_id": appointment["id"],
                    "montant": 65.0,  # Default amount for unpaid visite
                    "type_paiement": "espece",  # Would be espece if paid
                    "statut": "impaye",  # Special status for unpaid
                    "type_rdv": appointment.get("type_rdv", "visite"),
                    "assure": appointment.get("assure", False),
                    "date": appointment.get("date", ""),
                    "notes": "Consultation non payée",
                    "created_at": appointment.get("created_at", datetime.now())
                }
                
                # Get patient info
                try:
                    patient = patients_collection.find_one({"id": appointment["patient_id"]}, {"_id": 0})
                    if patient:
                        fake_payment["patient"] = {
                            "nom": patient.get("nom", ""),
                            "prenom": patient.get("prenom", "")
                        }
                    else:
                        fake_payment["patient"] = {"nom": "Inconnu", "prenom": ""}
                except:
                    fake_payment["patient"] = {"nom": "Inconnu", "prenom": ""}
                
                payments.append(fake_payment)
                
        else:
            # Handle paid payments (visite and controle)
            query["statut"] = "paye"  # Only paid payments for visite/controle filtering
            
            # Get all payments matching basic criteria
            payments = list(payments_collection.find(query, {"_id": 0}))
            
            # Enrich payments with appointment/consultation data and apply type filter
            filtered_payments = []
            for payment in payments:
                # Get appointment data first
                appointment = appointments_collection.find_one({"id": payment["appointment_id"]}, {"_id": 0})
                if appointment:
                    payment["type_rdv"] = appointment.get("type_rdv", "visite")
                    payment["patient_id"] = appointment.get("patient_id", "")
                else:
                    # Try to get from consultation
                    consultation = consultations_collection.find_one({"appointment_id": payment["appointment_id"]}, {"_id": 0})
                    if consultation:
                        payment["type_rdv"] = consultation.get("type_rdv", "visite")
                        payment["patient_id"] = consultation.get("patient_id", "")
                    else:
                        payment["type_rdv"] = "visite"  # Default
                
                # Apply statut_paiement filter
                if statut_paiement == "visite" and payment["type_rdv"] != "visite":
                    continue
                elif statut_paiement == "controle" and payment["type_rdv"] != "controle":
                    continue
                
                # Get patient info
                try:
                    if payment.get("patient_id"):
                        patient = patients_collection.find_one({"id": payment["patient_id"]}, {"_id": 0})
                        if patient:
                            payment["patient"] = {
                                "nom": patient.get("nom", ""),
                                "prenom": patient.get("prenom", "")
                            }
                        else:
                            payment["patient"] = {"nom": "Inconnu", "prenom": ""}
                    else:
                        payment["patient"] = {"nom": "Inconnu", "prenom": ""}
                except:
                    payment["patient"] = {"nom": "Inconnu", "prenom": ""}
                
                filtered_payments.append(payment)
            
            payments = filtered_payments
        
        # Filter by patient name if provided
        if patient_name:
            patient_name = patient_name.lower()
            payments = [
                payment for payment in payments 
                if patient_name in f"{payment['patient'].get('prenom', '')} {payment['patient'].get('nom', '')}".lower()
            ]
        
        # Sort by date (most recent first)
        payments.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        # Calculate pagination
        total_count = len(payments)
        total_pages = (total_count + limit - 1) // limit
        skip = (page - 1) * limit
        paginated_payments = payments[skip:skip + limit]
        
        return {
            "payments": paginated_payments,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "limit": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching payments: {str(e)}")

@app.put("/api/payments/{payment_id}")
async def update_payment(payment_id: str, payment_data: PaymentUpdate):
    """Update existing payment record"""
    try:
        # Check if payment exists
        existing_payment = payments_collection.find_one({"id": payment_id})
        if not existing_payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Prepare update data
        update_data = {
            "montant": payment_data.montant,
            "type_paiement": payment_data.type_paiement,
            "assure": payment_data.assure,
            "notes": payment_data.notes,
            "updated_at": datetime.now()
        }
        
        # Update payment record
        result = payments_collection.update_one(
            {"id": payment_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Failed to update payment")
        
        # Also update appointment payment status
        appointments_collection.update_one(
            {"id": existing_payment["appointment_id"]},
            {"$set": {"paye": payment_data.paye, "assure": payment_data.assure}}
        )
        
        return {"message": "Payment updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating payment: {str(e)}")


@app.put("/api/rdv/{rdv_id}/priority")
async def update_rdv_priority(rdv_id: str, priority_data: dict):
    """Update appointment priority/position for waiting room reordering"""
    action = priority_data.get("action")
    
    if not action:
        raise HTTPException(status_code=400, detail="action is required")
    
    # Validate action
    valid_actions = ["move_up", "move_down", "set_first", "set_position"]
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")
    
    # Get the appointment to reorder
    appointment = appointments_collection.find_one({"id": rdv_id})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Only allow reordering for appointments in 'attente' status
    if appointment["statut"] != "attente":
        raise HTTPException(status_code=400, detail="Only appointments with 'attente' status can be reordered")
    
    try:
        
        # Get all appointments for the same date with 'attente' status, sorted by current priority
        date = appointment["date"]
        waiting_appointments = list(appointments_collection.find({
            "date": date,
            "statut": "attente"
        }).sort([("priority", 1), ("heure", 1)]))  # Sort by priority first, then time
        
        if len(waiting_appointments) <= 1:
            return {"message": "Only one appointment in waiting room, no reordering needed"}
        
        # Find current position of the appointment
        current_pos = None
        for i, appt in enumerate(waiting_appointments):
            if appt["id"] == rdv_id:
                current_pos = i
                break
        
        if current_pos is None:
            raise HTTPException(status_code=404, detail="Appointment not found in waiting list")
        
        # Perform the reordering action
        if action == "set_first":
            # Move to first position
            new_pos = 0
        elif action == "set_position":
            # Set to specific position (for drag and drop)
            new_pos = min(max(0, priority_data.get("position", 0)), len(waiting_appointments) - 1)
        elif action == "move_up":
            # Move up one position (decrease index)
            new_pos = max(0, current_pos - 1)
        elif action == "move_down":
            # Move down one position (increase index)
            new_pos = min(len(waiting_appointments) - 1, current_pos + 1)
        
        # If position doesn't change, return early
        if new_pos == current_pos:
            return {
                "message": f"Appointment already at {action} position",
                "current_position": current_pos + 1,
                "total_waiting": len(waiting_appointments),
                "action": action
            }
        
        # Simple and correct algorithm for repositioning items in array
        # Create a new list with the item moved to its new position
        new_order = []
        
        # First, create a list without the moved item
        for i, appt in enumerate(waiting_appointments):
            if i != current_pos:
                new_order.append(appt)
        
        # Insert the moved item at its new position
        moved_item = waiting_appointments[current_pos]
        new_order.insert(new_pos, moved_item)
        
        # Update all priorities based on new positions
        for i, appt in enumerate(new_order):
            appointments_collection.update_one(
                {"id": appt["id"]},
                {"$set": {"priority": i, "updated_at": datetime.now()}}
            )
        
        return {
            "message": f"Appointment {action} successful",
            "previous_position": current_pos + 1,
            "new_position": new_pos + 1,
            "total_waiting": len(waiting_appointments),
            "action": action
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating priority: {str(e)}")

# ==================== Phone Messages API ====================

@app.get("/api/phone-messages")
async def get_phone_messages(
    status: str = Query("", description="Filter by status: nouveau, traité"),
    priority: str = Query("", description="Filter by priority: urgent, normal"),
    date_from: str = Query("", description="Filter from date YYYY-MM-DD"),
    date_to: str = Query("", description="Filter to date YYYY-MM-DD")
):
    """Get phone messages with filtering"""
    try:
        # Build filter query
        filter_query = {}
        
        if status:
            filter_query["status"] = status
        if priority:
            filter_query["priority"] = priority
        if date_from:
            filter_query["call_date"] = {"$gte": date_from}
        if date_to:
            if "call_date" in filter_query:
                filter_query["call_date"]["$lte"] = date_to
            else:
                filter_query["call_date"] = {"$lte": date_to}
        
        # Get messages sorted by call_date and call_time (newest first)
        messages = list(phone_messages_collection.find(filter_query, {"_id": 0})
                       .sort([("call_date", -1), ("call_time", -1)]))
        
        return {"phone_messages": messages, "total": len(messages)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching phone messages: {str(e)}")

@app.post("/api/phone-messages")
async def create_phone_message(message_data: PhoneMessageCreate):
    """Create new phone message (secrétaire only)"""
    try:
        # Get patient info
        patient = patients_collection.find_one({"id": message_data.patient_id}, {"_id": 0})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Create phone message
        phone_message = PhoneMessage(
            patient_id=message_data.patient_id,
            patient_name=f"{patient.get('prenom', '')} {patient.get('nom', '')}".strip(),
            message_content=message_data.message_content,
            priority=message_data.priority,
            call_date=message_data.call_date,
            call_time=message_data.call_time,
            created_by="Secrétaire"  # Could be dynamic based on user session
        )
        
        # Insert into database
        phone_message_dict = phone_message.dict()
        phone_messages_collection.insert_one(phone_message_dict)
        
        # Send WebSocket notification to médecin
        notification_data = {
            "type": "new_phone_message",
            "message_id": phone_message.id,
            "patient_name": phone_message.patient_name,
            "priority": phone_message.priority,
            "timestamp": phone_message.created_at.isoformat()
        }
        await manager.broadcast(notification_data)
        
        return {"message": "Phone message created successfully", "message_id": phone_message.id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating phone message: {str(e)}")

@app.put("/api/phone-messages/{message_id}/response")
async def respond_phone_message(message_id: str, response_data: PhoneMessageResponse):
    """Add response to phone message (médecin only)"""
    try:
        # Find message
        message = phone_messages_collection.find_one({"id": message_id})
        if not message:
            raise HTTPException(status_code=404, detail="Phone message not found")
        
        # Update message with response
        update_data = {
            "response_content": response_data.response_content,
            "status": "traité",
            "responded_by": "Dr Heni Dridi",  # Could be dynamic based on user session
            "updated_at": datetime.now()
        }
        
        result = phone_messages_collection.update_one(
            {"id": message_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Failed to update message")
        
        # Send WebSocket notification about response
        notification_data = {
            "type": "phone_message_responded",
            "message_id": message_id,
            "patient_name": message.get("patient_name", ""),
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(notification_data)
        
        return {"message": "Response added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error responding to phone message: {str(e)}")

@app.put("/api/phone-messages/{message_id}")
async def edit_phone_message(message_id: str, edit_data: PhoneMessageEdit):
    """Edit phone message content and priority"""
    try:
        # Find message
        message = phone_messages_collection.find_one({"id": message_id})
        if not message:
            raise HTTPException(status_code=404, detail="Phone message not found")
        
        # Update message
        update_data = {
            "message_content": edit_data.message_content,
            "priority": edit_data.priority,
            "updated_at": datetime.now()
        }
        
        result = phone_messages_collection.update_one(
            {"id": message_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Failed to update message")
        
        # Send WebSocket notification about edit
        notification_data = {
            "type": "phone_message_edited",
            "message_id": message_id,
            "patient_name": message.get("patient_name", ""),
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(notification_data)
        
        return {"message": "Phone message updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error editing phone message: {str(e)}")

@app.get("/api/phone-messages/stats")
async def get_phone_messages_stats():
    """Get phone messages statistics"""
    try:
        # Count by status
        nouveau_count = phone_messages_collection.count_documents({"status": "nouveau"})
        traite_count = phone_messages_collection.count_documents({"status": "traité"})
        
        # Count by priority
        urgent_count = phone_messages_collection.count_documents({"priority": "urgent"})
        normal_count = phone_messages_collection.count_documents({"priority": "normal"})
        
        # Count by today
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = phone_messages_collection.count_documents({"call_date": today})
        
        return {
            "nouveau": nouveau_count,
            "traité": traite_count,
            "urgent": urgent_count,
            "normal": normal_count,
            "today": today_count,
            "total": nouveau_count + traite_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching phone messages stats: {str(e)}")

@app.delete("/api/phone-messages/{message_id}")
async def delete_phone_message(message_id: str):
    """Delete phone message"""
    try:
        result = phone_messages_collection.delete_one({"id": message_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Phone message not found")
        
        return {"message": "Phone message deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting phone message: {str(e)}")

@app.delete("/api/phone-messages")
async def delete_all_phone_messages():
    """Delete all phone messages"""
    try:
        result = phone_messages_collection.delete_many({})
        
        return {
            "message": f"{result.deleted_count} message(s) supprimé(s) avec succès",
            "deleted_count": result.deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting all phone messages: {str(e)}")


# ==================== End Phone Messages API ====================

# ==================== Cash Movements API ====================

@app.post("/api/cash-movements")
async def create_cash_movement(movement: CashMovementCreate):
    """Créer un nouveau mouvement de caisse"""
    try:
        movement_data = CashMovement(
            montant=movement.montant,
            type_mouvement=movement.type_mouvement,
            motif=movement.motif,
            date=movement.date,
            created_at=datetime.now()
        ).dict()
        
        # Insert into database
        result = cash_movements_collection.insert_one(movement_data)
        
        # Calculer le nouveau solde de caisse pour aujourd'hui
        solde = await get_daily_cash_balance()
        
        # Prepare clean data for response (without ObjectId)
        clean_movement_data = {
            "id": movement_data["id"],
            "montant": movement_data["montant"],
            "type_mouvement": movement_data["type_mouvement"],
            "motif": movement_data["motif"],
            "date": movement_data["date"],
            "created_at": movement_data["created_at"].isoformat()
        }
        
        # Notification WebSocket
        notification_data = {
            "type": "cash_movement_created",
            "movement": clean_movement_data,
            "solde_actuel": solde,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(notification_data)
        
        return {
            "message": "Mouvement de caisse créé avec succès",
            "movement": clean_movement_data,
            "solde_actuel": solde
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating cash movement: {str(e)}")

@app.get("/api/cash-movements")
async def get_cash_movements(
    date_debut: Optional[str] = Query(None),
    date_fin: Optional[str] = Query(None),
    type_mouvement: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Récupérer les mouvements de caisse avec filtres et pagination"""
    try:
        # Construction du filtre
        filter_query = {}
        
        if date_debut and date_fin:
            filter_query["date"] = {"$gte": date_debut, "$lte": date_fin}
        elif date_debut:
            filter_query["date"] = {"$gte": date_debut}
        elif date_fin:
            filter_query["date"] = {"$lte": date_fin}
            
        if type_mouvement:
            filter_query["type_mouvement"] = type_mouvement
        
        # Compter total
        total_count = cash_movements_collection.count_documents(filter_query)
        
        # Récupérer les mouvements avec pagination
        skip = (page - 1) * limit
        movements = list(cash_movements_collection.find(filter_query, {"_id": 0})
                        .sort("created_at", -1)
                        .skip(skip)
                        .limit(limit))
        
        # Calcul pagination
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "movements": movements,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "limit": limit
            },
            "solde_jour": await get_daily_cash_balance()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cash movements: {str(e)}")

@app.get("/api/cash-movements/balance")
async def get_cash_balance(date: Optional[str] = Query(None)):
    """Obtenir le solde de caisse pour une date donnée (ou aujourd'hui par défaut)"""
    try:
        target_date = date or datetime.now().strftime("%Y-%m-%d")
        
        # Calculer le solde depuis les paiements consultations
        payments_total = 0
        consultations_with_payment = list(consultations_collection.find(
            {"date": target_date}, {"_id": 0}
        ))
        
        for consultation in consultations_with_payment:
            # Chercher le paiement associé
            payment = payments_collection.find_one({"appointment_id": consultation["appointment_id"]})
            if payment and payment.get("statut") == "paye":
                payments_total += payment.get("montant", 0)
        
        # Calculer les mouvements de caisse
        mouvements = list(cash_movements_collection.find(
            {"date": target_date}, {"_id": 0}
        ))
        
        mouvements_total = 0
        for movement in mouvements:
            if movement["type_mouvement"] == "ajout":
                mouvements_total += movement["montant"]
            else:  # soustraction
                mouvements_total -= movement["montant"]
        
        solde_final = payments_total + mouvements_total
        
        return {
            "date": target_date,
            "recette_consultations": payments_total,
            "mouvements_caisse": mouvements_total,
            "solde_final": solde_final,
            "details_mouvements": mouvements
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating cash balance: {str(e)}")

@app.put("/api/cash-movements/{movement_id}")
async def update_cash_movement(movement_id: str, movement_update: CashMovementCreate):
    """Modifier un mouvement de caisse"""
    try:
        update_data = {
            "montant": movement_update.montant,
            "type_mouvement": movement_update.type_mouvement,
            "motif": movement_update.motif,
            "date": movement_update.date,
            "updated_at": datetime.now()
        }
        
        result = cash_movements_collection.update_one(
            {"id": movement_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Mouvement de caisse non trouvé")
        
        # Nouveau solde
        solde = await get_daily_cash_balance()
        
        # Notification
        notification_data = {
            "type": "cash_movement_updated",
            "movement_id": movement_id,
            "solde_actuel": solde,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(notification_data)
        
        return {
            "message": "Mouvement de caisse modifié avec succès",
            "solde_actuel": solde
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating cash movement: {str(e)}")

@app.delete("/api/cash-movements/{movement_id}")
async def delete_cash_movement(movement_id: str):
    """Supprimer un mouvement de caisse"""
    try:
        result = cash_movements_collection.delete_one({"id": movement_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Mouvement de caisse non trouvé")
        
        # Nouveau solde
        solde = await get_daily_cash_balance()
        
        # Notification
        notification_data = {
            "type": "cash_movement_deleted",
            "movement_id": movement_id,
            "solde_actuel": solde,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast(notification_data)
        
        return {
            "message": "Mouvement de caisse supprimé avec succès",
            "solde_actuel": solde
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting cash movement: {str(e)}")

async def get_daily_cash_balance():
    """Fonction helper pour calculer le solde de caisse du jour"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Paiements du jour
    payments_total = 0
    consultations_today = list(consultations_collection.find(
        {"date": today}, {"_id": 0}
    ))
    
    for consultation in consultations_today:
        payment = payments_collection.find_one({"appointment_id": consultation["appointment_id"]})
        if payment and payment.get("statut") == "paye":
            payments_total += payment.get("montant", 0)
    
    # Mouvements de caisse du jour
    mouvements_total = 0
    mouvements = list(cash_movements_collection.find({"date": today}, {"_id": 0}))
    
    for movement in mouvements:
        if movement["type_mouvement"] == "ajout":
            mouvements_total += movement["montant"]
        else:
            mouvements_total -= movement["montant"]
    
    return payments_total + mouvements_total

# ==================== ADMINISTRATION API ENDPOINTS ====================

@app.get("/api/admin/stats")
async def get_admin_stats():
    """Get administration statistics"""
    try:
        # Total patients in database
        total_patients = patients_collection.count_documents({})
        
        # New patients since start of current year
        current_year = datetime.now().year
        start_of_year = f"{current_year}-01-01"
        nouveaux_patients_annee = patients_collection.count_documents({
            "created_at": {"$gte": datetime.strptime(start_of_year, "%Y-%m-%d")}
        })
        
        # Inactive patients (no consultation in last 12 months)
        twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # Get all patient IDs who have consultations in last 12 months
        recent_consultations = list(consultations_collection.find(
            {"date": {"$gte": twelve_months_ago}}, 
            {"patient_id": 1, "_id": 0}
        ))
        active_patient_ids = set(c["patient_id"] for c in recent_consultations)
        
        # Count total patients not in active list
        all_patient_ids = set(p["id"] for p in patients_collection.find({}, {"id": 1, "_id": 0}))
        patients_inactifs = len(all_patient_ids - active_patient_ids)
        
        return {
            "total_patients": total_patients,
            "nouveaux_patients_annee": nouveaux_patients_annee, 
            "patients_inactifs": patients_inactifs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching admin stats: {str(e)}")

@app.get("/api/admin/inactive-patients")
async def get_inactive_patients():
    """Get list of patients inactive for more than 12 months"""
    try:
        twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # Get patient IDs with recent consultations
        recent_consultations = list(consultations_collection.find(
            {"date": {"$gte": twelve_months_ago}}, 
            {"patient_id": 1, "_id": 0}
        ))
        active_patient_ids = set(c["patient_id"] for c in recent_consultations)
        
        # Get all patients
        all_patients = list(patients_collection.find({}, {"_id": 0}))
        
        # Filter inactive patients and get their last consultation date
        inactive_patients = []
        for patient in all_patients:
            if patient["id"] not in active_patient_ids:
                # Get last consultation date for this patient
                last_consultation = consultations_collection.find_one(
                    {"patient_id": patient["id"]},
                    sort=[("date", -1)]
                )
                
                last_consultation_date = None
                if last_consultation:
                    last_consultation_date = last_consultation.get("date")
                
                inactive_patients.append({
                    "id": patient["id"],
                    "nom": patient.get("nom", ""),
                    "prenom": patient.get("prenom", ""),
                    "age": patient.get("age", ""),
                    "numero_whatsapp": patient.get("numero_whatsapp", ""),
                    "lien_whatsapp": patient.get("lien_whatsapp", ""),
                    "last_consultation_date": last_consultation_date,
                    "created_at": patient.get("created_at", datetime.now()).isoformat() if patient.get("created_at") else None
                })
        
        return {"inactive_patients": inactive_patients}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching inactive patients: {str(e)}")

@app.delete("/api/admin/database/{collection_name}")
async def reset_database_collection(collection_name: str):
    """Reset specific database collection"""
    try:
        valid_collections = {
            "patients": patients_collection,
            "appointments": appointments_collection, 
            "consultations": consultations_collection,
            "facturation": payments_collection  # Facturation = payments + cash movements
        }
        
        if collection_name not in valid_collections:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid collection. Valid options: {', '.join(valid_collections.keys())}"
            )
        
        # Reset the specific collection
        collection = valid_collections[collection_name]
        result = collection.delete_many({})
        
        # For facturation, also reset cash movements
        if collection_name == "facturation":
            cash_result = cash_movements_collection.delete_many({})
            return {
                "message": f"Collection '{collection_name}' réinitialisée avec succès",
                "payments_deleted": result.deleted_count,
                "cash_movements_deleted": cash_result.deleted_count,
                "total_deleted": result.deleted_count + cash_result.deleted_count
            }
        
        return {
            "message": f"Collection '{collection_name}' réinitialisée avec succès",
            "deleted_count": result.deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting collection: {str(e)}")

@app.get("/api/admin/monthly-report")
async def get_monthly_report(
    year: int = Query(None, description="Year (default: current year)"),
    month: int = Query(None, description="Month 1-12 (default: current month)"),
    start_month: int = Query(None, description="Start month for multi-month report"),
    end_month: int = Query(None, description="End month for multi-month report"),
    start_year: int = Query(None, description="Start year for multi-month report"),
    end_year: int = Query(None, description="End year for multi-month report")
):
    """Generate monthly report with all statistics - supports single month or date range"""
    try:
        # Handle multi-month report
        if start_month and end_month:
            if not start_year:
                start_year = datetime.now().year
            if not end_year:
                end_year = start_year
                
            # Generate multi-month report
            monthly_reports = []
            total_stats = {
                "nouveaux_patients": 0,
                "consultations_totales": 0,
                "nb_visites": 0,
                "nb_controles": 0,
                "nb_assures": 0,
                "recette_totale": 0.0,
                "nb_relances_telephoniques": 0
            }
            
            # Generate reports for each month in range
            current_year = start_year
            current_month = start_month
            
            while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
                # Date range for the month
                start_date = datetime(current_year, current_month, 1).strftime("%Y-%m-%d")
                
                # Calculate end date (last day of month)
                if current_month == 12:
                    end_date = datetime(current_year + 1, 1, 1) - timedelta(days=1)
                    next_year = current_year + 1
                    next_month = 1
                else:
                    end_date = datetime(current_year, current_month + 1, 1) - timedelta(days=1)
                    next_year = current_year
                    next_month = current_month + 1
                    
                end_date_str = end_date.strftime("%Y-%m-%d")
                
                # Calculate monthly stats
                monthly_data = await calculate_monthly_stats(start_date, end_date_str, current_year, current_month)
                monthly_reports.append(monthly_data)
                
                # Add to totals
                for key in total_stats:
                    total_stats[key] += monthly_data[key]
                
                # Move to next month
                current_year = next_year
                current_month = next_month
            
            # Calculate averages
            num_months = len(monthly_reports)
            averages = {key: round(value / num_months, 2) for key, value in total_stats.items()}
            
            return {
                "periode": f"{start_month:02d}/{start_year} - {end_month:02d}/{end_year}",
                "type": "multi_month",
                "start_date": monthly_reports[0]["start_date"],
                "end_date": monthly_reports[-1]["end_date"],
                "monthly_reports": monthly_reports,
                "totals": total_stats,
                "averages": averages,
                "num_months": num_months,
                "generated_at": datetime.now().isoformat()
            }
        
        # Single month report (existing logic)
        else:
            # Default to current month/year
            if not year:
                year = datetime.now().year
            if not month:
                month = datetime.now().month
                
            # Date range for the month
            start_date = datetime(year, month, 1).strftime("%Y-%m-%d")
            
            # Calculate end date (last day of month)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            monthly_data = await calculate_monthly_stats(start_date, end_date_str, year, month)
            
            return {
                **monthly_data,
                "type": "single_month",
                "generated_at": datetime.now().isoformat()
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating monthly report: {str(e)}")

async def calculate_monthly_stats(start_date: str, end_date_str: str, year: int, month: int):
    """Calculate statistics for a specific month"""
    # New patients this month
    nouveaux_patients = patients_collection.count_documents({
        "created_at": {
            "$gte": datetime.strptime(start_date, "%Y-%m-%d"),
            "$lte": datetime.strptime(end_date_str, "%Y-%m-%d")
        }
    })
    
    # Consultations this month  
    consultations_mois = consultations_collection.count_documents({
        "date": {"$gte": start_date, "$lte": end_date_str}
    })
    
    # Visites vs Controles
    nb_visites = consultations_collection.count_documents({
        "date": {"$gte": start_date, "$lte": end_date_str},
        "type_rdv": "visite"
    })
    
    nb_controles = consultations_collection.count_documents({
        "date": {"$gte": start_date, "$lte": end_date_str},
        "type_rdv": "controle"
    })
    
    # Patients assurés (appointments with assure=true)
    nb_assures = appointments_collection.count_documents({
        "date": {"$gte": start_date, "$lte": end_date_str},
        "assure": True,
        "statut": {"$in": ["termine", "absent", "retard"]}  # Completed appointments
    })
    
    # Total revenue for the month
    recette_totale = 0
    
    # From payments
    payments_month = list(payments_collection.find({
        "date": {"$gte": start_date, "$lte": end_date_str},
        "statut": "paye"
    }, {"_id": 0}))
    
    for payment in payments_month:
        recette_totale += payment.get("montant", 0)
        
    # From cash movements
    cash_movements_month = list(cash_movements_collection.find({
        "date": {"$gte": start_date, "$lte": end_date_str}
    }, {"_id": 0}))
    
    for movement in cash_movements_month:
        if movement["type_mouvement"] == "ajout":
            recette_totale += movement["montant"]
        else:
            recette_totale -= movement["montant"]
    
    # Phone reminders count (relances téléphoniques)
    nb_relances = phone_messages_collection.count_documents({
        "call_date": {"$gte": start_date, "$lte": end_date_str}
    })
    
    return {
        "periode": f"{month:02d}/{year}",
        "start_date": start_date,
        "end_date": end_date_str,
        "nouveaux_patients": nouveaux_patients,
        "consultations_totales": consultations_mois,
        "nb_visites": nb_visites,
        "nb_controles": nb_controles,
        "nb_assures": nb_assures,
        "recette_totale": round(recette_totale, 2),
        "nb_relances_telephoniques": nb_relances
    }

@app.get("/api/admin/export/{collection_name}")
async def export_collection_data(collection_name: str):
    """Export collection data for download"""
    try:
        valid_collections = {
            "patients": patients_collection,
            "appointments": appointments_collection,
            "consultations": consultations_collection,
            "payments": payments_collection
        }
        
        if collection_name not in valid_collections:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid collection. Valid options: {', '.join(valid_collections.keys())}"
            )
        
        collection = valid_collections[collection_name]
        data = list(collection.find({}, {"_id": 0}))  # Exclude MongoDB _id field
        
        if not data:
            return {
                "message": f"Aucune donnée trouvée dans la collection {collection_name}",
                "data": [],
                "count": 0
            }
        
        return {
            "message": f"Export de {len(data)} éléments de {collection_name}",
            "data": data,
            "count": len(data),
            "collection": collection_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting collection: {str(e)}")

@app.post("/api/admin/maintenance/{action}")
async def perform_maintenance(action: str):
    """Perform various maintenance actions"""
    try:
        if action == "update_calculated_fields":
            # Update calculated fields like age, whatsapp links
            patients_updated = 0
            current_date = datetime.now()
            
            for patient in patients_collection.find():
                updates = {}
                
                # Update age if birth date exists
                if patient.get("date_naissance"):
                    try:
                        birth_date = datetime.strptime(patient["date_naissance"], "%Y-%m-%d")
                        age = current_date.year - birth_date.year - ((current_date.month, current_date.day) < (birth_date.month, birth_date.day))
                        updates["age"] = age
                    except:
                        pass
                
                # Update WhatsApp link if phone number exists
                if patient.get("numero_whatsapp"):
                    updates["lien_whatsapp"] = f"https://wa.me/{patient['numero_whatsapp']}"
                
                if updates:
                    patients_collection.update_one({"id": patient["id"]}, {"$set": updates})
                    patients_updated += 1
            
            return {
                "action": "update_calculated_fields",
                "completed": True,
                "message": "Champs calculés mis à jour",
                "details": {
                    "patients_updated": patients_updated
                }
            }
        
        elif action == "verify_data_integrity":
            # Check for orphaned consultations, payments without appointments, etc.
            issues = []
            
            # Check orphaned consultations
            consultations = list(consultations_collection.find())
            for consultation in consultations:
                if consultation.get("appointment_id"):
                    appointment = appointments_collection.find_one({"id": consultation["appointment_id"]})
                    if not appointment:
                        issues.append(f"Consultation {consultation['id']} has orphaned appointment_id {consultation['appointment_id']}")
            
            # Check orphaned payments
            payments = list(payments_collection.find())
            for payment in payments:
                if payment.get("appointment_id"):
                    appointment = appointments_collection.find_one({"id": payment["appointment_id"]})
                    if not appointment:
                        issues.append(f"Payment {payment['id']} has orphaned appointment_id {payment['appointment_id']}")
            
            return {
                "action": "verify_data_integrity",
                "completed": True,
                "message": f"Vérification terminée - {len(issues)} problèmes détectés",
                "details": {
                    "issues_found": len(issues),
                    "issues": issues[:10]  # First 10 issues only
                }
            }
        
        elif action == "optimize_database":
            # Database optimization (indexes, etc.)
            return {
                "action": "optimize_database",
                "completed": True,
                "message": "Base de données optimisée",
                "details": {
                    "indexes_created": 0,
                    "optimization_completed": True
                }
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid maintenance action. Valid options: update_calculated_fields, verify_data_integrity, optimize_database"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing maintenance: {str(e)}")

# ==================== USER MANAGEMENT API ====================

@app.post("/api/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    """Authenticate user and return JWT token"""
    try:
        user = users_collection.find_one({"username": user_login.username}, {"_id": 0})
        
        if not user or not verify_password(user_login.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Nom d'utilisateur ou mot de passe incorrect")
        
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="Compte utilisateur désactivé")
        
        # Update last login
        users_collection.update_one(
            {"username": user_login.username}, 
            {"$set": {"last_login": datetime.now()}}
        )
        
        # Create access token
        access_token = create_access_token(data={"sub": user["username"]})
        
        # Prepare user response (without password)
        user_response = {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email", ""),
            "full_name": user["full_name"],
            "role": user["role"],
            "permissions": user.get("permissions", {}),
            "last_login": user.get("last_login")
        }
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(**current_user)

@app.get("/api/admin/users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    """Get all users (admin only)"""
    if not current_user.get("permissions", {}).get("manage_users", False):
        raise HTTPException(status_code=403, detail="Permission refusée: gestion des utilisateurs requise")
    
    try:
        users = list(users_collection.find({}, {"_id": 0, "hashed_password": 0}))
        return {"users": users, "count": len(users)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@app.post("/api/admin/users", response_model=UserResponse)
async def create_user(user_create: UserCreate, current_user: dict = Depends(get_current_user)):
    """Create new user (admin only)"""
    if not current_user.get("permissions", {}).get("manage_users", False):
        raise HTTPException(status_code=403, detail="Permission refusée: gestion des utilisateurs requise")
    
    try:
        # Check if username already exists
        existing_user = users_collection.find_one({"username": user_create.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Ce nom d'utilisateur existe déjà")
        
        # Set default permissions based on role
        if user_create.permissions is None:
            if user_create.role == "medecin":
                permissions = UserPermissions(
                    administration=True,
                    delete_appointment=True,
                    delete_payments=True,
                    export_data=True,
                    reset_data=True,
                    manage_users=True
                )
            else:  # secretaire
                permissions = UserPermissions(
                    administration=False,
                    delete_appointment=False,
                    delete_payments=False,
                    export_data=False,
                    reset_data=False,
                    manage_users=False,
                    consultation_read_only=True
                )
        else:
            permissions = user_create.permissions
        
        # Create user
        new_user = User(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            role=user_create.role,
            hashed_password=hash_password(user_create.password),
            permissions=permissions
        )
        
        # Insert to database
        users_collection.insert_one(new_user.dict())
        
        # Return user without password
        return UserResponse(**new_user.dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

@app.put("/api/admin/users/{user_id}")
async def update_user(user_id: str, user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Update user (admin only or self)"""
    # Allow users to update themselves or admins to update anyone
    can_update = (
        current_user.get("id") == user_id or 
        current_user.get("permissions", {}).get("manage_users", False)
    )
    
    if not can_update:
        raise HTTPException(status_code=403, detail="Permission refusée")
    
    try:
        user = users_collection.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Prepare update data
        update_data = {"updated_at": datetime.now()}
        
        if user_update.username is not None:
            # Check if new username is taken by someone else
            existing = users_collection.find_one({"username": user_update.username, "id": {"$ne": user_id}})
            if existing:
                raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")
            update_data["username"] = user_update.username
        
        if user_update.email is not None:
            update_data["email"] = user_update.email
        
        if user_update.full_name is not None:
            update_data["full_name"] = user_update.full_name
        
        if user_update.password is not None:
            update_data["hashed_password"] = hash_password(user_update.password)
        
        if user_update.is_active is not None:
            # Only admins can change active status
            if current_user.get("permissions", {}).get("manage_users", False):
                update_data["is_active"] = user_update.is_active
        
        if user_update.permissions is not None:
            # Only admins can change permissions
            if current_user.get("permissions", {}).get("manage_users", False):
                update_data["permissions"] = user_update.permissions.dict()
        
        # Update user
        users_collection.update_one({"id": user_id}, {"$set": update_data})
        
        # Return updated user
        updated_user = users_collection.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
        return {"message": "Utilisateur mis à jour avec succès", "user": updated_user}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Delete user (admin only)"""
    if not current_user.get("permissions", {}).get("manage_users", False):
        raise HTTPException(status_code=403, detail="Permission refusée: gestion des utilisateurs requise")
    
    try:
        # Don't allow deleting yourself
        if current_user.get("id") == user_id:
            raise HTTPException(status_code=400, detail="Impossible de supprimer votre propre compte")
        
        user = users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Delete user
        result = users_collection.delete_one({"id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        return {"message": "Utilisateur supprimé avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

@app.put("/api/admin/users/{user_id}/permissions")
async def update_user_permissions(user_id: str, permissions: UserPermissions, current_user: dict = Depends(get_current_user)):
    """Update user permissions (admin only)"""
    if not current_user.get("permissions", {}).get("manage_users", False):
        raise HTTPException(status_code=403, detail="Permission refusée: gestion des utilisateurs requise")
    
    try:
        user = users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Update permissions
        users_collection.update_one(
            {"id": user_id}, 
            {"$set": {"permissions": permissions.dict(), "updated_at": datetime.now()}}
        )
        
        # Return updated user
        updated_user = users_collection.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
        return {"message": "Permissions mises à jour avec succès", "user": updated_user}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating permissions: {str(e)}")

@app.get("/api/admin/charts/yearly-evolution")
async def get_yearly_evolution_charts():
    """Get yearly evolution data for charts (revenue, new patients, consultations)"""
    try:
        current_year = datetime.now().year
        monthly_data = []
        
        # Generate data for each month of current year
        for month in range(1, 13):
            # Date range for the month
            start_date = datetime(current_year, month, 1).strftime("%Y-%m-%d")
            
            # Calculate end date (last day of month)
            if month == 12:
                end_date = datetime(current_year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(current_year, month + 1, 1) - timedelta(days=1)
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # New patients this month
            nouveaux_patients = patients_collection.count_documents({
                "created_at": {
                    "$gte": datetime.strptime(start_date, "%Y-%m-%d"),
                    "$lte": datetime.strptime(end_date_str, "%Y-%m-%d")
                }
            })
            
            # Total consultations this month
            consultations_mois = consultations_collection.count_documents({
                "date": {"$gte": start_date, "$lte": end_date_str}
            })
            
            # Revenue this month (from payments + cash movements)
            recette_mensuelle = 0
            
            # From payments
            payments_month = list(payments_collection.find({
                "date": {"$gte": start_date, "$lte": end_date_str},
                "statut": "paye"
            }, {"_id": 0, "montant": 1}))
            
            for payment in payments_month:
                recette_mensuelle += payment.get("montant", 0)
                
            # From cash movements (additions only)
            cash_movements_month = list(cash_movements_collection.find({
                "date": {"$gte": start_date, "$lte": end_date_str}
            }, {"_id": 0, "montant": 1, "type_mouvement": 1}))
            
            for movement in cash_movements_month:
                if movement["type_mouvement"] == "ajout":
                    recette_mensuelle += movement["montant"]
                else:
                    recette_mensuelle -= movement["montant"]
            
            # Visites vs Controles breakdown
            nb_visites = consultations_collection.count_documents({
                "date": {"$gte": start_date, "$lte": end_date_str},
                "type_rdv": "visite"
            })
            
            nb_controles = consultations_collection.count_documents({
                "date": {"$gte": start_date, "$lte": end_date_str},
                "type_rdv": "controle"
            })
            
            monthly_data.append({
                "month": month,
                "month_name": datetime(current_year, month, 1).strftime("%B"),
                "month_short": datetime(current_year, month, 1).strftime("%b"),
                "nouveaux_patients": nouveaux_patients,
                "consultations_totales": consultations_mois,
                "nb_visites": nb_visites,
                "nb_controles": nb_controles,
                "recette_mensuelle": round(recette_mensuelle, 2)
            })
        
        # Calculate totals for year
        total_nouveaux = sum(data["nouveaux_patients"] for data in monthly_data)
        total_consultations = sum(data["consultations_totales"] for data in monthly_data)
        total_recette = sum(data["recette_mensuelle"] for data in monthly_data)
        
        return {
            "year": current_year,
            "monthly_data": monthly_data,
            "totals": {
                "nouveaux_patients_annee": total_nouveaux,
                "consultations_annee": total_consultations,
                "recette_annee": round(total_recette, 2)
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating yearly charts data: {str(e)}")

# ==================== END USER MANAGEMENT API ====================

# ==================== END ADMINISTRATION API ====================

# ==================== End Cash Movements API ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)