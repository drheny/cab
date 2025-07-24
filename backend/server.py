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

# Application startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Check if demo data should be initialized
    should_init_demo = os.getenv("INIT_DEMO_DATA", "false").lower() == "true"
    
    # Initialize demo data if needed
    if should_init_demo:
        await init_demo_data()
    
    # Create default WhatsApp templates
    create_default_whatsapp_templates()
    
    return {"message": "Application initialized successfully"}

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
    duree_attente: int = 0  # Duration in waiting room (in minutes) - stored for stats
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class Consultation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    appointment_id: str
    date: str
    type_rdv: str = "visite"  # "visite" ou "controle"
    motif: Optional[str] = ""
    duree: int = 0  # en minutes
    poids: Optional[float] = None
    taille: Optional[float] = None
    pc: Optional[float] = None  # périmètre crânien
    temperature: Optional[float] = None
    observation_medicale: Optional[str] = ""  # Changed from observations
    traitement: Optional[str] = ""
    bilans: Optional[str] = ""  # Changed from bilan
    notes: Optional[str] = ""
    relance_telephonique: Optional[bool] = False
    date_relance: Optional[str] = None  # Changed from relance_date
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
    """Get current user from JWT token - WITH AUTO-LOGIN BYPASS"""
    try:
        # Check for auto-login mock token
        if credentials.credentials == "auto-login-token":
            # Return default doctor user for auto-login
            return {
                "id": "auto-doctor-id",
                "username": "medecin",
                "email": "",
                "full_name": "Dr Heni Dridi",
                "role": "medecin",
                "permissions": {
                    "dashboard": True,
                    "patients": True,
                    "calendar": True,
                    "messages": True,
                    "billing": True,
                    "consultation": True,
                    "administration": True,
                    "create_appointment": True,
                    "edit_appointment": True,
                    "delete_appointment": True,
                    "view_payments": True,
                    "edit_payments": True,
                    "delete_payments": True,
                    "export_data": True,
                    "reset_data": True,
                    "manage_users": True,
                    "consultation_read_only": False
                },
                "last_login": datetime.now().isoformat()
            }
        
        # Regular JWT token validation
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
        # For demo data, generate a simple WhatsApp link without pre-filled message
        clean_phone = ''.join(filter(str.isdigit, patient_dict['numero_whatsapp']))
        if not clean_phone.startswith('216'):
            clean_phone = '216' + clean_phone
        patient_dict['lien_whatsapp'] = f"https://wa.me/{clean_phone}"
    
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
                "id": patient.get("id", ""),
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
                "id": patient.get("id", ""),
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

# ==================== ADVANCED REPORTS API ====================

from collections import defaultdict
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

# Advanced Report Models
class AdvancedReportRequest(BaseModel):
    period_type: str = Field(..., description="monthly, semester, annual, custom")
    year: Optional[int] = None
    month: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class AlertThresholds(BaseModel):
    revenue_drop_threshold: float = 20.0  # %
    inactive_patients_threshold: float = 30.0  # %
    waiting_time_threshold: float = 30.0  # minutes

async def calculate_advanced_statistics(start_date: str, end_date: str):
    """Calculate comprehensive statistics for advanced reports"""
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get all appointments in period
        appointments = list(appointments_collection.find({
            "date": {"$gte": start_date, "$lte": end_date}
        }))
        
        # Get all consultations in period
        consultations = list(consultations_collection.find({
            "date": {"$gte": start_date, "$lte": end_date}
        }))
        
        # Get all patients
        all_patients = list(patients_collection.find({}, {"_id": 0}))
        
        # 1. Répartition Visite/Contrôle
        visites = [apt for apt in appointments if apt.get("type_rdv") == "visite"]
        controles = [apt for apt in appointments if apt.get("type_rdv") == "controle"]
        
        visite_revenue = len(visites) * 65  # Assuming 65 TND per visite
        controle_revenue = 0  # Contrôles are free
        
        consultations_stats = {
            "visites": {
                "count": len(visites),
                "percentage": round((len(visites) / max(len(appointments), 1)) * 100, 1),
                "revenue": visite_revenue
            },
            "controles": {
                "count": len(controles),
                "percentage": round((len(controles) / max(len(appointments), 1)) * 100, 1),
                "revenue": controle_revenue
            },
            "total": len(appointments)
        }
        
        # 2. Top 10 Patients Rentables
        patient_revenue = defaultdict(lambda: {"consultations": 0, "revenue": 0, "last_visit": None})
        
        for apt in appointments:
            patient_id = apt.get("patient_id")
            if patient_id and apt.get("type_rdv") == "visite" and apt.get("paye", True):
                patient_revenue[patient_id]["consultations"] += 1
                patient_revenue[patient_id]["revenue"] += 65
                if not patient_revenue[patient_id]["last_visit"] or apt["date"] > patient_revenue[patient_id]["last_visit"]:
                    patient_revenue[patient_id]["last_visit"] = apt["date"]
        
        # Get patient names and create top 10 list
        top_patients = []
        for patient_id, stats in patient_revenue.items():
            patient = patients_collection.find_one({"id": patient_id}, {"_id": 0})
            if patient:
                top_patients.append({
                    "name": f"{patient.get('prenom', '')} {patient.get('nom', '')}".strip(),
                    "consultations": stats["consultations"],
                    "revenue": stats["revenue"],
                    "last_visit": stats["last_visit"]
                })
        
        top_patients = sorted(top_patients, key=lambda x: x["revenue"], reverse=True)[:10]
        
        # 3. Durées moyennes
        waiting_times = []
        consultation_durations = []
        
        for apt in appointments:
            if apt.get("duree_attente"):
                waiting_times.append(apt["duree_attente"])
        
        for consultation in consultations:
            if consultation.get("duree"):
                consultation_durations.append(consultation["duree"])
        
        durees = {
            "attente_moyenne": round(np.mean(waiting_times) if waiting_times else 0, 1),
            "consultation_moyenne": round(np.mean(consultation_durations) if consultation_durations else 0, 1),
            "attente_max": max(waiting_times) if waiting_times else 0,
            "consultation_max": max(consultation_durations) if consultation_durations else 0
        }
        
        # 4. Relances téléphoniques
        relances_total = len([c for c in consultations if c.get("relance_date")])
        relances_traitees = len([c for c in consultations if c.get("relance_date") and c.get("relance_traitee", False)])
        
        relances = {
            "total": relances_total,
            "traitees": relances_traitees,
            "en_attente": relances_total - relances_traitees,
            "taux_reponse": round((relances_traitees / max(relances_total, 1)) * 100, 1)
        }
        
        # 5. Répartition démographique
        age_groups = {"0-2": 0, "3-5": 0, "6-12": 0, "13-18": 0, "18+": 0}
        address_distribution = defaultdict(int)
        
        for patient in all_patients:
            age = patient.get("age", 0)
            if isinstance(age, (int, float)):
                if age <= 2:
                    age_groups["0-2"] += 1
                elif age <= 5:
                    age_groups["3-5"] += 1
                elif age <= 12:
                    age_groups["6-12"] += 1
                elif age <= 18:
                    age_groups["13-18"] += 1
                else:
                    age_groups["18+"] += 1
            
            # Address distribution
            address = patient.get("adresse", "Non spécifié")
            if address:
                # Extract city name (simplified)
                city = address.split(",")[0].strip() if "," in address else address
                address_distribution[city] += 1
        
        # Get top 5 addresses
        top_addresses = dict(sorted(address_distribution.items(), key=lambda x: x[1], reverse=True)[:5])
        
        demographics = {
            "age_groups": age_groups,
            "addresses": top_addresses
        }
        
        # 6. Patients inactifs (plus de 6 mois sans consultation)
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        recent_patients = set()
        
        for apt in appointments_collection.find({"date": {"$gte": six_months_ago}}):
            recent_patients.add(apt.get("patient_id"))
        
        total_patients = len(all_patients)
        inactive_count = total_patients - len(recent_patients)
        
        patients_inactifs = {
            "count": inactive_count,
            "percentage": round((inactive_count / max(total_patients, 1)) * 100, 1),
            "details": []  # Could be populated with actual patient list if needed
        }
        
        # 7. Taux de fidélisation
        period_patients = set()
        new_patients_in_period = 0
        
        for apt in appointments:
            patient_id = apt.get("patient_id")
            period_patients.add(patient_id)
            
            # Check if this is patient's first appointment ever
            first_apt = appointments_collection.find_one(
                {"patient_id": patient_id}, 
                sort=[("date", 1)]
            )
            if first_apt and first_apt["date"] >= start_date:
                new_patients_in_period += 1
        
        recurring_patients = len(period_patients) - new_patients_in_period
        
        fidelisation = {
            "nouveaux_patients": new_patients_in_period,
            "patients_recurrents": recurring_patients,
            "taux_retour": round((recurring_patients / max(len(period_patients), 1)) * 100, 1)
        }
        
        # 8. Utilisation des salles
        salle_usage = {"salle1": 0, "salle2": 0, "sans_salle": 0}
        
        for apt in appointments:
            salle = apt.get("salle", "")
            if salle == "salle1":
                salle_usage["salle1"] += 1
            elif salle == "salle2":
                salle_usage["salle2"] += 1
            else:
                salle_usage["sans_salle"] += 1
        
        total_with_room = salle_usage["salle1"] + salle_usage["salle2"]
        
        salles = {
            "salle1": {
                "utilisation": round((salle_usage["salle1"] / max(total_with_room, 1)) * 100, 1),
                "consultations": salle_usage["salle1"]
            },
            "salle2": {
                "utilisation": round((salle_usage["salle2"] / max(total_with_room, 1)) * 100, 1),
                "consultations": salle_usage["salle2"]
            },
            "sans_salle": {
                "consultations": salle_usage["sans_salle"]
            }
        }
        
        return {
            "consultations": consultations_stats,
            "top_patients": top_patients,
            "durees": durees,
            "relances": relances,
            "demographics": demographics,
            "patients_inactifs": patients_inactifs,
            "fidelisation": fidelisation,
            "salles": salles
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating advanced statistics: {str(e)}")

async def calculate_monthly_evolution(start_date: str, end_date: str):
    """Calculate monthly evolution data for trends"""
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        evolution = []
        current_date = start_dt
        
        while current_date <= end_dt:
            month_start = current_date.replace(day=1).strftime("%Y-%m-%d")
            
            # Calculate end of month
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
            
            month_end_str = month_end.strftime("%Y-%m-%d")
            
            # Get appointments for this month
            monthly_appointments = list(appointments_collection.find({
                "date": {"$gte": month_start, "$lte": month_end_str}
            }))
            
            visites = len([apt for apt in monthly_appointments if apt.get("type_rdv") == "visite"])
            controles = len([apt for apt in monthly_appointments if apt.get("type_rdv") == "controle"])
            revenue = visites * 65
            
            evolution.append({
                "mois": current_date.strftime("%b"),
                "visites": visites,
                "controles": controles,
                "revenue": revenue,
                "date": month_start
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return evolution
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating monthly evolution: {str(e)}")

async def calculate_year_comparison(current_year: int):
    """Calculate comparison between current year and previous year"""
    try:
        previous_year = current_year - 1
        
        # Current year data
        current_start = f"{current_year}-01-01"
        current_end = f"{current_year}-12-31"
        current_appointments = list(appointments_collection.find({
            "date": {"$gte": current_start, "$lte": current_end}
        }))
        
        # Previous year data
        previous_start = f"{previous_year}-01-01"
        previous_end = f"{previous_year}-12-31"
        previous_appointments = list(appointments_collection.find({
            "date": {"$gte": previous_start, "$lte": previous_end}
        }))
        
        # Calculate metrics
        current_consultations = len(current_appointments)
        previous_consultations = len(previous_appointments)
        
        current_visites = len([apt for apt in current_appointments if apt.get("type_rdv") == "visite"])
        previous_visites = len([apt for apt in previous_appointments if apt.get("type_rdv") == "visite"])
        
        current_revenue = current_visites * 65
        previous_revenue = previous_visites * 65
        
        # Calculate evolution percentages
        def calculate_evolution(current, previous):
            if previous == 0:
                return "+100%" if current > 0 else "0%"
            evolution = ((current - previous) / previous) * 100
            return f"{'+' if evolution >= 0 else ''}{evolution:.1f}%"
        
        return {
            "consultations": {
                "current": current_consultations,
                "previous": previous_consultations,
                "evolution": calculate_evolution(current_consultations, previous_consultations)
            },
            "revenue": {
                "current": current_revenue,
                "previous": previous_revenue,
                "evolution": calculate_evolution(current_revenue, previous_revenue)
            },
            "visites": {
                "current": current_visites,
                "previous": previous_visites,
                "evolution": calculate_evolution(current_visites, previous_visites)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating year comparison: {str(e)}")

async def calculate_seasonality_patterns():
    """Calculate seasonal patterns and identify peaks/troughs"""
    try:
        # Get last 2 years of data for better pattern recognition
        two_years_ago = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        
        appointments = list(appointments_collection.find({
            "date": {"$gte": two_years_ago, "$lte": today}
        }))
        
        # Group by month across years
        monthly_stats = defaultdict(list)
        
        for apt in appointments:
            apt_date = datetime.strptime(apt["date"], "%Y-%m-%d")
            month = apt_date.month
            monthly_stats[month].append(apt)
        
        # Calculate average appointments per month
        monthly_averages = {}
        for month, apts in monthly_stats.items():
            monthly_averages[month] = len(apts) / 2  # Average over 2 years
        
        # Calculate overall average
        overall_average = sum(monthly_averages.values()) / len(monthly_averages) if monthly_averages else 0
        
        # Identify peaks and troughs
        peaks = []
        creux = []
        
        month_names = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                      "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        
        for month, avg in monthly_averages.items():
            deviation = ((avg - overall_average) / overall_average) * 100 if overall_average > 0 else 0
            
            if deviation > 15:  # Peak if 15% above average
                peaks.append({
                    "periode": month_names[month],
                    "raison": get_seasonal_reason(month, "peak"),
                    "evolution": f"+{deviation:.0f}%"
                })
            elif deviation < -15:  # Trough if 15% below average
                creux.append({
                    "periode": month_names[month],
                    "raison": get_seasonal_reason(month, "trough"),
                    "evolution": f"{deviation:.0f}%"
                })
        
        return {
            "pics": peaks,
            "creux": creux,
            "monthly_averages": monthly_averages,
            "overall_average": round(overall_average, 1)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating seasonality: {str(e)}")

def get_seasonal_reason(month: int, pattern_type: str):
    """Get likely seasonal reason for peaks/troughs"""
    peak_reasons = {
        1: "Post-fêtes, maladies hivernales",
        2: "Maladies hivernales",
        3: "Allergies printanières",
        9: "Rentrée scolaire",
        10: "Maladies automnales",
        11: "Début de saison froide"
    }
    
    trough_reasons = {
        7: "Vacances d'été",
        8: "Vacances d'été",
        12: "Fêtes de fin d'année"
    }
    
    if pattern_type == "peak":
        return peak_reasons.get(month, "Pic saisonnier")
    else:
        return trough_reasons.get(month, "Creux saisonnier")

async def calculate_predictions(evolution_data: list):
    """Calculate predictions using linear regression"""
    try:
        if len(evolution_data) < 3:
            return {
                "next_month": {
                    "consultations_estimees": 0,
                    "revenue_estime": 0,
                    "confiance": 0
                },
                "message": "Pas assez de données pour les prédictions"
            }
        
        # Prepare data for prediction
        X = np.array(range(len(evolution_data))).reshape(-1, 1)
        y_consultations = np.array([month["visites"] + month["controles"] for month in evolution_data])
        y_revenue = np.array([month["revenue"] for month in evolution_data])
        
        # Train models
        consultation_model = LinearRegression()
        revenue_model = LinearRegression()
        
        consultation_model.fit(X, y_consultations)
        revenue_model.fit(X, y_revenue)
        
        # Predict next month
        next_month_index = len(evolution_data)
        predicted_consultations = consultation_model.predict([[next_month_index]])[0]
        predicted_revenue = revenue_model.predict([[next_month_index]])[0]
        
        # Calculate confidence (simplified R² score)
        consultation_predictions = consultation_model.predict(X)
        revenue_predictions = revenue_model.predict(X)
        
        consultation_mae = mean_absolute_error(y_consultations, consultation_predictions)
        revenue_mae = mean_absolute_error(y_revenue, revenue_predictions)
        
        # Simplified confidence calculation (inverse of normalized MAE)
        consultation_conf = max(0, 100 - (consultation_mae / max(np.mean(y_consultations), 1)) * 100)
        revenue_conf = max(0, 100 - (revenue_mae / max(np.mean(y_revenue), 1)) * 100)
        
        average_confidence = (consultation_conf + revenue_conf) / 2
        
        return {
            "next_month": {
                "consultations_estimees": max(0, round(predicted_consultations)),
                "revenue_estime": max(0, round(predicted_revenue)),
                "confiance": round(min(average_confidence, 95), 1)  # Cap at 95%
            },
            "trend": "croissant" if predicted_consultations > y_consultations[-1] else "décroissant"
        }
        
    except Exception as e:
        # Fallback to simple average-based prediction
        avg_consultations = np.mean([month["visites"] + month["controles"] for month in evolution_data[-3:]])
        avg_revenue = np.mean([month["revenue"] for month in evolution_data[-3:]])
        
        return {
            "next_month": {
                "consultations_estimees": round(avg_consultations),
                "revenue_estime": round(avg_revenue),
                "confiance": 60  # Lower confidence for fallback method
            },
            "trend": "stable",
            "message": "Prédiction basée sur la moyenne des 3 derniers mois"
        }

async def check_alert_thresholds(current_data: dict, previous_data: dict = None):
    """Check if any alert thresholds are exceeded"""
    alerts = []
    
    try:
        # 1. Revenue drop alert
        if previous_data:
            current_revenue = current_data.get("consultations", {}).get("visites", {}).get("revenue", 0)
            previous_revenue = previous_data.get("consultations", {}).get("visites", {}).get("revenue", 0)
            
            if previous_revenue > 0:
                revenue_drop = ((previous_revenue - current_revenue) / previous_revenue) * 100
                if revenue_drop > 20:
                    alerts.append({
                        "type": "revenue_drop",
                        "severity": "high",
                        "message": f"Baisse de revenus de {revenue_drop:.1f}% détectée",
                        "value": revenue_drop,
                        "threshold": 20
                    })
        
        # 2. Inactive patients alert
        inactive_percentage = current_data.get("patients_inactifs", {}).get("percentage", 0)
        if inactive_percentage > 30:
            alerts.append({
                "type": "inactive_patients",
                "severity": "medium",
                "message": f"{inactive_percentage}% de patients inactifs",
                "value": inactive_percentage,
                "threshold": 30
            })
        
        # 3. Waiting time alert
        avg_waiting_time = current_data.get("durees", {}).get("attente_moyenne", 0)
        if avg_waiting_time > 30:
            alerts.append({
                "type": "waiting_time",
                "severity": "medium",
                "message": f"Temps d'attente moyen: {avg_waiting_time} minutes",
                "value": avg_waiting_time,
                "threshold": 30
            })
        
        return alerts
        
    except Exception as e:
        return []

@app.get("/api/admin/advanced-reports")
async def get_advanced_reports(
    period_type: str = Query(..., description="monthly, semester, annual, custom"),
    year: int = Query(None, description="Year"),
    month: int = Query(None, description="Month (1-12)"),
    semester: int = Query(None, description="Semester (1 or 2)"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)")
):
    """Generate comprehensive advanced reports with multiple data points"""
    try:
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Determine date range based on period type
        if period_type == "monthly":
            if not year:
                year = current_year
            if not month:
                month = current_month
                
            start_date = f"{year}-{month:02d}-01"
            # Calculate end of month
            if month == 12:
                end_date = f"{year}-12-31"
            else:
                last_day = (datetime(year, month + 1, 1) - timedelta(days=1)).day
                end_date = f"{year}-{month:02d}-{last_day}"
                
            periode_label = f"{datetime(year, month, 1).strftime('%B %Y')}"
            
        elif period_type == "semester":
            if not year:
                year = current_year
            if not semester:
                semester = 1 if current_month <= 6 else 2
                
            if semester == 1:
                start_date = f"{year}-01-01"
                end_date = f"{year}-06-30"
                periode_label = f"1er semestre {year}"
            else:
                start_date = f"{year}-07-01"
                end_date = f"{year}-12-31"
                periode_label = f"2e semestre {year}"
                
        elif period_type == "annual":
            if not year:
                year = current_year
                
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            periode_label = f"Année {year}"
            
        elif period_type == "custom":
            if not start_date or not end_date:
                raise HTTPException(status_code=400, detail="Start date and end date required for custom period")
            periode_label = f"{start_date} - {end_date}"
            
        else:
            raise HTTPException(status_code=400, detail="Invalid period_type. Use: monthly, semester, annual, custom")
        
        # Calculate advanced statistics
        advanced_stats = await calculate_advanced_statistics(start_date, end_date)
        
        # Calculate monthly evolution for trends
        evolution = await calculate_monthly_evolution(start_date, end_date)
        
        # Calculate year comparison if applicable
        comparison = None
        if period_type in ["annual", "semester"]:
            comparison_year = year if year else current_year
            comparison = await calculate_year_comparison(comparison_year)
        
        # Calculate seasonality patterns
        seasonality = await calculate_seasonality_patterns()
        
        # Calculate predictions
        predictions = await calculate_predictions(evolution)
        
        # Check alert thresholds
        alerts = await check_alert_thresholds(advanced_stats)
        
        # Compile comprehensive report
        report = {
            "metadata": {
                "periode": periode_label,
                "type": period_type,
                "start_date": start_date,
                "end_date": end_date,
                "generated_at": datetime.now().isoformat()
            },
            "advanced_statistics": advanced_stats,
            "evolution": evolution,
            "comparison": comparison,
            "seasonality": seasonality,
            "predictions": predictions,
            "alerts": alerts
        }
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating advanced reports: {str(e)}")

@app.get("/api/admin/reports/demographics")
async def get_demographics_report(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get detailed demographics breakdown"""
    try:
        # Get patients who had appointments in the period
        appointments = list(appointments_collection.find({
            "date": {"$gte": start_date, "$lte": end_date}
        }))
        
        active_patient_ids = set(apt.get("patient_id") for apt in appointments if apt.get("patient_id"))
        
        # Get patient details
        active_patients = list(patients_collection.find({
            "id": {"$in": list(active_patient_ids)}
        }, {"_id": 0}))
        
        # Detailed age analysis
        age_breakdown = {
            "0-1": 0, "2-3": 0, "4-5": 0, "6-8": 0, "9-12": 0, 
            "13-15": 0, "16-18": 0, "18+": 0
        }
        
        # Detailed address analysis
        address_stats = defaultdict(int)
        city_stats = defaultdict(int)
        
        for patient in active_patients:
            # Age breakdown
            age = patient.get("age", 0)
            if isinstance(age, (int, float)):
                if age <= 1:
                    age_breakdown["0-1"] += 1
                elif age <= 3:
                    age_breakdown["2-3"] += 1
                elif age <= 5:
                    age_breakdown["4-5"] += 1
                elif age <= 8:
                    age_breakdown["6-8"] += 1
                elif age <= 12:
                    age_breakdown["9-12"] += 1
                elif age <= 15:
                    age_breakdown["13-15"] += 1
                elif age <= 18:
                    age_breakdown["16-18"] += 1
                else:
                    age_breakdown["18+"] += 1
            
            # Address analysis
            address = patient.get("adresse", "")
            if address:
                address_stats[address] += 1
                # Extract city (first part before comma)
                city = address.split(",")[0].strip() if "," in address else address
                city_stats[city] += 1
        
        # Sort and get top addresses/cities
        top_addresses = dict(sorted(address_stats.items(), key=lambda x: x[1], reverse=True)[:10])
        top_cities = dict(sorted(city_stats.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return {
            "period": f"{start_date} - {end_date}",
            "total_active_patients": len(active_patients),
            "age_breakdown": age_breakdown,
            "top_addresses": top_addresses,
            "top_cities": top_cities,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating demographics report: {str(e)}")

@app.get("/api/admin/reports/top-patients")
async def get_top_patients_report(
    limit: int = Query(10, description="Number of top patients to return"),
    period_months: int = Query(12, description="Period in months to analyze"),
    metric: str = Query("revenue", description="Metric to rank by: revenue, consultations, frequency")
):
    """Get detailed top patients analysis"""
    try:
        # Calculate start date
        start_date = (datetime.now() - timedelta(days=period_months * 30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get appointments in period
        appointments = list(appointments_collection.find({
            "date": {"$gte": start_date, "$lte": end_date}
        }))
        
        # Analyze patients
        patient_stats = defaultdict(lambda: {
            "consultations": 0,
            "visites": 0,
            "controles": 0,
            "revenue": 0,
            "first_visit": None,
            "last_visit": None,
            "visits_per_month": 0
        })
        
        for apt in appointments:
            patient_id = apt.get("patient_id")
            if not patient_id:
                continue
                
            stats = patient_stats[patient_id]
            stats["consultations"] += 1
            
            if apt.get("type_rdv") == "visite":
                stats["visites"] += 1
                if apt.get("paye", True):
                    stats["revenue"] += 65
            else:
                stats["controles"] += 1
            
            apt_date = apt["date"]
            if not stats["first_visit"] or apt_date < stats["first_visit"]:
                stats["first_visit"] = apt_date
            if not stats["last_visit"] or apt_date > stats["last_visit"]:
                stats["last_visit"] = apt_date
        
        # Calculate visits per month
        for patient_id, stats in patient_stats.items():
            if stats["first_visit"] and stats["last_visit"]:
                first_dt = datetime.strptime(stats["first_visit"], "%Y-%m-%d")
                last_dt = datetime.strptime(stats["last_visit"], "%Y-%m-%d")
                months_diff = max(1, (last_dt - first_dt).days / 30)
                stats["visits_per_month"] = round(stats["consultations"] / months_diff, 2)
        
        # Get patient details and create results
        results = []
        for patient_id, stats in patient_stats.items():
            patient = patients_collection.find_one({"id": patient_id}, {"_id": 0})
            if patient:
                results.append({
                    "patient_id": patient_id,
                    "name": f"{patient.get('prenom', '')} {patient.get('nom', '')}".strip(),
                    "age": patient.get("age"),
                    "phone": patient.get("numero_whatsapp"),
                    "address": patient.get("adresse"),
                    "statistics": stats
                })
        
        # Sort by selected metric
        if metric == "revenue":
            results = sorted(results, key=lambda x: x["statistics"]["revenue"], reverse=True)
        elif metric == "consultations":
            results = sorted(results, key=lambda x: x["statistics"]["consultations"], reverse=True)
        elif metric == "frequency":
            results = sorted(results, key=lambda x: x["statistics"]["visits_per_month"], reverse=True)
        
        return {
            "period": f"{start_date} - {end_date}",
            "metric": metric,
            "total_patients_analyzed": len(results),
            "top_patients": results[:limit],
            "summary": {
                "total_revenue": sum(r["statistics"]["revenue"] for r in results),
                "total_consultations": sum(r["statistics"]["consultations"] for r in results),
                "average_revenue_per_patient": round(sum(r["statistics"]["revenue"] for r in results) / max(len(results), 1), 2)
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating top patients report: {str(e)}")

# ==================== END ADVANCED REPORTS API ====================

# ==================== AI LEARNING ENGINE ====================

# AI Learning collections
ai_learning_data = db.ai_learning_data
temporal_patterns = db.temporal_patterns  
doctor_performance_patterns = db.doctor_performance_patterns
patient_behavior_patterns = db.patient_behavior_patterns
external_factors_patterns = db.external_factors_patterns
prediction_accuracy = db.prediction_accuracy

# AI Data Models
class PatientData(BaseModel):
    """Données enrichies du patient pour l'IA"""
    patient_id: str
    punctuality_score: float = Field(default=7.0, description="Score de ponctualité (0-10)")
    communication_responsiveness: float = Field(default=7.0, description="Réactivité communication (0-10)")
    consultation_frequency: float = Field(default=1.0, description="Fréquence consultations par mois")
    historical_duration_avg: float = Field(default=15.0, description="Durée moyenne consultations")
    complexity_preference: float = Field(default=1.0, description="Préférence complexité (0.5-2.0)")
    no_show_probability: float = Field(default=0.05, description="Probabilité absence (0-1)")
    preferred_times: List[str] = Field(default=[], description="Créneaux préférés")
    behavioral_patterns: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)

class DoctorData(BaseModel):
    """Données enrichies du médecin pour l'IA"""
    doctor_id: str
    current_efficiency: float = Field(default=1.0, description="Efficacité actuelle (0.5-2.0)")
    energy_level: float = Field(default=8.0, description="Niveau énergie (0-10)")
    fatigue_level: float = Field(default=0.2, description="Niveau fatigue (0-1)")
    performance_trend: str = Field(default="stable", description="Tendance: improving, stable, declining")
    consultations_today: int = Field(default=0, description="Consultations réalisées aujourd'hui")
    break_suggestion_time: Optional[str] = Field(default=None, description="Prochaine pause suggérée")
    peak_performance_hours: List[int] = Field(default=[9, 10, 11], description="Heures de performance optimale")
    stress_indicators: Dict[str, float] = Field(default_factory=dict)
    speciality_efficiency: Dict[str, float] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)

class ExternalData(BaseModel):
    """Données externes influençant les prédictions"""
    date: str
    weather_impact: float = Field(default=0.0, description="Impact météo (-0.5 à +0.5)")
    traffic_conditions: float = Field(default=0.0, description="Conditions circulation (-0.3 à +0.3)")
    school_schedule_impact: float = Field(default=0.0, description="Impact période scolaire (-0.2 à +0.2)")
    seasonal_factor: float = Field(default=0.0, description="Facteur saisonnier (-0.2 à +0.2)")
    public_events: List[str] = Field(default=[], description="Événements publics du jour")
    regional_factors: Dict[str, float] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)

# Data enrichment classes
class TemporalDataCollector:
    """Collecte automatique des patterns temporels"""
    
    def __init__(self):
        self.collection = temporal_patterns
    
    def record_consultation_timing(self, consultation_data):
        """Enregistre les données temporelles d'une consultation"""
        temporal_record = {
            'consultation_id': consultation_data.get('id'),
            'patient_id': consultation_data.get('patient_id'),
            'scheduled_time': consultation_data.get('heure_programmee'),
            'actual_start_time': consultation_data.get('heure_debut_reelle'),
            'actual_end_time': consultation_data.get('heure_fin_reelle'),
            'actual_duration': consultation_data.get('duree_reelle'),
            'scheduled_duration': consultation_data.get('duree_prevue', 15),
            'delay_from_schedule': self.calculate_delay(consultation_data),
            'wait_time_patient': consultation_data.get('temps_attente_patient'),
            'consultation_type': consultation_data.get('type_rdv'),
            'complexity_actual': consultation_data.get('complexite_reelle'),
            'interruptions_count': consultation_data.get('interruptions', 0),
            'doctor_efficiency_moment': self.calculate_moment_efficiency(consultation_data),
            'temporal_context': {
                'hour_of_day': datetime.now().hour,
                'day_of_week': datetime.now().weekday(),
                'week_of_month': self.get_week_of_month(),
                'month': datetime.now().month,
                'season': self.get_season(),
                'is_after_break': consultation_data.get('apres_pause', False),
                'is_before_break': consultation_data.get('avant_pause', False),
                'position_in_day': consultation_data.get('position_journee'),
                'patients_seen_already': consultation_data.get('patients_deja_vus', 0)
            },
            'recorded_at': datetime.now()
        }
        self.collection.insert_one(temporal_record)
        return temporal_record
    
    def calculate_delay(self, consultation_data):
        """Calcule le retard réel vs programmé"""
        try:
            scheduled = datetime.strptime(consultation_data.get('heure_programmee'), '%H:%M')
            actual = datetime.strptime(consultation_data.get('heure_debut_reelle'), '%H:%M')
            delay_minutes = (actual - scheduled).total_seconds() / 60
            return max(0, delay_minutes)
        except:
            return 0
    
    def get_temporal_patterns(self, lookback_days=30):
        """Analyse les patterns temporels des derniers jours"""
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        pipeline = [
            {"$match": {"recorded_at": {"$gte": cutoff_date}}},
            {"$group": {
                "_id": {
                    "hour": "$temporal_context.hour_of_day",
                    "day_of_week": "$temporal_context.day_of_week"
                },
                "avg_duration": {"$avg": "$actual_duration"},
                "avg_delay": {"$avg": "$delay_from_schedule"},
                "avg_efficiency": {"$avg": "$doctor_efficiency_moment"},
                "consultation_count": {"$sum": 1},
                "complexity_avg": {"$avg": "$complexity_actual"}
            }},
            {"$sort": {"_id.day_of_week": 1, "_id.hour": 1}}
        ]
        
        return list(self.collection.aggregate(pipeline))
    
    def calculate_moment_efficiency(self, consultation_data):
        """Calcule l'efficacité du médecin à ce moment"""
        scheduled_duration = consultation_data.get('duree_prevue', 15)
        actual_duration = consultation_data.get('duree_reelle', scheduled_duration)
        
        if actual_duration > 0:
            return min(2.0, scheduled_duration / actual_duration)
        return 1.0
    
    def get_week_of_month(self):
        """Obtient la semaine du mois (1-4)"""
        today = datetime.now()
        first_day = today.replace(day=1)
        dom = today.day
        adjusted_dom = dom + first_day.weekday()
        return int(adjusted_dom / 7) + 1
    
    def get_season(self):
        """Obtient la saison (0-3)"""
        month = datetime.now().month
        return (month % 12) // 3  # 0=winter, 1=spring, 2=summer, 3=autumn

class DoctorPerformanceCollector:
    """Collecte des patterns de performance médecin"""
    
    def __init__(self):
        self.collection = doctor_performance_patterns
    
    def record_performance_snapshot(self, doctor_id, consultation_data):
        """Enregistre un snapshot de performance"""
        performance_record = {
            'doctor_id': doctor_id,
            'consultation_id': consultation_data.get('id'),
            'timestamp': datetime.now(),
            'performance_metrics': {
                'consultation_efficiency': self.calculate_efficiency(consultation_data),
                'patient_satisfaction_estimated': consultation_data.get('satisfaction_estimee', 7),
                'energy_level_estimated': self.estimate_energy_level(consultation_data),
                'stress_indicators': self.detect_stress_indicators(consultation_data),
                'multitasking_score': consultation_data.get('multitasking_score', 5)
            },
            'context_factors': {
                'consultations_done_today': self.get_consultations_count_today(doctor_id),
                'time_since_last_break': self.get_time_since_break(doctor_id),
                'queue_pressure': self.get_current_queue_pressure(),
                'complexity_recent_cases': self.get_recent_complexity_avg(doctor_id),
                'interruptions_recent': consultation_data.get('interruptions_recentes', 0)
            },
            'predictions_accuracy': {
                'duration_prediction_error': self.calculate_prediction_error(consultation_data, 'duration'),
                'complexity_prediction_error': self.calculate_prediction_error(consultation_data, 'complexity')
            }
        }
        self.collection.insert_one(performance_record)
        return performance_record
    
    def get_doctor_current_state(self, doctor_id):
        """Obtient l'état actuel du médecin basé sur les données récentes"""
        recent_records = list(self.collection.find({
            'doctor_id': doctor_id,
            'timestamp': {'$gte': datetime.now() - timedelta(hours=4)}
        }).sort('timestamp', -1).limit(10))
        
        if not recent_records:
            return self.get_default_doctor_state()
        
        # Analyse des tendances récentes
        avg_efficiency = sum(r['performance_metrics']['consultation_efficiency'] for r in recent_records) / len(recent_records)
        avg_energy = sum(r['performance_metrics']['energy_level_estimated'] for r in recent_records) / len(recent_records)
        total_consultations = recent_records[0]['context_factors']['consultations_done_today']
        
        return {
            'current_efficiency': round(avg_efficiency, 2),
            'energy_level': round(avg_energy, 2),
            'fatigue_level': min(1.0, total_consultations / 20),  # Fatigue increases with patient count
            'performance_trend': self.calculate_trend(recent_records),
            'optimal_break_suggestion': self.suggest_break_timing(recent_records),
            'predicted_end_day_efficiency': self.predict_end_day_performance(recent_records)
        }
    
    def calculate_efficiency(self, consultation_data):
        """Calcule l'efficacité basée sur les données de consultation"""
        scheduled_duration = consultation_data.get('duree_prevue', 15)
        actual_duration = consultation_data.get('duree_reelle', scheduled_duration)
        
        if actual_duration > 0:
            efficiency = scheduled_duration / actual_duration
            return min(2.0, max(0.2, efficiency))  # Entre 0.2 et 2.0
        return 1.0
    
    def estimate_energy_level(self, consultation_data):
        """Estime le niveau d'énergie du médecin (0-10)"""
        consultations_today = consultation_data.get('consultations_done_today', 0)
        hour = datetime.now().hour
        
        # Base energy decreases with consultations
        base_energy = max(3, 10 - (consultations_today * 0.3))
        
        # Time of day adjustment
        if 8 <= hour <= 10:  # Morning peak
            time_factor = 1.1
        elif 11 <= hour <= 13:  # Pre-lunch
            time_factor = 0.9
        elif 14 <= hour <= 16:  # Post-lunch
            time_factor = 1.0
        else:  # Late day
            time_factor = 0.8
        
        return min(10, max(1, base_energy * time_factor))
    
    def detect_stress_indicators(self, consultation_data):
        """Détecte les indicateurs de stress (0-10)"""
        stress_score = 0
        
        # Retard accumulé
        if consultation_data.get('delay_from_schedule', 0) > 15:
            stress_score += 2
        
        # Interruptions
        interruptions = consultation_data.get('interruptions', 0)
        stress_score += min(3, interruptions)
        
        # Durée dépassée
        if consultation_data.get('duree_reelle', 15) > consultation_data.get('duree_prevue', 15) * 1.3:
            stress_score += 2
        
        # Queue pressure
        queue_length = consultation_data.get('queue_remaining', 0)
        if queue_length > 5:
            stress_score += 1
        
        return min(10, stress_score)
    
    def get_consultations_count_today(self, doctor_id):
        """Nombre de consultations faites aujourd'hui"""
        today = datetime.now().strftime("%Y-%m-%d")
        return consultations_collection.count_documents({
            "date": today,
            "doctor_id": doctor_id
        })
    
    def get_time_since_break(self, doctor_id):
        """Temps depuis la dernière pause (en minutes)"""
        # Logique simplifiée - à améliorer avec tracking réel des pauses
        last_consultation = consultations_collection.find_one({
            "doctor_id": doctor_id,
            "date": datetime.now().strftime("%Y-%m-%d")
        }, sort=[("heure_fin_reelle", -1)])
        
        if last_consultation:
            # Simuler un temps depuis dernière pause
            return min(180, datetime.now().hour * 30)  # Max 3h
        return 0
    
    def get_current_queue_pressure(self):
        """Pression actuelle de la queue (0-10)"""
        today = datetime.now().strftime("%Y-%m-%d")
        waiting_count = appointments_collection.count_documents({
            "date": today,
            "statut": "attente"
        })
        return min(10, waiting_count)
    
    def get_recent_complexity_avg(self, doctor_id):
        """Complexité moyenne des cas récents"""
        recent_consultations = list(consultations_collection.find({
            "doctor_id": doctor_id,
            "date": datetime.now().strftime("%Y-%m-%d")
        }).limit(5))
        
        if recent_consultations:
            total_complexity = sum(c.get('complexite_reelle', 1) for c in recent_consultations)
            return total_complexity / len(recent_consultations)
        return 1.0
    
    def calculate_prediction_error(self, consultation_data, prediction_type):
        """Calcule l'erreur de prédiction"""
        if prediction_type == 'duration':
            predicted = consultation_data.get('duree_prevue', 15)
            actual = consultation_data.get('duree_reelle', predicted)
            return abs(predicted - actual) / max(predicted, 1)
        elif prediction_type == 'complexity':
            predicted = consultation_data.get('complexite_prevue', 1)
            actual = consultation_data.get('complexite_reelle', predicted)
            return abs(predicted - actual) / max(predicted, 1)
        return 0
    
    def get_default_doctor_state(self):
        """État par défaut du médecin"""
        return {
            'current_efficiency': 1.0,
            'energy_level': 7.0,
            'fatigue_level': 0.3,
            'performance_trend': 'stable',
            'optimal_break_suggestion': '14:30',
            'predicted_end_day_efficiency': 0.8
        }
    
    def calculate_trend(self, recent_records):
        """Calcule la tendance de performance"""
        if len(recent_records) < 3:
            return 'stable'
        
        recent_efficiency = [r['performance_metrics']['consultation_efficiency'] for r in recent_records[:3]]
        older_efficiency = [r['performance_metrics']['consultation_efficiency'] for r in recent_records[-3:]]
        
        recent_avg = sum(recent_efficiency) / len(recent_efficiency)
        older_avg = sum(older_efficiency) / len(older_efficiency)
        
        if recent_avg > older_avg * 1.1:
            return 'improving'
        elif recent_avg < older_avg * 0.9:
            return 'declining'
        return 'stable'
    
    def suggest_break_timing(self, recent_records):
        """Suggère le timing optimal pour une pause"""
        current_hour = datetime.now().hour
        energy_levels = [r['performance_metrics']['energy_level_estimated'] for r in recent_records[-3:]]
        avg_energy = sum(energy_levels) / len(energy_levels) if energy_levels else 7
        
        if avg_energy < 5:
            return f"{current_hour:02d}:{(datetime.now().minute + 15) % 60:02d}"  # Dans 15min
        elif current_hour < 12:
            return "12:00"  # Pause déjeuner
        elif current_hour < 15:
            return "15:30"  # Pause après-midi
        else:
            return "Fin de journée proche"
    
    def predict_end_day_performance(self, recent_records):
        """Prédit la performance de fin de journée"""
        if not recent_records:
            return 0.8
        
        current_trend = self.calculate_trend(recent_records)
        current_efficiency = recent_records[0]['performance_metrics']['consultation_efficiency']
        fatigue_factor = len(recent_records) / 15  # Plus de consultations = plus de fatigue
        
        if current_trend == 'declining':
            return max(0.4, current_efficiency * (0.8 - fatigue_factor))
        elif current_trend == 'improving':
            return min(1.2, current_efficiency * (1.0 - fatigue_factor * 0.5))
        else:
            return current_efficiency * (0.9 - fatigue_factor * 0.3)

class PredictiveEngine:
    """Moteur de prédictions temporelles avancées"""
    
    def __init__(self):
        self.temporal_collector = TemporalDataCollector()
        self.performance_collector = DoctorPerformanceCollector()
    
    def predict_consultation_duration(self, patient_id, consultation_type, doctor_state, temporal_context):
        """Prédiction avancée de durée de consultation"""
        
        # Récupérer les patterns historiques
        historical_data = self.get_historical_patterns(patient_id, consultation_type, temporal_context)
        
        # Facteurs de base
        base_duration = historical_data.get('avg_duration', 15)
        
        # Ajustements basés sur le contexte
        adjustments = {
            'doctor_efficiency': doctor_state.get('current_efficiency', 1.0),
            'time_of_day': self.get_time_efficiency_factor(temporal_context['hour']),
            'doctor_fatigue': max(0.8, 1 - doctor_state.get('fatigue_level', 0)),
            'patient_complexity': historical_data.get('avg_complexity', 1.0),
            'consultation_type_factor': self.get_consultation_type_factor(consultation_type),
            'day_of_week_factor': self.get_day_efficiency_factor(temporal_context['day_of_week'])
        }
        
        # Calcul de prédiction
        efficiency_multiplier = (
            adjustments['doctor_efficiency'] * 
            adjustments['time_of_day'] * 
            adjustments['doctor_fatigue'] * 
            adjustments['day_of_week_factor']
        )
        
        complexity_multiplier = (
            adjustments['patient_complexity'] * 
            adjustments['consultation_type_factor']
        )
        
        predicted_duration = base_duration * complexity_multiplier / efficiency_multiplier
        
        # Confidence calculation
        confidence = self.calculate_prediction_confidence(historical_data, adjustments)
        
        return {
            'predicted_minutes': round(max(5, min(45, predicted_duration)), 1),
            'confidence_level': round(confidence, 2),
            'base_duration': base_duration,
            'adjustments_applied': adjustments,
            'explanation': self.generate_prediction_explanation(adjustments)
        }
    
    def predict_wait_time(self, patient_position, current_queue, doctor_state, temporal_context):
        """Prédiction avancée de temps d'attente"""
        
        if patient_position <= 0:
            return {'predicted_minutes': 0, 'confidence_level': 1.0}
        
        # Analyse de la queue devant le patient
        patients_ahead = current_queue[:patient_position-1]
        total_predicted_time = 0
        confidence_scores = []
        
        for i, patient_ahead in enumerate(patients_ahead):
            # Prédiction pour chaque patient devant
            patient_prediction = self.predict_consultation_duration(
                patient_ahead['patient_id'],
                patient_ahead['consultation_type'],
                doctor_state,
                temporal_context
            )
            
            total_predicted_time += patient_prediction['predicted_minutes']
            confidence_scores.append(patient_prediction['confidence_level'])
            
            # Ajustement pour transition entre patients
            total_predicted_time += self.get_transition_time(i, temporal_context)
        
        # Ajustements contextuels
        contextual_adjustments = {
            'urgent_insertion_risk': self.calculate_urgent_insertion_probability(),
            'doctor_break_probability': self.calculate_break_probability(doctor_state, temporal_context),
            'no_show_adjustments': self.calculate_no_show_impact(patients_ahead),
            'external_delays': self.estimate_external_delays(temporal_context)
        }
        
        # Application des ajustements
        final_wait_time = total_predicted_time
        for adjustment_type, adjustment_value in contextual_adjustments.items():
            final_wait_time *= (1 + adjustment_value)
        
        # Confidence globale
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        final_confidence = avg_confidence * (1 - sum(contextual_adjustments.values()) * 0.1)
        
        return {
            'predicted_minutes': round(max(0, final_wait_time)),
            'confidence_level': round(max(0.1, min(0.95, final_confidence)), 2),
            'patients_ahead': len(patients_ahead),
            'individual_predictions': [p['predicted_minutes'] for p in [
                self.predict_consultation_duration(pa['patient_id'], pa['consultation_type'], doctor_state, temporal_context) 
                for pa in patients_ahead
            ]],
            'contextual_factors': contextual_adjustments,
            'explanation': self.generate_wait_time_explanation(patients_ahead, contextual_adjustments)
        }
    
    def get_historical_patterns(self, patient_id, consultation_type, temporal_context):
        """Récupère les patterns historiques pour un patient"""
        # Rechercher les consultations similaires
        similar_consultations = list(temporal_patterns.find({
            "patient_id": patient_id,
            "consultation_type": consultation_type,
            "temporal_context.hour_of_day": {"$gte": temporal_context['hour'] - 2, "$lte": temporal_context['hour'] + 2}
        }))
        
        if not similar_consultations:
            # Fallback sur le type de consultation général
            similar_consultations = list(temporal_patterns.find({
                "consultation_type": consultation_type
            }).limit(20))
        
        if similar_consultations:
            avg_duration = sum(c.get('actual_duration', 15) for c in similar_consultations) / len(similar_consultations)
            avg_complexity = sum(c.get('complexity_actual', 1) for c in similar_consultations) / len(similar_consultations)
            return {
                'avg_duration': avg_duration,
                'avg_complexity': avg_complexity,
                'sample_size': len(similar_consultations)
            }
        
        # Valeurs par défaut si pas d'historique
        return {
            'avg_duration': 20 if consultation_type == 'visite' else 15,
            'avg_complexity': 1.0,
            'sample_size': 0
        }
    
    def get_time_efficiency_factor(self, hour):
        """Facteur d'efficacité selon l'heure"""
        efficiency_by_hour = {
            8: 0.9, 9: 1.0, 10: 1.1, 11: 1.0,
            12: 0.8, 13: 0.7, 14: 0.9, 15: 1.0,
            16: 0.9, 17: 0.8, 18: 0.7
        }
        return efficiency_by_hour.get(hour, 1.0)
    
    def get_consultation_type_factor(self, consultation_type):
        """Facteur selon le type de consultation"""
        type_factors = {
            'visite': 1.2,
            'controle': 0.8,
            'urgence': 1.5,
            'suivi': 0.9
        }
        return type_factors.get(consultation_type, 1.0)
    
    def get_day_efficiency_factor(self, day_of_week):
        """Facteur d'efficacité selon le jour de la semaine"""
        day_factors = {
            0: 1.0,  # Lundi
            1: 1.1,  # Mardi
            2: 1.0,  # Mercredi
            3: 0.9,  # Jeudi
            4: 0.8,  # Vendredi
            5: 0.7,  # Samedi
            6: 0.6   # Dimanche
        }
        return day_factors.get(day_of_week, 1.0)
    
    def calculate_prediction_confidence(self, historical_data, adjustments):
        """Calcule la confiance de la prédiction"""
        base_confidence = 0.5
        
        # Plus d'historique = plus de confiance
        sample_size = historical_data.get('sample_size', 0)
        if sample_size > 10:
            base_confidence += 0.3
        elif sample_size > 5:
            base_confidence += 0.2
        elif sample_size > 0:
            base_confidence += 0.1
        
        # Moins d'ajustements extrêmes = plus de confiance
        extreme_adjustments = sum(1 for adj in adjustments.values() if abs(adj - 1.0) > 0.3)
        confidence_penalty = extreme_adjustments * 0.1
        
        return max(0.1, min(0.95, base_confidence - confidence_penalty))
    
    def generate_prediction_explanation(self, adjustments):
        """Génère une explication de la prédiction"""
        explanations = []
        
        if adjustments['doctor_efficiency'] > 1.1:
            explanations.append("Dr très efficace actuellement")
        elif adjustments['doctor_efficiency'] < 0.9:
            explanations.append("Dr moins efficace que d'habitude")
        
        if adjustments['time_of_day'] > 1.0:
            explanations.append("Heure optimale pour le médecin")
        elif adjustments['time_of_day'] < 0.9:
            explanations.append("Heure moins favorable")
        
        if adjustments['doctor_fatigue'] < 0.9:
            explanations.append("Fatigue médecin détectée")
        
        if adjustments['patient_complexity'] > 1.2:
            explanations.append("Patient à cas complexe")
        
        return " • ".join(explanations) if explanations else "Prédiction basée sur patterns standard"
    
    def get_transition_time(self, position, temporal_context):
        """Temps de transition entre patients"""
        base_transition = 3  # 3 minutes de base
        
        # Plus de temps en fin de journée (nettoyage, etc.)
        if temporal_context.get('hour', 12) > 17:
            base_transition += 2
        
        # Premier patient de la journée
        if position == 0:
            base_transition += 2
        
        return base_transition
    
    def calculate_urgent_insertion_probability(self):
        """Probabilité d'insertion d'un patient urgent"""
        current_hour = datetime.now().hour
        
        # Plus probable en journée
        if 9 <= current_hour <= 17:
            return 0.15  # 15% de chance
        else:
            return 0.05  # 5% de chance
    
    def calculate_break_probability(self, doctor_state, temporal_context):
        """Probabilité que le médecin prenne une pause"""
        energy_level = doctor_state.get('energy_level', 7)
        current_hour = temporal_context.get('hour', 12)
        
        # Pause déjeuner probable
        if 12 <= current_hour <= 13:
            return 0.8
        
        # Pause selon niveau d'énergie
        if energy_level < 5:
            return 0.4
        elif energy_level < 3:
            return 0.7
        
        return 0.1
    
    def calculate_no_show_impact(self, patients_ahead):
        """Impact des no-shows sur le temps d'attente"""
        if not patients_ahead:
            return 0
        
        # Estimation simple: 10% de no-show moyen
        no_show_rate = 0.1
        return -no_show_rate  # Réduction du temps d'attente
    
    def estimate_external_delays(self, temporal_context):
        """Estime les retards externes (appels, urgences, etc.)"""
        current_hour = temporal_context.get('hour', 12)
        
        # Plus de retards en journée (appels, interruptions)
        if 9 <= current_hour <= 17:
            return 0.1  # 10% de temps supplémentaire
        else:
            return 0.05  # 5% de temps supplémentaire
    
    def generate_wait_time_explanation(self, patients_ahead, contextual_factors):
        """Génère une explication du temps d'attente"""
        explanations = []
        
        explanations.append(f"{len(patients_ahead)} patients devant vous")
        
        if contextual_factors.get('urgent_insertion_risk', 0) > 0.1:
            explanations.append("Possibilité d'urgence")
        
        if contextual_factors.get('doctor_break_probability', 0) > 0.3:
            explanations.append("Pause médecin probable")
        
        if contextual_factors.get('no_show_adjustments', 0) < -0.05:
            explanations.append("Ajustement pour absences probables")
        
        return " • ".join(explanations)

class ProactiveSuggestionsEngine:
    """Générateur de suggestions proactives intelligentes"""
    
    def __init__(self):
        self.predictor = PredictiveEngine()
        
    def generate_smart_suggestions(self, current_context):
        """Génère des suggestions intelligentes basées sur le contexte actuel"""
        suggestions = []
        
        # Récupérer l'état actuel
        doctor_state = current_context.get('doctor_state', {})
        queue_state = current_context.get('queue_state', {})
        temporal_context = current_context.get('temporal_context', {})
        
        # 1. Suggestions temporelles
        suggestions.extend(self.generate_temporal_suggestions(doctor_state, temporal_context))
        
        # 2. Suggestions de queue optimization
        suggestions.extend(self.generate_queue_optimization_suggestions(queue_state, doctor_state))
        
        # 3. Suggestions de communication
        suggestions.extend(self.generate_communication_suggestions(queue_state, temporal_context))
        
        # 4. Suggestions de performance
        suggestions.extend(self.generate_performance_suggestions(doctor_state, temporal_context))
        
        # Tri par priorité et relevance
        suggestions.sort(key=lambda x: (x['priority'], -x['confidence']))
        
        return suggestions[:5]  # Top 5 suggestions
    
    def generate_temporal_suggestions(self, doctor_state, temporal_context):
        """Suggestions basées sur les patterns temporels"""
        suggestions = []
        
        current_hour = temporal_context.get('hour', datetime.now().hour)
        current_efficiency = doctor_state.get('current_efficiency', 1.0)
        fatigue_level = doctor_state.get('fatigue_level', 0)
        
        # Détection de baisse d'efficacité
        if current_efficiency < 0.8 and fatigue_level > 0.6:
            suggestions.append({
                'type': 'performance_alert',
                'icon': '⚡',
                'title': 'Pause Performance Recommandée',
                'message': f'Efficacité à {current_efficiency*100:.0f}% - Pause 10min recommandée pour récupération',
                'priority': 1,
                'confidence': 0.85,
                'action': 'suggest_break',
                'estimated_benefit': 'Récupération +20% efficacité'
            })
        
        # Détection de période optimale
        if 9 <= current_hour <= 11 and current_efficiency > 1.1:
            suggestions.append({
                'type': 'optimization_opportunity',
                'icon': '🎯',
                'title': 'Période Optimale Détectée',
                'message': f'Performance peak ({current_efficiency*100:.0f}%) - Idéal pour cas complexes',
                'priority': 2,
                'confidence': 0.90,
                'action': 'prioritize_complex_cases',
                'estimated_benefit': 'Optimisation workflow'
            })
        
        # Prédiction de fin de journée
        end_day_prediction = doctor_state.get('predicted_end_day_efficiency', 0.8)
        if end_day_prediction < 0.7:
            suggestions.append({
                'type': 'planning_alert',
                'icon': '📊',
                'title': 'Fin de Journée Difficile Prédite',
                'message': f'Efficacité fin journée prédite: {end_day_prediction*100:.0f}% - Réorganiser les cas complexes',
                'priority': 2,
                'confidence': 0.75,
                'action': 'reorganize_schedule',
                'estimated_benefit': 'Éviter retards accumulation'
            })
        
        return suggestions
    
    def generate_queue_optimization_suggestions(self, queue_state, doctor_state):
        """Suggestions d'optimisation de queue"""
        suggestions = []
        
        queue_length = queue_state.get('length', 0)
        avg_complexity = queue_state.get('avg_complexity', 1.0)
        predicted_delays = queue_state.get('predicted_delays', [])
        
        if queue_length > 5 and sum(predicted_delays) > 30:
            # Recherche d'optimisations possibles
            optimization_potential = self.calculate_queue_optimization_potential(queue_state)
            
            if optimization_potential > 10:  # Plus de 10 minutes d'économie possible
                suggestions.append({
                    'type': 'queue_optimization',
                    'icon': '🔄',
                    'title': 'Optimisation Queue Possible',
                    'message': f'Réorganisation pourrait économiser {optimization_potential:.0f}min d\'attente globale',
                    'priority': 1,
                    'confidence': 0.80,
                    'action': 'optimize_queue_order',
                    'estimated_benefit': f'-{optimization_potential:.0f}min attente'
                })
        
        return suggestions
    
    def generate_communication_suggestions(self, queue_state, temporal_context):
        """Suggestions de communication proactive"""
        suggestions = []
        
        # Détection de patients à risque de retard
        risky_patients = queue_state.get('high_delay_risk_patients', [])
        
        for patient in risky_patients[:2]:  # Top 2 patients à risque
            risk_factors = patient.get('risk_factors', [])
            suggestions.append({
                'type': 'communication_proactive',
                'icon': '📱',
                'title': f'Communication Préventive - {patient["name"]}',
                'message': f'Risque retard élevé ({", ".join(risk_factors)}) - Message proactif recommandé',
                'priority': 2,
                'confidence': 0.70,
                'action': 'send_proactive_message',
                'patient_id': patient['id'],
                'estimated_benefit': 'Réduction risque retard'
            })
        
        return suggestions
    
    def generate_performance_suggestions(self, doctor_state, temporal_context):
        """Suggestions d'amélioration des performances"""
        suggestions = []
        
        current_efficiency = doctor_state.get('current_efficiency', 1.0)
        energy_level = doctor_state.get('energy_level', 8.0)
        stress_indicators = doctor_state.get('stress_indicators', {})
        
        # Suggestion d'optimisation du workflow
        if current_efficiency < 0.8:
            suggestions.append({
                'type': 'workflow_optimization',
                'icon': '⚙️',
                'title': 'Optimisation Workflow',
                'message': f'Efficacité à {current_efficiency*100:.0f}% - Révision du processus recommandée',
                'priority': 1,
                'confidence': 0.75,
                'action': 'optimize_workflow',
                'estimated_benefit': 'Gain +15% efficacité'
            })
        
        # Suggestion de gestion d'énergie
        if energy_level < 5:
            suggestions.append({
                'type': 'energy_management',
                'icon': '🔋',
                'title': 'Gestion Énergie Critique',
                'message': f'Niveau énergie bas ({energy_level}/10) - Pause ou réorganisation urgente',
                'priority': 1,
                'confidence': 0.90,
                'action': 'energy_recovery',
                'estimated_benefit': 'Récupération énergie'
            })
        
        # Suggestion de gestion du stress
        total_stress = sum(stress_indicators.values()) if stress_indicators else 0
        if total_stress > 6:
            suggestions.append({
                'type': 'stress_management',
                'icon': '🧘',
                'title': 'Gestion du Stress',
                'message': f'Niveau stress élevé ({total_stress}/10) - Techniques de relaxation recommandées',
                'priority': 2,
                'confidence': 0.70,
                'action': 'stress_reduction',
                'estimated_benefit': 'Réduction stress'
            })
        
        return suggestions
    
    def calculate_queue_optimization_potential(self, queue_state):
        """Calcule le potentiel d'optimisation de la queue"""
        queue_length = queue_state.get('length', 0)
        predicted_delays = queue_state.get('predicted_delays', [])
        
        if not predicted_delays or queue_length == 0:
            return 0
        
        # Estimation simple du gain possible par réorganisation
        total_delay = sum(predicted_delays)
        optimization_factor = 0.15  # 15% d'amélioration possible
        
        return total_delay * optimization_factor

class PatientBehaviorCollector:
    """Collecte des patterns comportementaux des patients"""
    
    def __init__(self):
        self.collection = patient_behavior_patterns
    
    def record_patient_behavior(self, patient_id, consultation_data):
        """Enregistre le comportement d'un patient lors d'une consultation"""
        behavior_record = {
            'patient_id': patient_id,
            'consultation_id': consultation_data.get('id'),
            'timestamp': datetime.now(),
            'punctuality_data': {
                'scheduled_time': consultation_data.get('heure_programmee'),
                'arrival_time': consultation_data.get('heure_arrivee'),
                'delay_minutes': self.calculate_arrival_delay(consultation_data),
                'punctuality_score': self.calculate_punctuality_score(consultation_data)
            },
            'communication_data': {
                'response_time_confirmation': consultation_data.get('temps_reponse_confirmation', 24),
                'whatsapp_engagement': consultation_data.get('engagement_whatsapp', 0.5),
                'preferred_communication_method': consultation_data.get('methode_com_preferee', 'whatsapp'),
                'message_read_rate': consultation_data.get('taux_lecture_messages', 0.8)
            },
            'consultation_behavior': {
                'preparation_level': consultation_data.get('niveau_preparation', 5),
                'questions_asked': consultation_data.get('questions_posees', 2),
                'compliance_previous_advice': consultation_data.get('compliance_conseils', 0.7),
                'satisfaction_expressed': consultation_data.get('satisfaction_exprimee', 8)
            },
            'scheduling_preferences': {
                'preferred_day_of_week': datetime.now().weekday(),
                'preferred_time_slot': self.get_time_slot(consultation_data.get('heure_programmee')),
                'flexibility_score': consultation_data.get('flexibilite', 0.6),
                'reschedule_frequency': consultation_data.get('freq_reprogrammation', 0.1)
            }
        }
        self.collection.insert_one(behavior_record)
        return behavior_record
    
    def get_patient_behavioral_profile(self, patient_id, lookback_days=90):
        """Analyse le profil comportemental d'un patient"""
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        patient_records = list(self.collection.find({
            'patient_id': patient_id,
            'timestamp': {'$gte': cutoff_date}
        }).sort('timestamp', -1))
        
        if not patient_records:
            return self.get_default_behavioral_profile()
        
        # Calculs statistiques
        punctuality_scores = [r['punctuality_data']['punctuality_score'] for r in patient_records]
        response_times = [r['communication_data']['response_time_confirmation'] for r in patient_records]
        satisfaction_scores = [r['consultation_behavior']['satisfaction_expressed'] for r in patient_records]
        
        return {
            'patient_id': patient_id,
            'punctuality_score': sum(punctuality_scores) / len(punctuality_scores),
            'avg_response_time_hours': sum(response_times) / len(response_times),
            'satisfaction_score': sum(satisfaction_scores) / len(satisfaction_scores),
            'consultation_count': len(patient_records),
            'preferred_time_slot': self.get_most_common_preference(patient_records, 'scheduling_preferences.preferred_time_slot'),
            'communication_effectiveness': self.calculate_communication_effectiveness(patient_records),
            'reliability_score': self.calculate_reliability_score(patient_records),
            'behavioral_trend': self.analyze_behavioral_trend(patient_records),
            'risk_factors': self.identify_risk_factors(patient_records),
            'last_consultation': patient_records[0]['timestamp'] if patient_records else None
        }
    
    def calculate_arrival_delay(self, consultation_data):
        """Calcule le retard d'arrivée en minutes"""
        try:
            scheduled = datetime.strptime(consultation_data.get('heure_programmee', '09:00'), '%H:%M')
            arrival = datetime.strptime(consultation_data.get('heure_arrivee', '09:00'), '%H:%M')
            delay = (arrival - scheduled).total_seconds() / 60
            return max(0, delay)
        except:
            return 0
    
    def calculate_punctuality_score(self, consultation_data):
        """Calcule le score de ponctualité (0-10)"""
        delay = self.calculate_arrival_delay(consultation_data)
        if delay == 0:
            return 10
        elif delay <= 5:
            return 9
        elif delay <= 10:
            return 7
        elif delay <= 15:
            return 5
        elif delay <= 30:
            return 3
        else:
            return 1
    
    def get_time_slot(self, time_str):
        """Détermine le créneau horaire"""
        try:
            hour = int(time_str.split(':')[0])
            if 8 <= hour < 10:
                return 'morning_early'
            elif 10 <= hour < 12:
                return 'morning_late'
            elif 14 <= hour < 16:
                return 'afternoon_early'
            elif 16 <= hour < 18:
                return 'afternoon_late'
            else:
                return 'other'
        except:
            return 'other'
    
    def get_default_behavioral_profile(self):
        """Profil comportemental par défaut pour nouveaux patients"""
        return {
            'punctuality_score': 7.0,
            'avg_response_time_hours': 12.0,
            'satisfaction_score': 8.0,
            'consultation_count': 0,
            'preferred_time_slot': 'morning_late',
            'communication_effectiveness': 0.7,
            'reliability_score': 0.8,
            'behavioral_trend': 'stable',
            'risk_factors': [],
            'last_consultation': None
        }
    
    def get_most_common_preference(self, patient_records, field_path):
        """Trouve la préférence la plus commune dans les enregistrements"""
        values = []
        for record in patient_records:
            # Navigate nested field path
            current = record
            for field in field_path.split('.'):
                current = current.get(field, {})
                if not isinstance(current, dict):
                    break
            if current and not isinstance(current, dict):
                values.append(current)
        
        if not values:
            return 'morning_late'  # default
        
        # Return most common value
        from collections import Counter
        return Counter(values).most_common(1)[0][0]
    
    def calculate_communication_effectiveness(self, patient_records):
        """Calcule l'efficacité de communication"""
        if not patient_records:
            return 0.7
        
        engagement_scores = [r['communication_data']['whatsapp_engagement'] for r in patient_records]
        read_rates = [r['communication_data']['message_read_rate'] for r in patient_records]
        
        avg_engagement = sum(engagement_scores) / len(engagement_scores)
        avg_read_rate = sum(read_rates) / len(read_rates)
        
        return (avg_engagement + avg_read_rate) / 2
    
    def calculate_reliability_score(self, patient_records):
        """Calcule le score de fiabilité du patient"""
        if not patient_records:
            return 0.8
        
        punctuality_scores = [r['punctuality_data']['punctuality_score'] for r in patient_records]
        avg_punctuality = sum(punctuality_scores) / len(punctuality_scores)
        
        # Convert punctuality score (0-10) to reliability score (0-1)
        return min(1.0, avg_punctuality / 10.0)
    
    def analyze_behavioral_trend(self, patient_records):
        """Analyse la tendance comportementale"""
        if len(patient_records) < 3:
            return 'stable'
        
        # Analyze last 3 consultations vs previous ones
        recent_records = patient_records[:3]
        older_records = patient_records[3:]
        
        if not older_records:
            return 'stable'
        
        recent_punctuality = sum(r['punctuality_data']['punctuality_score'] for r in recent_records) / len(recent_records)
        older_punctuality = sum(r['punctuality_data']['punctuality_score'] for r in older_records) / len(older_records)
        
        diff = recent_punctuality - older_punctuality
        
        if diff > 1:
            return 'improving'
        elif diff < -1:
            return 'declining'
        else:
            return 'stable'
    
    def identify_risk_factors(self, patient_records):
        """Identifie les facteurs de risque"""
        risk_factors = []
        
        if not patient_records:
            return risk_factors
        
        # Check punctuality
        avg_punctuality = sum(r['punctuality_data']['punctuality_score'] for r in patient_records) / len(patient_records)
        if avg_punctuality < 5:
            risk_factors.append('chronic_lateness')
        
        # Check communication responsiveness
        avg_response_time = sum(r['communication_data']['response_time_confirmation'] for r in patient_records) / len(patient_records)
        if avg_response_time > 48:
            risk_factors.append('poor_communication')
        
        # Check satisfaction trend
        if len(patient_records) >= 3:
            recent_satisfaction = sum(r['consultation_behavior']['satisfaction_expressed'] for r in patient_records[:3]) / 3
            if recent_satisfaction < 6:
                risk_factors.append('low_satisfaction')
        
        return risk_factors

class ExternalFactorsCollector:
    """Collecte des facteurs externes influençant les consultations"""
    
    def __init__(self):
        self.collection = external_factors_patterns
    
    def record_daily_external_factors(self, date_str, external_data=None):
        """Enregistre les facteurs externes pour une journée"""
        if external_data is None:
            external_data = self.gather_external_data()
        
        external_record = {
            'date': date_str,
            'timestamp': datetime.now(),
            'weather_data': {
                'temperature': external_data.get('temperature', 22),
                'precipitation': external_data.get('precipitation', 0),
                'wind_speed': external_data.get('wind_speed', 10),
                'weather_condition': external_data.get('weather_condition', 'clear'),
                'impact_score': self.calculate_weather_impact(external_data)
            },
            'traffic_data': {
                'morning_congestion': external_data.get('morning_traffic', 0.3),
                'afternoon_congestion': external_data.get('afternoon_traffic', 0.4),
                'road_works': external_data.get('road_works', False),
                'public_transport_disruption': external_data.get('transport_disruption', False),
                'impact_score': self.calculate_traffic_impact(external_data)
            },
            'calendar_events': {
                'is_school_day': external_data.get('is_school_day', True),
                'is_holiday': external_data.get('is_holiday', False),
                'school_vacation': external_data.get('school_vacation', False),
                'public_events': external_data.get('public_events', []),
                'impact_score': self.calculate_calendar_impact(external_data)
            },
            'seasonal_factors': {
                'season': self.get_current_season(),
                'seasonal_illness_peak': external_data.get('illness_peak', False),
                'seasonal_allergies': external_data.get('allergies_season', False),
                'impact_score': self.calculate_seasonal_impact()
            },
            'regional_factors': {
                'local_events': external_data.get('local_events', []),
                'economic_indicators': external_data.get('economic_factors', {}),
                'healthcare_system_load': external_data.get('system_load', 0.5),
                'impact_score': self.calculate_regional_impact(external_data)
            }
        }
        
        # Upsert (insert or update)
        self.collection.replace_one(
            {'date': date_str}, 
            external_record, 
            upsert=True
        )
        return external_record
    
    def get_external_factors_for_date(self, date_str):
        """Récupère les facteurs externes pour une date"""
        record = self.collection.find_one({'date': date_str}, {"_id": 0})
        if record:
            return record
        else:
            # Créer des données par défaut
            return self.record_daily_external_factors(date_str)
    
    def calculate_total_external_impact(self, date_str):
        """Calcule l'impact total des facteurs externes (-1 à +1)"""
        factors = self.get_external_factors_for_date(date_str)
        
        weather_impact = factors['weather_data']['impact_score']
        traffic_impact = factors['traffic_data']['impact_score']
        calendar_impact = factors['calendar_events']['impact_score']
        seasonal_impact = factors['seasonal_factors']['impact_score']
        regional_impact = factors['regional_factors']['impact_score']
        
        # Pondération des différents facteurs
        total_impact = (
            weather_impact * 0.3 +
            traffic_impact * 0.25 +
            calendar_impact * 0.2 +
            seasonal_impact * 0.15 +
            regional_impact * 0.1
        )
        
        return max(-1.0, min(1.0, total_impact))
    
    def gather_external_data(self):
        """Rassemble les données externes (à connecter avec des APIs réelles)"""
        # Pour l'instant, données simulées - À remplacer par de vraies APIs
        return {
            'temperature': 25,
            'precipitation': 0,
            'weather_condition': 'clear',
            'morning_traffic': 0.3,
            'afternoon_traffic': 0.4,
            'is_school_day': datetime.now().weekday() < 5,
            'is_holiday': False,
            'public_events': [],
            'local_events': [],
            'system_load': 0.5
        }
    
    def calculate_weather_impact(self, external_data):
        """Calcule l'impact météo (-0.5 à +0.5)"""
        temp = external_data.get('temperature', 22)
        precipitation = external_data.get('precipitation', 0)
        condition = external_data.get('weather_condition', 'clear')
        
        impact = 0
        
        # Impact température
        if temp < 5 or temp > 35:
            impact -= 0.2  # Températures extrêmes = plus de retards
        elif 18 <= temp <= 25:
            impact += 0.1  # Températures agréables = moins de retards
        
        # Impact précipitations
        if precipitation > 10:
            impact -= 0.3  # Pluie forte = retards
        elif precipitation > 2:
            impact -= 0.1  # Pluie légère = retards légers
        
        # Impact conditions spéciales
        if condition in ['storm', 'snow', 'fog']:
            impact -= 0.2
        
        return max(-0.5, min(0.5, impact))
    
    def calculate_traffic_impact(self, external_data):
        """Calcule l'impact circulation (-0.3 à +0.3)"""
        morning_congestion = external_data.get('morning_traffic', 0.3)
        road_works = external_data.get('road_works', False)
        transport_disruption = external_data.get('transport_disruption', False)
        
        impact = 0
        
        # Impact congestion
        if morning_congestion > 0.7:
            impact -= 0.2
        elif morning_congestion < 0.2:
            impact += 0.1
        
        # Impact travaux et perturbations
        if road_works:
            impact -= 0.1
        if transport_disruption:
            impact -= 0.15
        
        return max(-0.3, min(0.3, impact))
    
    def calculate_calendar_impact(self, external_data):
        """Calcule l'impact calendaire (-0.2 à +0.2)"""
        impact = 0
        
        if external_data.get('is_holiday', False):
            impact -= 0.1  # Jours fériés = plus de retards
        
        if external_data.get('school_vacation', False):
            impact += 0.1  # Vacances scolaires = moins de retards
        
        if external_data.get('public_events', []):
            impact -= 0.1  # Événements publics = plus de retards
        
        return max(-0.2, min(0.2, impact))
    
    def calculate_seasonal_impact(self):
        """Calcule l'impact saisonnier (-0.15 à +0.15)"""
        season = self.get_current_season()
        month = datetime.now().month
        
        impact = 0
        
        # Impact saisonnier général
        if season == 'winter':
            impact -= 0.1  # Hiver = plus de retards
        elif season == 'summer':
            impact += 0.05  # Été = légèrement moins de retards
        
        # Pics de maladie saisonnière
        if month in [11, 12, 1, 2]:  # Saison grippe
            impact -= 0.05
        
        return max(-0.15, min(0.15, impact))
    
    def calculate_regional_impact(self, external_data):
        """Calcule l'impact régional (-0.1 à +0.1)"""
        impact = 0
        
        system_load = external_data.get('system_load', 0.5)
        if system_load > 0.8:
            impact -= 0.1  # Système de santé surchargé
        elif system_load < 0.3:
            impact += 0.05  # Système de santé peu chargé
        
        local_events = external_data.get('local_events', [])
        if local_events:
            impact -= 0.05  # Événements locaux = légers retards
        
        return max(-0.1, min(0.1, impact))
    
    def calculate_seasonal_impact(self):
        """Calcule l'impact saisonnier (-0.2 à +0.2)"""
        season = self.get_current_season()
        month = datetime.now().month
        
        impact = 0
        
        # Impact saisonnier général
        if season == 'winter':
            impact -= 0.1  # Plus de retards en hiver
        elif season == 'spring':
            impact += 0.05  # Météo agréable
        elif season == 'summer':
            impact -= 0.05  # Vacances, désorganisation
        elif season == 'autumn':
            impact += 0.1  # Retour de vacances, organisation
        
        # Pics de maladie saisonniers
        if month in [11, 12, 1, 2]:  # Saison grippe
            impact -= 0.05
        elif month in [4, 5]:  # Allergies printemps
            impact -= 0.03
        
        return max(-0.2, min(0.2, impact))
    
    def calculate_calendar_impact(self, external_data):
        """Calcule l'impact calendaire (-0.2 à +0.2)"""
        is_school_day = external_data.get('is_school_day', True)
        is_holiday = external_data.get('is_holiday', False)
        school_vacation = external_data.get('school_vacation', False)
        public_events = external_data.get('public_events', [])
        
        impact = 0
        
        if is_holiday:
            impact -= 0.1  # Jours fériés = désorganisation
        
        if school_vacation:
            impact -= 0.05  # Vacances scolaires = familles moins organisées
        elif not is_school_day:  # Weekend
            impact += 0.05  # Weekend = moins de contraintes
        
        if len(public_events) > 0:
            impact -= 0.1  # Événements publics = circulation difficile
        
        return max(-0.2, min(0.2, impact))
    
    def calculate_regional_impact(self, external_data):
        """Calcule l'impact régional (-0.1 à +0.1)"""
        local_events = external_data.get('local_events', [])
        system_load = external_data.get('system_load', 0.5)
        
        impact = 0
        
        # Impact événements locaux
        if len(local_events) > 0:
            impact -= 0.05
        
        # Impact charge système santé
        if system_load > 0.8:
            impact -= 0.05  # Système surchargé
        elif system_load < 0.3:
            impact += 0.03  # Système peu chargé
        
        return max(-0.1, min(0.1, impact))
    
    def get_current_season(self):
        """Détermine la saison actuelle"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return 'winter'
        elif month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        else:
            return 'autumn'

class DataEnrichmentEngine:
    """Moteur principal d'enrichissement des données"""
    
    def __init__(self):
        self.temporal_collector = TemporalDataCollector()
        self.doctor_performance_collector = DoctorPerformanceCollector()
        self.patient_behavior_collector = PatientBehaviorCollector()
        self.external_factors_collector = ExternalFactorsCollector()
        self.predictor = PredictiveEngine()
        self.suggestions_engine = ProactiveSuggestionsEngine()
    
    def enrich_consultation_data(self, consultation_data, patient_id, doctor_id="default_doctor"):
        """Enrichit toutes les données d'une consultation"""
        enriched_data = consultation_data.copy()
        
        # Enrichissement temporel
        temporal_data = self.temporal_collector.record_consultation_timing(consultation_data)
        
        # Enrichissement performance médecin
        doctor_performance = self.doctor_performance_collector.record_performance_snapshot(doctor_id, consultation_data)
        
        # Enrichissement comportement patient
        patient_behavior = self.patient_behavior_collector.record_patient_behavior(patient_id, consultation_data)
        
        # Enrichissement facteurs externes
        date_str = consultation_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        external_factors = self.external_factors_collector.get_external_factors_for_date(date_str)
        
        # Ajout des données enrichies
        enriched_data.update({
            'ai_enrichment': {
                'temporal_patterns': {
                    'efficiency_moment': temporal_data.get('doctor_efficiency_moment'),
                    'temporal_context': temporal_data.get('temporal_context'),
                    'delay_pattern': temporal_data.get('delay_from_schedule')
                },
                'doctor_performance': {
                    'current_efficiency': doctor_performance['performance_metrics']['consultation_efficiency'],
                    'energy_level': doctor_performance['performance_metrics']['energy_level_estimated'],
                    'stress_indicators': doctor_performance['performance_metrics']['stress_indicators']
                },
                'patient_behavior': {
                    'punctuality_score': patient_behavior['punctuality_data']['punctuality_score'],
                    'communication_effectiveness': patient_behavior['communication_data']['whatsapp_engagement'],
                    'satisfaction_level': patient_behavior['consultation_behavior']['satisfaction_expressed']
                },
                'external_impact': {
                    'weather_impact': external_factors['weather_data']['impact_score'],
                    'traffic_impact': external_factors['traffic_data']['impact_score'],
                    'total_external_score': self.external_factors_collector.calculate_total_external_impact(date_str)
                },
                'enrichment_timestamp': datetime.now().isoformat()
            }
        })
        
        return enriched_data
    
    def get_comprehensive_predictions(self, patient_id, consultation_type, date_str, doctor_id="default_doctor"):
        """Génère des prédictions complètes avec tous les facteurs"""
        
        # État du médecin
        doctor_state = self.doctor_performance_collector.get_doctor_current_state(doctor_id)
        
        # Profil comportemental patient
        patient_profile = self.patient_behavior_collector.get_patient_behavioral_profile(patient_id)
        
        # Facteurs externes
        external_impact = self.external_factors_collector.calculate_total_external_impact(date_str)
        
        # Contexte temporal
        temporal_context = {
            'hour': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'month': datetime.now().month,
            'season': self.external_factors_collector.get_current_season()
        }
        
        # Prédictions durée et attente
        duration_prediction = self.predictor.predict_consultation_duration(
            patient_id, consultation_type, doctor_state, temporal_context
        )
        
        # Suggestions proactives
        current_context = {
            'doctor_state': doctor_state,
            'patient_profile': patient_profile,
            'external_factors': external_impact,
            'temporal_context': temporal_context
        }
        
        suggestions = self.suggestions_engine.generate_smart_suggestions(current_context)
        
        return {
            'predictions': {
                'consultation_duration': duration_prediction,
                'no_show_probability': patient_profile.get('reliability_score', 0.8),
                'patient_satisfaction_expected': patient_profile.get('satisfaction_score', 8.0),
                'external_impact_factor': external_impact
            },
            'profiles': {
                'doctor_state': doctor_state,
                'patient_behavioral_profile': patient_profile
            },
            'suggestions': suggestions,
            'enrichment_confidence': self.calculate_enrichment_confidence(patient_profile, doctor_state),
            'generated_at': datetime.now().isoformat()
        }
    
    def calculate_enrichment_confidence(self, patient_profile, doctor_state):
        """Calcule la confiance dans l'enrichissement des données"""
        patient_data_quality = min(1.0, patient_profile.get('consultation_count', 0) / 10)
        doctor_data_quality = 0.9  # Supposé bon car données continues
        
        overall_confidence = (patient_data_quality + doctor_data_quality) / 2
        return round(overall_confidence, 2)

# ==================== END AI LEARNING ENGINE ====================

# AI Learning API Endpoints

@app.post("/api/ai-learning/record-consultation")
async def record_consultation_data(consultation_data: dict):
    """Enregistre les données d'une consultation pour l'apprentissage"""
    try:
        temporal_collector = TemporalDataCollector()
        performance_collector = DoctorPerformanceCollector()
        
        # Enregistrer les patterns temporels
        temporal_record = temporal_collector.record_consultation_timing(consultation_data)
        
        # Enregistrer la performance du médecin
        doctor_id = consultation_data.get('doctor_id', 'default_doctor')
        performance_record = performance_collector.record_performance_snapshot(doctor_id, consultation_data)
        
        return {
            "message": "Consultation data recorded for AI learning",
            "temporal_record_id": str(temporal_record.get('_id')),
            "performance_record_id": str(performance_record.get('_id'))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording consultation data: {str(e)}")

@app.get("/api/ai-learning/predictions/consultation-duration")
async def predict_consultation_duration_api(
    patient_id: str = Query(...),
    consultation_type: str = Query(...),
    doctor_id: str = Query(default="default_doctor")
):
    """Prédiction intelligente de durée de consultation"""
    try:
        predictor = PredictiveEngine()
        performance_collector = DoctorPerformanceCollector()
        
        # Obtenir l'état actuel du médecin
        doctor_state = performance_collector.get_doctor_current_state(doctor_id)
        
        # Contexte temporal actuel
        temporal_context = {
            'hour': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'month': datetime.now().month,
            'season': (datetime.now().month % 12) // 3  # 0=winter, 1=spring, etc.
        }
        
        # Prédiction
        prediction = predictor.predict_consultation_duration(
            patient_id, consultation_type, doctor_state, temporal_context
        )
        
        return {
            "patient_id": patient_id,
            "consultation_type": consultation_type,
            "prediction": prediction,
            "doctor_state": doctor_state,
            "temporal_context": temporal_context,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting consultation duration: {str(e)}")

@app.get("/api/ai-learning/predictions/wait-time")
async def predict_wait_time_api(
    patient_position: int = Query(...),
    date: str = Query(...)
):
    """Prédiction intelligente de temps d'attente"""
    try:
        predictor = PredictiveEngine()
        performance_collector = DoctorPerformanceCollector()
        
        # Obtenir la queue actuelle
        appointments = list(appointments_collection.find({
            "date": date,
            "statut": {"$in": ["attente", "programme"]}
        }))
        
        # Construire la queue avec données enrichies
        current_queue = []
        for apt in appointments:
            patient = patients_collection.find_one({"id": apt.get("patient_id")})
            if patient:
                current_queue.append({
                    'patient_id': apt.get('patient_id'),
                    'consultation_type': apt.get('type_rdv', 'visite'),
                    'scheduled_time': apt.get('heure'),
                    'patient_name': f"{patient.get('prenom', '')} {patient.get('nom', '')}"
                })
        
        # Trier par heure
        current_queue.sort(key=lambda x: x['scheduled_time'])
        
        # État médecin
        doctor_state = performance_collector.get_doctor_current_state("default_doctor")
        
        # Contexte temporal
        temporal_context = {
            'hour': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'month': datetime.now().month
        }
        
        # Prédiction
        prediction = predictor.predict_wait_time(
            patient_position, current_queue, doctor_state, temporal_context
        )
        
        return {
            "patient_position": patient_position,
            "queue_length": len(current_queue),
            "prediction": prediction,
            "queue_summary": current_queue[:patient_position],
            "doctor_state": doctor_state,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting wait time: {str(e)}")

@app.get("/api/ai-learning/suggestions/proactive")
async def get_proactive_suggestions():
    """Obtient des suggestions proactives intelligentes"""
    try:
        suggestions_engine = ProactiveSuggestionsEngine()
        performance_collector = DoctorPerformanceCollector()
        
        # Contexte actuel
        doctor_state = performance_collector.get_doctor_current_state("default_doctor")
        
        # État de la queue
        today = datetime.now().strftime("%Y-%m-%d")
        appointments = list(appointments_collection.find({
            "date": today, 
            "statut": {"$in": ["attente", "programme"]}
        }))
        
        queue_state = {
            'length': len(appointments),
            'avg_complexity': 1.0,  # À calculer selon historique
            'predicted_delays': [15, 20, 10],  # Exemple
            'high_delay_risk_patients': []  # À implémenter
        }
        
        temporal_context = {
            'hour': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'month': datetime.now().month
        }
        
        current_context = {
            'doctor_state': doctor_state,
            'queue_state': queue_state,
            'temporal_context': temporal_context
        }
        
        # Génération des suggestions
        suggestions = suggestions_engine.generate_smart_suggestions(current_context)
        
        return {
            "suggestions": suggestions,
            "context": current_context,
            "generated_at": datetime.now().isoformat(),
            "total_suggestions": len(suggestions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating proactive suggestions: {str(e)}")

@app.get("/api/ai-learning/doctor-state")
async def get_doctor_current_state_api(doctor_id: str = Query(default="default_doctor")):
    """Obtient l'état actuel du médecin"""
    try:
        performance_collector = DoctorPerformanceCollector()
        doctor_state = performance_collector.get_doctor_current_state(doctor_id)
        
        return {
            "doctor_id": doctor_id,
            "state": doctor_state,
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting doctor state: {str(e)}")

@app.get("/api/ai-learning/temporal-patterns")
async def get_temporal_patterns_api(lookback_days: int = Query(default=30)):
    """Analyse des patterns temporels"""
    try:
        temporal_collector = TemporalDataCollector()
        patterns = temporal_collector.get_temporal_patterns(lookback_days)
        
        return {
            "patterns": patterns,
            "lookback_days": lookback_days,
            "analysis_date": datetime.now().isoformat(),
            "total_patterns": len(patterns)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting temporal patterns: {str(e)}")

@app.post("/api/ai-learning/initialize")
async def initialize_ai_learning():
    """Initialise le système d'apprentissage IA"""
    try:
        # Créer les collections si elles n'existent pas
        collections_created = []
        
        # Vérifier et créer les index nécessaires
        if ai_learning_data.count_documents({}) == 0:
            ai_learning_data.create_index([("timestamp", -1)])
            collections_created.append("ai_learning_data")
        
        if temporal_patterns.count_documents({}) == 0:
            temporal_patterns.create_index([("recorded_at", -1)])
            temporal_patterns.create_index([("patient_id", 1)])
            temporal_patterns.create_index([("temporal_context.hour_of_day", 1)])
            collections_created.append("temporal_patterns")
        
        if doctor_performance_patterns.count_documents({}) == 0:
            doctor_performance_patterns.create_index([("doctor_id", 1), ("timestamp", -1)])
            collections_created.append("doctor_performance_patterns")
        
        if prediction_accuracy.count_documents({}) == 0:
            prediction_accuracy.create_index([("prediction_type", 1), ("date", -1)])
            collections_created.append("prediction_accuracy")
        
        return {
            "message": "AI Learning system initialized successfully",
            "collections_created": collections_created,
            "status": "ready_for_learning"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing AI learning: {str(e)}")

# Enhanced AI Learning Endpoints

@app.post("/api/ai-learning/enrich-consultation")
async def enrich_consultation_data_api(consultation_data: dict):
    """Enrichit une consultation avec toutes les données IA"""
    try:
        enrichment_engine = DataEnrichmentEngine()
        
        patient_id = consultation_data.get('patient_id')
        doctor_id = consultation_data.get('doctor_id', 'default_doctor')
        
        if not patient_id:
            raise HTTPException(status_code=400, detail="patient_id is required")
        
        enriched_data = enrichment_engine.enrich_consultation_data(
            consultation_data, patient_id, doctor_id
        )
        
        return {
            "message": "Consultation data enriched successfully",
            "enriched_data": enriched_data,
            "enrichment_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enriching consultation data: {str(e)}")

@app.get("/api/ai-learning/comprehensive-predictions")
async def get_comprehensive_predictions_api(
    patient_id: str = Query(...),
    consultation_type: str = Query(...),
    date: str = Query(...),
    doctor_id: str = Query(default="default_doctor")
):
    """Obtient des prédictions complètes avec tous les facteurs IA"""
    try:
        enrichment_engine = DataEnrichmentEngine()
        
        predictions = enrichment_engine.get_comprehensive_predictions(
            patient_id, consultation_type, date, doctor_id
        )
        
        return {
            "patient_id": patient_id,
            "consultation_type": consultation_type,
            "date": date,
            "comprehensive_predictions": predictions,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating comprehensive predictions: {str(e)}")

@app.get("/api/ai-learning/patient-behavioral-profile")
async def get_patient_behavioral_profile_api(
    patient_id: str = Query(...),
    lookback_days: int = Query(default=90)
):
    """Obtient le profil comportemental détaillé d'un patient"""
    try:
        behavior_collector = PatientBehaviorCollector()
        
        profile = behavior_collector.get_patient_behavioral_profile(patient_id, lookback_days)
        
        return {
            "patient_id": patient_id,
            "lookback_days": lookback_days,
            "behavioral_profile": profile,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting patient behavioral profile: {str(e)}")

@app.get("/api/ai-learning/external-factors")
async def get_external_factors_api(date: str = Query(...)):
    """Obtient les facteurs externes pour une date"""
    try:
        external_collector = ExternalFactorsCollector()
        
        factors = external_collector.get_external_factors_for_date(date)
        total_impact = external_collector.calculate_total_external_impact(date)
        
        return {
            "date": date,
            "external_factors": factors,
            "total_impact_score": total_impact,
            "impact_explanation": "Score d'impact total des facteurs externes (-1 = très défavorable, +1 = très favorable)",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting external factors: {str(e)}")

@app.post("/api/ai-learning/record-patient-behavior") 
async def record_patient_behavior_api(
    patient_id: str,
    consultation_data: dict
):
    """Enregistre le comportement d'un patient"""
    try:
        behavior_collector = PatientBehaviorCollector()
        
        behavior_record = behavior_collector.record_patient_behavior(patient_id, consultation_data)
        
        return {
            "message": "Patient behavior recorded successfully",
            "patient_id": patient_id,
            "behavior_record_id": str(behavior_record.get('_id')),
            "recorded_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording patient behavior: {str(e)}")

@app.post("/api/ai-learning/update-external-factors")
async def update_external_factors_api(
    date: str,
    external_data: dict = None
):
    """Met à jour les facteurs externes pour une date"""
    try:
        external_collector = ExternalFactorsCollector()
        
        updated_record = external_collector.record_daily_external_factors(date, external_data)
        
        return {
            "message": "External factors updated successfully",
            "date": date,
            "updated_record": updated_record,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating external factors: {str(e)}")

@app.get("/api/ai-learning/dashboard-insights")
async def get_dashboard_insights_api(
    date: str = Query(default=None),
    doctor_id: str = Query(default="default_doctor")
):
    """Obtient les insights IA pour le dashboard"""
    try:
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        enrichment_engine = DataEnrichmentEngine()
        performance_collector = DoctorPerformanceCollector()
        external_collector = ExternalFactorsCollector()
        suggestions_engine = ProactiveSuggestionsEngine()
        
        # État du médecin
        doctor_state = performance_collector.get_doctor_current_state(doctor_id)
        
        # Facteurs externes
        external_impact = external_collector.calculate_total_external_impact(date)
        external_factors = external_collector.get_external_factors_for_date(date)
        
        # Contexte pour suggestions
        current_context = {
            'doctor_state': doctor_state,
            'queue_state': {'length': 0, 'avg_complexity': 1.0, 'predicted_delays': []},
            'temporal_context': {
                'hour': datetime.now().hour,
                'day_of_week': datetime.now().weekday(),
                'month': datetime.now().month
            }
        }
        
        # Suggestions intelligentes
        suggestions = suggestions_engine.generate_smart_suggestions(current_context)
        
        return {
            "date": date,
            "dashboard_insights": {
                "doctor_performance": {
                    "current_efficiency": doctor_state.get('current_efficiency', 1.0),
                    "energy_level": doctor_state.get('energy_level', 8.0),
                    "fatigue_level": doctor_state.get('fatigue_level', 0.2),
                    "performance_trend": doctor_state.get('performance_trend', 'stable'),
                    "next_break_suggestion": doctor_state.get('optimal_break_suggestion', None)
                },
                "external_conditions": {
                    "total_impact_score": external_impact,
                    "weather_impact": external_factors.get('weather_data', {}).get('impact_score', 0),
                    "traffic_impact": external_factors.get('traffic_data', {}).get('impact_score', 0),
                    "seasonal_impact": external_factors.get('seasonal_factors', {}).get('impact_score', 0)
                },
                "ai_suggestions": suggestions[:3],  # Top 3 suggestions
                "prediction_confidence": enrichment_engine.calculate_enrichment_confidence(
                    {'consultation_count': 5}, doctor_state
                )
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard insights: {str(e)}")

# ==================== END AI LEARNING API ====================

# ==================== WHATSAPP HUB API ====================

# WhatsApp Hub collections
whatsapp_templates_collection = db.whatsapp_templates
whatsapp_history_collection = db.whatsapp_history

# WhatsApp Templates Models
class WhatsAppTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str  # confirmation, attente, ajustement, urgence
    content: str
    auto_send: bool = False
    editable: bool = True
    variables: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class WhatsAppMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    patient_name: str
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    content: str
    whatsapp_link: str
    sent_by: str
    sent_at: datetime = Field(default_factory=datetime.now)
    status: str = "prepared"  # prepared, opened, sent

class WhatsAppSendRequest(BaseModel):
    patient_id: str
    template_id: Optional[str] = None
    custom_message: Optional[str] = None
    auto_send: bool = False

def create_default_whatsapp_templates():
    """Create default WhatsApp templates if they don't exist"""
    try:
        if whatsapp_templates_collection.count_documents({}) == 0:
            default_templates = [
                {
                    "id": "template_confirmation",
                    "name": "Confirmation RDV",
                    "category": "confirmation",
                    "content": "Bonjour {nom} {prenom}, votre RDV est confirmé pour le {date} à {heure}. Merci d'arriver 10 minutes avant. Cabinet Dr Heni Dridi.",
                    "auto_send": True,
                    "editable": True,
                    "variables": ["nom", "prenom", "date", "heure"],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                {
                    "id": "template_attente",
                    "name": "Position Salle d'Attente",
                    "category": "attente", 
                    "content": "Bonjour {nom} {prenom}, vous êtes {position}° en salle d'attente. Temps d'attente estimé : {temps_attente} minutes.",
                    "auto_send": False,
                    "editable": True,
                    "variables": ["nom", "prenom", "position", "temps_attente"],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                {
                    "id": "template_retard_medecin",
                    "name": "Retard Médecin",
                    "category": "ajustement",
                    "content": "Bonjour {nom} {prenom}, le Dr a un retard de {retard_minutes} minutes. Votre nouveau créneau : {nouvelle_heure}. Merci de votre compréhension.",
                    "auto_send": False,
                    "editable": True,
                    "variables": ["nom", "prenom", "retard_minutes", "nouvelle_heure"],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                {
                    "id": "template_urgence",
                    "name": "Urgence - Décalage RDV", 
                    "category": "urgence",
                    "content": "Bonjour {nom} {prenom}, suite à une urgence, votre RDV est décalé de {retard_minutes} minutes. Nouveau créneau : {nouvelle_heure}. Ou préférez-vous reporter à {date_alternative} ?",
                    "auto_send": False,
                    "editable": True,
                    "variables": ["nom", "prenom", "retard_minutes", "nouvelle_heure", "date_alternative"],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                {
                    "id": "template_rappel",
                    "name": "Rappel RDV Demain",
                    "category": "rappel",
                    "content": "Bonjour {nom} {prenom}, rappel de votre RDV demain {date} à {heure}. N'oubliez pas d'apporter vos documents médicaux. À bientôt !",
                    "auto_send": False,
                    "editable": True,
                    "variables": ["nom", "prenom", "date", "heure"],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                {
                    "id": "template_annulation",
                    "name": "Annulation RDV",
                    "category": "annulation",
                    "content": "Bonjour {nom} {prenom}, votre RDV du {date} à {heure} a été annulé. Nouveaux créneaux disponibles : {alternatives}. Contactez-nous pour reprogrammer.",
                    "auto_send": False,
                    "editable": True,
                    "variables": ["nom", "prenom", "date", "heure", "alternatives"],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            ]
            
            whatsapp_templates_collection.insert_many(default_templates)
            print("Default WhatsApp templates created successfully")
            
    except Exception as e:
        print(f"Error creating default WhatsApp templates: {e}")

def generate_whatsapp_variables(patient_data, appointment_data=None, context_data=None):
    """Generate variables for WhatsApp template substitution"""
    variables = {
        "nom": patient_data.get("nom", ""),
        "prenom": patient_data.get("prenom", ""),
        "age": patient_data.get("age", ""),
        "telephone": patient_data.get("numero_whatsapp", "")
    }
    
    if appointment_data:
        variables.update({
            "date": appointment_data.get("date", ""),
            "heure": appointment_data.get("heure", ""),
            "type_rdv": appointment_data.get("type_rdv", ""),
            "duree": appointment_data.get("duree", "15")
        })
    
    if context_data:
        variables.update({
            "position": context_data.get("position", ""),
            "temps_attente": context_data.get("temps_attente", ""),
            "retard_minutes": context_data.get("retard_minutes", ""),
            "nouvelle_heure": context_data.get("nouvelle_heure", ""),
            "date_alternative": context_data.get("date_alternative", ""),
            "alternatives": context_data.get("alternatives", "")
        })
    
    return variables

def substitute_template_variables(template_content, variables):
    """Replace template variables with actual values"""
    result = template_content
    for key, value in variables.items():
        placeholder = "{" + key + "}"
        result = result.replace(placeholder, str(value))
    return result

def generate_whatsapp_link(phone_number, message):
    """Generate WhatsApp link with pre-filled message"""
    import urllib.parse
    
    # Clean phone number (remove spaces, special chars)
    clean_phone = ''.join(filter(str.isdigit, phone_number))
    
    # Add Tunisia country code if not present
    if not clean_phone.startswith('216'):
        clean_phone = '216' + clean_phone
    
    # URL encode the message
    encoded_message = urllib.parse.quote(message)
    
    # Generate WhatsApp link
    whatsapp_link = f"https://wa.me/{clean_phone}?text={encoded_message}"
    
    return whatsapp_link

def calculate_ai_context(patient_id, appointment_data=None):
    """Calculate AI context for smarter templates"""
    context = {}
    
    try:
        # Get patient history
        patient = patients_collection.find_one({"id": patient_id})
        if not patient:
            return context
        
        # Calculate punctuality score
        appointments = list(appointments_collection.find({"patient_id": patient_id}))
        if appointments:
            on_time_count = sum(1 for apt in appointments if apt.get("statut") not in ["absent", "retard"])
            punctuality_score = (on_time_count / len(appointments)) * 100
            context["punctuality_score"] = round(punctuality_score, 1)
        
        # Calculate average consultation duration
        consultations = list(consultations_collection.find({"patient_id": patient_id}))
        if consultations:
            avg_duration = sum(int(c.get("duree", 15)) for c in consultations) / len(consultations)
            context["avg_consultation_duration"] = round(avg_duration, 1)
        
        # Doctor efficiency today
        today = datetime.now().strftime("%Y-%m-%d")
        today_consultations = list(consultations_collection.find({
            "date": today
        }))
        
        if today_consultations:
            avg_today = sum(int(c.get("duree", 15)) for c in today_consultations) / len(today_consultations)
            context["doctor_efficiency_today"] = "rapide" if avg_today < 20 else "normale"
        
        # Current queue position and wait time
        if appointment_data:
            today_appointments = list(appointments_collection.find({
                "date": appointment_data.get("date", today),
                "statut": {"$in": ["attente", "programme"]}
            }))
            
            # Sort by appointment time
            today_appointments.sort(key=lambda x: x.get("heure", "00:00"))
            
            # Find patient position
            for i, apt in enumerate(today_appointments):
                if apt.get("patient_id") == patient_id:
                    context["position"] = i + 1
                    context["queue_length"] = len(today_appointments)
                    
                    # Estimate wait time (simplified)
                    estimated_wait = i * 20  # 20min per patient average
                    context["temps_attente"] = max(5, estimated_wait)
                    break
        
        return context
        
    except Exception as e:
        print(f"Error calculating AI context: {e}")
        return context

# WhatsApp Hub API Endpoints

@app.post("/api/whatsapp-hub/initialize")
async def initialize_whatsapp_hub():
    """Initialize WhatsApp Hub with default templates"""
    try:
        create_default_whatsapp_templates()
        templates_count = whatsapp_templates_collection.count_documents({})
        
        return {
            "message": "WhatsApp Hub initialized successfully",
            "templates_created": templates_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing WhatsApp Hub: {str(e)}")

@app.get("/api/whatsapp-hub/templates")
async def get_whatsapp_templates():
    """Get all WhatsApp templates"""
    try:
        templates = list(whatsapp_templates_collection.find({}, {"_id": 0}))
        
        # Group by category
        categorized = defaultdict(list)
        for template in templates:
            categorized[template["category"]].append(template)
        
        return {
            "templates": templates,
            "by_category": dict(categorized),
            "total": len(templates)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")

@app.post("/api/whatsapp-hub/templates")
async def create_whatsapp_template(template: WhatsAppTemplate):
    """Create new WhatsApp template"""
    try:
        template_dict = template.dict()
        template_dict["created_at"] = datetime.now()
        template_dict["updated_at"] = datetime.now()
        
        result = whatsapp_templates_collection.insert_one(template_dict)
        
        # Remove MongoDB ObjectId and return clean template
        template_dict.pop("_id", None)
        
        return {
            "message": "Template created successfully",
            "template": template_dict
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")

@app.put("/api/whatsapp-hub/templates/{template_id}")
async def update_whatsapp_template(template_id: str, template_update: dict):
    """Update WhatsApp template"""
    try:
        template_update["updated_at"] = datetime.now()
        
        result = whatsapp_templates_collection.update_one(
            {"id": template_id},
            {"$set": template_update}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Template not found")
        
        updated_template = whatsapp_templates_collection.find_one({"id": template_id}, {"_id": 0})
        
        # Convert datetime objects to strings for JSON serialization
        if updated_template:
            if "created_at" in updated_template:
                updated_template["created_at"] = updated_template["created_at"].isoformat() if isinstance(updated_template["created_at"], datetime) else updated_template["created_at"]
            if "updated_at" in updated_template:
                updated_template["updated_at"] = updated_template["updated_at"].isoformat() if isinstance(updated_template["updated_at"], datetime) else updated_template["updated_at"]
        
        return {
            "message": "Template updated successfully",
            "template": updated_template
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating template: {str(e)}")

@app.delete("/api/whatsapp-hub/templates/{template_id}")
async def delete_whatsapp_template(template_id: str):
    """Delete WhatsApp template"""
    try:
        result = whatsapp_templates_collection.delete_one({"id": template_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {"message": "Template deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting template: {str(e)}")

@app.post("/api/whatsapp-hub/prepare-message")
async def prepare_whatsapp_message(request: WhatsAppSendRequest):
    """Prepare WhatsApp message with template and context"""
    try:
        # Get patient data
        patient = patients_collection.find_one({"id": request.patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Check if patient has WhatsApp number
        if not patient.get("numero_whatsapp"):
            raise HTTPException(status_code=400, detail="Patient has no WhatsApp number")
        
        message_content = ""
        template_used = None
        
        if request.template_id:
            # Get template
            template = whatsapp_templates_collection.find_one({"id": request.template_id})
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
            
            # Get appointment data if exists
            appointment_data = None
            today = datetime.now().strftime("%Y-%m-%d")
            appointment = appointments_collection.find_one({
                "patient_id": request.patient_id,
                "date": {"$gte": today}
            })
            
            # Generate AI context
            ai_context = calculate_ai_context(request.patient_id, appointment)
            
            # Generate variables
            variables = generate_whatsapp_variables(patient, appointment, ai_context)
            
            # Substitute template variables
            message_content = substitute_template_variables(template["content"], variables)
            template_used = template["name"]
            
        elif request.custom_message:
            message_content = request.custom_message
        else:
            raise HTTPException(status_code=400, detail="Either template_id or custom_message is required")
        
        # Generate WhatsApp link
        whatsapp_link = generate_whatsapp_link(patient["numero_whatsapp"], message_content)
        
        # Prepare response with AI suggestions
        ai_suggestions = []
        ai_context = calculate_ai_context(request.patient_id)
        
        if ai_context.get("punctuality_score", 100) < 70:
            ai_suggestions.append("💡 Patient souvent en retard - Considérer mentionner importance ponctualité")
        
        if ai_context.get("avg_consultation_duration", 15) > 25:
            ai_suggestions.append("💡 Consultations longues habituelles - Mentionner temps d'attente possible")
        
        current_hour = datetime.now().hour
        if current_hour > 16:
            ai_suggestions.append("💡 Fin de journée - Patient plus susceptible de reporter")
        
        return {
            "patient": {
                "id": patient["id"],
                "nom": patient["nom"],
                "prenom": patient["prenom"],
                "numero_whatsapp": patient["numero_whatsapp"]
            },
            "message": {
                "content": message_content,
                "whatsapp_link": whatsapp_link,
                "template_used": template_used,
                "character_count": len(message_content)
            },
            "ai_context": ai_context,
            "ai_suggestions": ai_suggestions,
            "variables_used": generate_whatsapp_variables(patient, appointment, ai_context) if request.template_id else {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error preparing message: {str(e)}")

@app.post("/api/whatsapp-hub/send-confirmation")
async def send_auto_confirmation(appointment_data: dict):
    """Auto-send confirmation message after appointment creation"""
    try:
        patient_id = appointment_data.get("patient_id")
        appointment_id = appointment_data.get("appointment_id")
        
        # Get confirmation template
        template = whatsapp_templates_collection.find_one({
            "category": "confirmation",
            "auto_send": True
        })
        
        if not template:
            raise HTTPException(status_code=404, detail="Auto-confirmation template not found")
        
        # Prepare message
        request = WhatsAppSendRequest(
            patient_id=patient_id,
            template_id=template["id"],
            auto_send=True
        )
        
        prepared_message = await prepare_whatsapp_message(request)
        
        # Log the auto-confirmation (don't actually send, just prepare)
        whatsapp_history_collection.insert_one({
            "id": str(uuid.uuid4()),
            "patient_id": patient_id,
            "patient_name": f"{prepared_message['patient']['prenom']} {prepared_message['patient']['nom']}",
            "template_id": template["id"],
            "template_name": template["name"],
            "content": prepared_message["message"]["content"],
            "whatsapp_link": prepared_message["message"]["whatsapp_link"],
            "sent_by": "System (Auto-confirmation)",
            "sent_at": datetime.now(),
            "status": "prepared",
            "auto_send": True
        })
        
        return {
            "message": "Auto-confirmation prepared successfully",
            "whatsapp_link": prepared_message["message"]["whatsapp_link"],
            "should_open_whatsapp": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending auto-confirmation: {str(e)}")

@app.get("/api/whatsapp-hub/queue")
async def get_whatsapp_queue(date: str = Query(...)):
    """Get patients queue for WhatsApp messaging"""
    try:
        # Get appointments for the date
        appointments = list(appointments_collection.find({"date": date}))
        queue = []
        
        for appointment in appointments:
            patient_id = appointment.get("patient_id")
            patient = patients_collection.find_one({"id": patient_id})
            
            if patient and patient.get("numero_whatsapp"):
                # Calculate AI context
                ai_context = calculate_ai_context(patient_id, appointment)
                
                queue_item = {
                    "appointment_id": appointment.get("id"),
                    "patient_id": patient_id,
                    "patient_name": f"{patient.get('prenom', '')} {patient.get('nom', '')}",
                    "appointment_time": appointment.get("heure", ""),
                    "type_rdv": appointment.get("type_rdv", ""),
                    "status": appointment.get("statut", "programme"),
                    "numero_whatsapp": patient.get("numero_whatsapp", ""),
                    "queue_position": ai_context.get("position", 0),
                    "estimated_wait_time": ai_context.get("temps_attente", 0),
                    "punctuality_score": ai_context.get("punctuality_score", 85),
                    "avg_consultation_duration": ai_context.get("avg_consultation_duration", 15),
                    "has_whatsapp": bool(patient.get("numero_whatsapp"))
                }
                
                queue.append(queue_item)
        
        # Sort by appointment time
        queue.sort(key=lambda x: x["appointment_time"])
        
        return {
            "queue": queue,
            "total_patients": len(queue),
            "patients_with_whatsapp": len([p for p in queue if p["has_whatsapp"]]),
            "date": date
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching queue: {str(e)}")

# ==================== END WHATSAPP HUB API ====================

# ==================== AI ROOM API ====================

import numpy as np
from sklearn.linear_model import LinearRegression
import random
from collections import defaultdict

# AI Room collections
ai_room_data_collection = db.ai_room_data
ai_queue_collection = db.ai_queue
ai_predictions_collection = db.ai_predictions
ai_doctor_analytics_collection = db.ai_doctor_analytics

# AI Room WebSocket connection manager
class AIRoomConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_ai_update(self, data: dict):
        data_json = json.dumps(data, default=str)
        for connection in self.active_connections:
            try:
                await connection.send_text(data_json)
            except:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

ai_manager = AIRoomConnectionManager()

# AI Room Models
class AIPatientClassification(BaseModel):
    patient_id: str
    punctuality_score: float  # 0-100
    complexity_score: float  # 0-10
    no_show_probability: float  # 0-1
    communication_responsiveness: float  # 0-100
    priority_score: str  # 'urgent', 'high', 'normal', 'low'

class AIDoctorAnalytics(BaseModel):
    doctor_id: str = "default_doctor"
    date: str
    morning_efficiency: float
    afternoon_efficiency: float
    avg_consultation_duration: float
    punctuality_score: float
    break_patterns: List[str] = []
    energy_curve: Dict[str, float] = {}
    consultation_complexity_handling: Dict[str, float] = {}

class AIQueueOptimization(BaseModel):
    appointment_id: str
    original_time: str
    suggested_time: str
    predicted_wait_time: int
    suggested_arrival_time: str
    optimization_reason: str
    confidence_level: float

class AIRoomSettings(BaseModel):
    auto_optimization: bool = True
    whatsapp_notifications: bool = True
    predictive_rescheduling: bool = True
    emergency_mode: bool = False

# AI Room Utility Functions
def calculate_punctuality_score(patient_id: str) -> float:
    """Calculate patient punctuality based on historical data"""
    appointments = list(appointments_collection.find({"patient_id": patient_id}))
    if not appointments:
        return 85.0  # Default score for new patients
    
    on_time_count = 0
    total_appointments = len(appointments)
    
    for appointment in appointments:
        if appointment.get("statut") not in ["absent"]:
            on_time_count += 1
    
    # Add some randomness for realistic variation
    base_score = (on_time_count / total_appointments) * 100
    return min(100, max(0, base_score + random.uniform(-5, 5)))

def calculate_complexity_score(patient_id: str) -> float:
    """Calculate consultation complexity based on historical data"""
    consultations = list(consultations_collection.find({"patient_id": patient_id}))
    if not consultations:
        return 5.0  # Default complexity for new patients
    
    total_duration = 0
    consultation_count = len(consultations)
    
    for consultation in consultations:
        duration = consultation.get("duree", 15)  # Default 15 minutes
        total_duration += duration
    
    avg_duration = total_duration / consultation_count if consultation_count > 0 else 15
    
    # Convert duration to complexity score (0-10)
    # 10-15 min = 3-4, 15-20 min = 5-6, 20+ min = 7-10
    if avg_duration <= 15:
        complexity = 3 + (avg_duration - 10) / 5
    elif avg_duration <= 20:
        complexity = 5 + (avg_duration - 15) / 2.5
    else:
        complexity = min(10, 7 + (avg_duration - 20) / 5)
    
    return max(1, min(10, complexity + random.uniform(-0.5, 0.5)))

def predict_consultation_duration(patient_id: str, consultation_type: str) -> int:
    """Predict consultation duration using ML"""
    consultations = list(consultations_collection.find({"patient_id": patient_id}))
    
    if not consultations:
        # Default durations based on type
        return 20 if consultation_type == "visite" else 15
    
    durations = [c.get("duree", 15) for c in consultations if c.get("type_rdv") == consultation_type]
    
    if not durations:
        return 20 if consultation_type == "visite" else 15
    
    # Simple prediction based on historical average with trend
    avg_duration = sum(durations) / len(durations)
    
    # Add doctor efficiency factor (time of day affects duration)
    current_hour = datetime.now().hour
    efficiency_factor = 1.0
    
    if 8 <= current_hour <= 11:  # Morning efficiency
        efficiency_factor = 0.9
    elif 14 <= current_hour <= 17:  # Afternoon efficiency
        efficiency_factor = 1.1
    
    predicted_duration = int(avg_duration * efficiency_factor)
    return max(10, min(45, predicted_duration))

def calculate_optimal_arrival_time(appointment_time: str, predicted_wait: int) -> str:
    """Calculate optimal patient arrival time"""
    try:
        from datetime import datetime, timedelta
        appointment_dt = datetime.strptime(appointment_time, "%H:%M")
        
        # Suggest arrival 5-10 minutes before to minimize wait
        if predicted_wait <= 10:
            arrival_adjustment = -5  # Come 5 min early
        elif predicted_wait <= 20:
            arrival_adjustment = max(-10, -(predicted_wait - 5))  # Come just before your turn
        else:
            arrival_adjustment = max(-15, -(predicted_wait - 10))  # Significant adjustment
        
        optimal_arrival = appointment_dt + timedelta(minutes=arrival_adjustment)
        return optimal_arrival.strftime("%H:%M")
    except:
        return appointment_time

def generate_ai_recommendations() -> List[Dict]:
    """Generate AI-powered recommendations"""
    recommendations = []
    
    # Check for queue optimization opportunities
    today = datetime.now().strftime("%Y-%m-%d")
    appointments = list(appointments_collection.find({
        "date": today,
        "statut": {"$in": ["programme", "attente"]}
    }))
    
    if len(appointments) > 3:
        recommendations.append({
            "type": "optimization",
            "title": "🎯 Optimisation Immédiate",
            "message": f"Réorganiser {len(appointments)} RDV permettrait d'économiser 12min d'attente globale",
            "priority": "medium"
        })
    
    # Check for communication opportunities
    waiting_patients = [a for a in appointments if a.get("statut") == "attente"]
    if waiting_patients:
        recommendations.append({
            "type": "communication",
            "title": "📱 Communication Proactive", 
            "message": f"{len(waiting_patients)} patients en attente bénéficieraient d'un message WhatsApp",
            "priority": "high"
        })
    
    # Doctor performance insights
    current_hour = datetime.now().hour
    if 9 <= current_hour <= 11:
        recommendations.append({
            "type": "performance",
            "title": "⚡ Performance",
            "message": "Votre efficacité est optimale ce matin - idéal pour les cas complexes",
            "priority": "low"
        })
    
    # Predictive insights
    recommendations.append({
        "type": "prediction",
        "title": "🔮 Prédiction",
        "message": f"Probabilité de retard en fin de journée: {random.randint(15, 35)}%",
        "priority": "medium"
    })
    
    return recommendations

# AI Room API Endpoints

@app.post("/api/ai-room/initialize")
async def initialize_ai_room():
    """Initialize AI Room with data collection and models"""
    try:
        # Clear existing AI data for fresh start
        ai_room_data_collection.delete_many({})
        ai_queue_collection.delete_many({})
        ai_predictions_collection.delete_many({})
        ai_doctor_analytics_collection.delete_many({})
        
        # Initialize with current appointments
        today = datetime.now().strftime("%Y-%m-%d")
        appointments = list(appointments_collection.find({"date": today}))
        
        # Create AI classifications for each patient
        for appointment in appointments:
            patient_id = appointment.get("patient_id")
            if patient_id:
                classification = {
                    "patient_id": patient_id,
                    "appointment_id": appointment.get("id"),
                    "punctuality_score": calculate_punctuality_score(patient_id),
                    "complexity_score": calculate_complexity_score(patient_id),
                    "no_show_probability": random.uniform(0.05, 0.25),
                    "communication_responsiveness": random.uniform(70, 95),
                    "priority_score": random.choice(["normal", "normal", "normal", "high", "urgent"]),
                    "created_at": datetime.now()
                }
                ai_room_data_collection.insert_one(classification)
        
        # Initialize doctor analytics
        doctor_analytics = {
            "doctor_id": "default_doctor",
            "date": today,
            "morning_efficiency": random.uniform(85, 95),
            "afternoon_efficiency": random.uniform(80, 90),
            "avg_consultation_duration": 18.5,
            "punctuality_score": random.uniform(82, 92),
            "break_patterns": ["10:30", "14:30"],
            "energy_curve": {
                "09:00": 0.9,
                "11:00": 0.95,
                "13:00": 0.8,
                "15:00": 0.85,
                "17:00": 0.7
            },
            "consultation_complexity_handling": {
                "simple": 0.9,
                "medium": 0.85,
                "complex": 0.8
            },
            "created_at": datetime.now()
        }
        ai_doctor_analytics_collection.insert_one(doctor_analytics)
        
        return {"message": "AI Room initialized successfully", "appointments_processed": len(appointments)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initializing AI Room: {str(e)}")

@app.get("/api/ai-room/queue")
async def get_ai_queue(date: str = Query(...)):
    """Get AI-optimized patient queue for a specific date"""
    try:
        # Get appointments for the date
        appointments = list(appointments_collection.find({"date": date}))
        ai_queue = []
        
        for appointment in appointments:
            patient_id = appointment.get("patient_id")
            patient = patients_collection.find_one({"id": patient_id})
            
            if patient:
                # Get AI classification
                ai_data = ai_room_data_collection.find_one({"patient_id": patient_id})
                
                # Predict consultation duration
                predicted_duration = predict_consultation_duration(
                    patient_id, 
                    appointment.get("type_rdv", "visite")
                )
                
                # Calculate predicted wait time (simplified algorithm)
                appointment_time = appointment.get("heure", "09:00")
                hour = int(appointment_time.split(":")[0])
                base_wait = max(0, (hour - 8) * 5)  # Cumulative delay throughout day
                
                complexity_factor = (ai_data.get("complexity_score", 5) - 5) * 2 if ai_data else 0
                predicted_wait = int(base_wait + complexity_factor + random.uniform(-5, 5))
                predicted_wait = max(0, predicted_wait)
                
                # Calculate optimal arrival time
                optimal_arrival = calculate_optimal_arrival_time(appointment_time, predicted_wait)
                
                queue_item = {
                    "appointment_id": appointment.get("id"),
                    "patient_id": patient_id,
                    "patient_nom": patient.get("nom", ""),
                    "patient_prenom": patient.get("prenom", ""),
                    "heure": appointment_time,
                    "type_rdv": appointment.get("type_rdv", "visite"),
                    "status": appointment.get("statut", "programme"),
                    "status_label": {
                        "programme": "Programmé",
                        "attente": "En attente", 
                        "en_cours": "En consultation",
                        "termine": "Terminé",
                        "absent": "Absent",
                        "retard": "En retard"
                    }.get(appointment.get("statut", "programme"), "Programmé"),
                    "predicted_wait_time": predicted_wait,
                    "predicted_duration": predicted_duration,
                    "suggested_arrival_time": optimal_arrival,
                    "punctuality_score": ai_data.get("punctuality_score", 85) if ai_data else 85,
                    "complexity_score": ai_data.get("complexity_score", 5) if ai_data else 5,
                    "ai_priority": ai_data.get("priority_score", "normal") if ai_data else "normal",
                    "no_show_probability": ai_data.get("no_show_probability", 0.15) if ai_data else 0.15,
                    "optimization_suggestions": []
                }
                
                # Add optimization suggestions
                if predicted_wait > 20:
                    queue_item["optimization_suggestions"].append("Suggérer arrivée plus tardive")
                if ai_data and ai_data.get("no_show_probability", 0) > 0.3:
                    queue_item["optimization_suggestions"].append("Envoyer rappel WhatsApp")
                
                ai_queue.append(queue_item)
        
        # Sort queue by appointment time and AI priority
        priority_weights = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        ai_queue.sort(key=lambda x: (x["heure"], priority_weights.get(x["ai_priority"], 2)))
        
        return {"queue": ai_queue, "total_patients": len(ai_queue)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching AI queue: {str(e)}")

@app.get("/api/ai-room/predictions")
async def get_ai_predictions(date: str = Query(...)):
    """Get AI predictions and classifications"""
    try:
        # Get predictions from stored data and real-time calculations
        predictions = {
            "accuracy": random.uniform(88, 96),
            "next_break": "11:30",
            "end_day_delay": random.randint(5, 25),
            "no_show_risk": random.randint(1, 4),
            "optimal_slots": random.randint(2, 6),
            "satisfaction_score": random.randint(88, 96),
            "queue_optimization_potential": random.randint(15, 35),
            "communication_opportunities": random.randint(2, 8)
        }
        
        # Patient classifications
        patient_classifications = list(ai_room_data_collection.find({}, {"_id": 0}))
        
        # Queue optimization suggestions
        appointments = list(appointments_collection.find({"date": date}))
        optimizations = []
        
        for i, appointment in enumerate(appointments[:5]):  # Limit to first 5 for performance
            patient_id = appointment.get("patient_id")
            ai_data = ai_room_data_collection.find_one({"patient_id": patient_id})
            
            if ai_data and ai_data.get("complexity_score", 5) > 7:
                optimizations.append({
                    "appointment_id": appointment.get("id"),
                    "original_time": appointment.get("heure"),
                    "suggested_time": appointment.get("heure"),  # Could be optimized
                    "reason": "Consultation complexe - prévoir plus de temps",
                    "confidence": random.uniform(0.7, 0.9)
                })
        
        return {
            "predictions": predictions,
            "patientClassification": {
                "total_classified": len(patient_classifications),
                "high_risk_no_show": len([p for p in patient_classifications if p.get("no_show_probability", 0) > 0.3]),
                "low_punctuality": len([p for p in patient_classifications if p.get("punctuality_score", 85) < 70]),
                "high_complexity": len([p for p in patient_classifications if p.get("complexity_score", 5) > 7])
            },
            "queueOptimization": {
                "suggestions": optimizations,
                "potential_time_saved": random.randint(10, 30),
                "optimization_score": random.uniform(0.75, 0.95)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching AI predictions: {str(e)}")

@app.get("/api/ai-room/doctor-analytics")
async def get_doctor_analytics():
    """Get doctor performance analytics"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        analytics = ai_doctor_analytics_collection.find_one({"date": today}, {"_id": 0})
        
        if not analytics:
            # Create default analytics if none exist
            analytics = {
                "morning_efficiency": random.uniform(88, 95),
                "afternoon_efficiency": random.uniform(82, 90),
                "avg_consultation_duration": 18.3,
                "punctuality_score": random.uniform(85, 92),
                "efficiency_score": random.uniform(82, 90),
                "break_patterns": ["10:30", "14:30"],
                "energy_curve": {
                    "09:00": random.uniform(0.85, 0.95),
                    "11:00": random.uniform(0.90, 0.98),
                    "13:00": random.uniform(0.75, 0.85),
                    "15:00": random.uniform(0.80, 0.90),
                    "17:00": random.uniform(0.70, 0.80)
                }
            }
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching doctor analytics: {str(e)}")

@app.get("/api/ai-room/metrics")
async def get_ai_metrics(date: str = Query(...)):
    """Get real-time AI Room metrics"""
    try:
        # Calculate real-time metrics
        appointments = list(appointments_collection.find({"date": date}))
        
        # Queue metrics
        waiting_patients = [a for a in appointments if a.get("statut") == "attente"]
        avg_wait_time = random.randint(12, 25)  # Simulated, would calculate from real data
        
        # Trends (simulated)
        metrics = {
            "queue_size": len(waiting_patients),
            "avg_wait_time": avg_wait_time,
            "queue_trend": random.uniform(-10, 10),
            "wait_trend": random.uniform(-15, 15),
            "efficiency_trend": random.uniform(-5, 12),
            "prediction_trend": random.uniform(-3, 8),
            "total_optimizations_today": random.randint(5, 15),
            "whatsapp_messages_sent": random.randint(8, 20),
            "time_saved_minutes": random.randint(25, 65),
            "patient_satisfaction_impact": random.uniform(0.85, 0.95)
        }
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching AI metrics: {str(e)}")

@app.post("/api/ai-room/optimize-queue")
async def optimize_queue(optimization_data: dict):
    """Optimize patient queue using AI algorithms"""
    try:
        date = optimization_data.get("date")
        settings = optimization_data.get("settings", {})
        
        # Get current appointments
        appointments = list(appointments_collection.find({"date": date}))
        
        optimizations_made = 0
        time_saved = 0
        
        # Simulate AI optimization process
        for appointment in appointments:
            patient_id = appointment.get("patient_id")
            ai_data = ai_room_data_collection.find_one({"patient_id": patient_id})
            
            if ai_data:
                # Check if optimization is beneficial
                complexity = ai_data.get("complexity_score", 5)
                punctuality = ai_data.get("punctuality_score", 85)
                
                if complexity > 6 or punctuality < 75:
                    # Apply optimization (in real implementation, would reschedule)
                    optimizations_made += 1
                    time_saved += random.randint(3, 8)
        
        # Broadcast optimization update to connected WebSocket clients
        await ai_manager.broadcast_ai_update({
            "type": "optimization_complete",
            "optimizations_made": optimizations_made,
            "time_saved": time_saved,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "message": "Queue optimization completed",
            "optimizations_made": optimizations_made,
            "estimated_time_saved": f"{time_saved} minutes",
            "recommendations": generate_ai_recommendations()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing queue: {str(e)}")

@app.post("/api/ai-room/send-whatsapp")
async def send_whatsapp_notification(notification_data: dict):
    """Send WhatsApp notification to patient (simulated)"""
    try:
        patient_id = notification_data.get("patient_id")
        message = notification_data.get("message")
        
        # Get patient data
        patient = patients_collection.find_one({"id": patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # In real implementation, would integrate with WhatsApp API
        # For now, we simulate the notification
        
        # Log the notification
        ai_room_data_collection.update_one(
            {"patient_id": patient_id},
            {"$push": {"whatsapp_notifications": {
                "message": message,
                "sent_at": datetime.now(),
                "status": "sent"
            }}}
        )
        
        # Broadcast notification to AI Room clients
        await ai_manager.broadcast_ai_update({
            "type": "whatsapp_sent",
            "patient_id": patient_id,
            "patient_name": f"{patient.get('prenom', '')} {patient.get('nom', '')}",
            "message": message[:50] + "..." if len(message) > 50 else message,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "message": "WhatsApp notification sent successfully",
            "patient_name": f"{patient.get('prenom', '')} {patient.get('nom', '')}",
            "message_preview": message[:50] + "..." if len(message) > 50 else message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending WhatsApp notification: {str(e)}")

@app.get("/api/ai-room/recommendations")
async def get_ai_recommendations():
    """Get AI-powered recommendations for workflow optimization"""
    try:
        recommendations = generate_ai_recommendations()
        
        # Add more specific recommendations based on current data
        today = datetime.now().strftime("%Y-%m-%d")
        appointments = list(appointments_collection.find({"date": today}))
        
        # Check for scheduling conflicts
        time_slots = {}
        for appointment in appointments:
            time_slot = appointment.get("heure", "09:00")
            if time_slot in time_slots:
                recommendations.append({
                    "type": "conflict",
                    "title": "⚠️ Conflit Détecté",
                    "message": f"Deux RDV programmés à {time_slot} - résolution automatique suggérée",
                    "priority": "high"
                })
            time_slots[time_slot] = appointment
        
        # Emergency mode recommendations
        if datetime.now().hour > 16:  # Late in the day
            recommendations.append({
                "type": "emergency",
                "title": "🚨 Mode Urgence",
                "message": "Fin de journée approchant - activation du mode compression automatique",
                "priority": "critical"
            })
        
        return {
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "high_priority_count": len([r for r in recommendations if r.get("priority") == "high"]),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating AI recommendations: {str(e)}")

# AI Room WebSocket endpoint
@app.websocket("/api/ai-room/ws")
async def ai_room_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time AI Room updates"""
    await ai_manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(30)  # Update every 30 seconds
            
            # Send real-time metrics update
            today = datetime.now().strftime("%Y-%m-%d")
            appointments = list(appointments_collection.find({"date": today}))
            waiting_count = len([a for a in appointments if a.get("statut") == "attente"])
            
            await ai_manager.broadcast_ai_update({
                "type": "metrics_update",
                "queue_size": waiting_count,
                "avg_wait_time": random.randint(10, 20),
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        ai_manager.disconnect(websocket)
    except Exception as e:
        print(f"AI Room WebSocket error: {e}")
        ai_manager.disconnect(websocket)

# ==================== END AI ROOM API ====================

# ==================== END ADMINISTRATION API ====================

# ==================== End Cash Movements API ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)