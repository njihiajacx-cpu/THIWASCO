from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
import uvicorn
import uuid
import json
import os

# ============================================
# THIWASCO SMARTWATER PLATFORM
# Main Application
# ============================================

app = FastAPI(
    title="THIWASCO SmartWater Platform",
    description="Water Management Ecosystem for Thika, Kenya",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# SECURITY CONFIGURATION
# ============================================
SECRET_KEY = "thiwasco-smartwater-secret-key-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ============================================
# DATA MODELS
# ============================================


class User(BaseModel):
    id: str
    tenant_id: str
    full_name: str
    email: EmailStr
    phone: str
    role: str  # Citizen, Technician, CSAgent, Manager, Executive, Admin
    reward_points: int = 0
    is_active: bool = True


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    role: str = "Citizen"
    tenant_id: str = "thiwasco"


class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]


class Incident(BaseModel):
    id: str
    category: str
    description: str
    latitude: float
    longitude: float
    status: str
    priority: int
    reporter_id: str
    created_at: datetime
    media_urls: List[str] = []


class IncidentCreate(BaseModel):
    category: str
    description: str
    latitude: float
    longitude: float
    media_ids: Optional[List[str]] = []


class WaterStatus(BaseModel):
    zone: str
    current_status: str
    pressure_avg_bar: float
    flow_rate_lps: float
    message: str
    last_updated: datetime


class SupplySchedule(BaseModel):
    zone: str
    schedule: List[Dict[str, Any]]


class Bill(BaseModel):
    id: str
    user_id: str
    period: str
    consumption_m3: float
    amount_due: float
    status: str
    due_date: datetime


class WorkOrder(BaseModel):
    id: str
    incident_id: str
    assigned_technician: str
    status: str
    priority: int
    location: Dict[str, float]
    description: str

# ============================================
# IN-MEMORY DATABASE (Replace with PostgreSQL in production)
# ============================================


class InMemoryDB:
    def __init__(self):
        self.users = {}
        self.incidents = {}
        self.bills = {}
        self.work_orders = {}
        self.technicians = {}
        self.sensor_data = {}

    def seed_data(self):
        """Seed initial test data"""
        # Create test users
        test_user_id = str(uuid.uuid4())
        self.users[test_user_id] = {
            "id": test_user_id,
            "tenant_id": "thiwasco",
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone": "+254700000001",
            "role": "Citizen",
            "hashed_password": pwd_context.hash("password123"),
            "reward_points": 150,
            "is_active": True,
            "created_at": datetime.now()
        }

        # Create technician
        tech_id = str(uuid.uuid4())
        self.users[tech_id] = {
            "id": tech_id,
            "tenant_id": "thiwasco",
            "full_name": "Jane Smith",
            "email": "jane@thiwasco.co.ke",
            "phone": "+254700000002",
            "role": "Technician",
            "hashed_password": pwd_context.hash("password123"),
            "reward_points": 0,
            "is_active": True,
            "created_at": datetime.now()
        }

        # Create manager
        manager_id = str(uuid.uuid4())
        self.users[manager_id] = {
            "id": manager_id,
            "tenant_id": "thiwasco",
            "full_name": "Admin User",
            "email": "admin@thiwasco.co.ke",
            "phone": "+254700000003",
            "role": "Executive",
            "hashed_password": pwd_context.hash("admin123"),
            "reward_points": 0,
            "is_active": True,
            "created_at": datetime.now()
        }

        # Create sample incidents
        for i in range(5):
            inc_id = str(uuid.uuid4())
            self.incidents[inc_id] = {
                "id": inc_id,
                "category": ["Leak", "Burst", "NoWater", "LowPressure", "IllegalConn"][i],
                "description": f"Sample incident {i+1}",
                "latitude": -1.0391 + (i * 0.001),
                "longitude": 37.0695 + (i * 0.001),
                "status": "Pending",
                "priority": i + 1,
                "reporter_id": test_user_id,
                "created_at": datetime.now() - timedelta(hours=i),
                "media_urls": []
            }

        # Create sample bills
        bill_id = str(uuid.uuid4())
        self.bills[bill_id] = {
            "id": bill_id,
            "user_id": test_user_id,
            "period": "2024-01",
            "consumption_m3": 12.5,
            "amount_due": 1250.00,
            "status": "Pending",
            "due_date": datetime.now() + timedelta(days=15)
        }

        # Initialize sensor data for zones
        zones = ["Makongeni", "Kiganjo", "Section9", "Landless"]
        for zone in zones:
            self.sensor_data[zone] = {
                "pressure": 2.5,
                "flow_rate": 150.0,
                "status": "Available",
                "last_updated": datetime.now()
            }


db = InMemoryDB()
db.seed_data()

# ============================================
# AUTHENTICATION FUNCTIONS
# ============================================


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(
        timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None or user_id not in db.users:
            raise credentials_exception
        return db.users[user_id]
    except JWTError:
        raise credentials_exception


def role_checker(allowed_roles: List[str]):
    def check_role(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource"
            )
        return current_user
    return check_role

# ============================================
# API ENDPOINTS
# ============================================


@app.get("/")
async def root():
    return {
        "platform": "THIWASCO SmartWater Platform",
        "version": "1.0.0",
        "status": "operational",
        "services": {
            "auth": "/auth",
            "water": "/water",
            "incidents": "/incidents",
            "billing": "/billing",
            "workorders": "/workorders",
            "gis": "/gis",
            "iot": "/iot"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "users_count": len(db.users),
        "incidents_count": len(db.incidents)
    }

# ============================================
# AUTH ENDPOINTS
# ============================================


@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Find user by email
    user = None
    for u in db.users.values():
        if u["email"] == form_data.username:
            user = u
            break

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token = create_access_token(
        data={
            "user_id": user["id"],
            "tenant_id": user["tenant_id"],
            "role": user["role"],
            "email": user["email"]
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "reward_points": user["reward_points"]
        }
    }


@app.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user exists
    for u in db.users.values():
        if u["email"] == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

    user_id = str(uuid.uuid4())
    new_user = {
        "id": user_id,
        "tenant_id": user_data.tenant_id,
        "full_name": user_data.full_name,
        "email": user_data.email,
        "phone": user_data.phone,
        "role": user_data.role,
        "hashed_password": pwd_context.hash(user_data.password),
        "reward_points": 0,
        "is_active": True,
        "created_at": datetime.now()
    }

    db.users[user_id] = new_user

    return {
        "message": "User registered successfully",
        "user": {
            "id": user_id,
            "full_name": new_user["full_name"],
            "email": new_user["email"],
            "role": new_user["role"]
        }
    }


@app.get("/users/me")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user

# ============================================
# WATER AVAILABILITY ENDPOINTS
# ============================================


@app.get("/water/status/{zone_id}")
async def get_water_status(zone_id: str):
    """Get current water status for a zone"""
    if zone_id not in db.sensor_data:
        raise HTTPException(status_code=404, detail="Zone not found")

    sensor = db.sensor_data[zone_id]
    return {
        "zone": zone_id,
        "current_status": sensor["status"],
        "pressure_avg_bar": sensor["pressure"],
        "flow_rate_lps": sensor["flow_rate"],
        "message": "Water supply is normal" if sensor["status"] == "Available" else "Check schedule",
        "last_updated": sensor["last_updated"].isoformat()
    }


@app.get("/water/schedule/{zone_id}")
async def get_water_schedule(zone_id: str):
    """Get water supply schedule for a zone"""
    schedules = {
        "Makongeni": [
            {"day": "Monday", "from": "06:00", "to": "12:00", "active": True},
            {"day": "Wednesday", "from": "06:00", "to": "12:00", "active": True},
            {"day": "Friday", "from": "06:00", "to": "12:00", "active": True}
        ],
        "Kiganjo": [
            {"day": "Tuesday", "from": "06:00", "to": "12:00", "active": True},
            {"day": "Thursday", "from": "06:00", "to": "12:00", "active": True},
            {"day": "Saturday", "from": "06:00", "to": "12:00", "active": True}
        ],
        "Section9": [
            {"day": "Monday", "from": "14:00", "to": "20:00", "active": True},
            {"day": "Wednesday", "from": "14:00", "to": "20:00", "active": True},
            {"day": "Friday", "from": "14:00", "to": "20:00", "active": True}
        ],
        "Landless": [
            {"day": "Tuesday", "from": "14:00", "to": "20:00", "active": True},
            {"day": "Thursday", "from": "14:00", "to": "20:00", "active": True},
            {"day": "Sunday", "from": "06:00", "to": "12:00", "active": True}
        ]
    }

    if zone_id not in schedules:
        raise HTTPException(status_code=404, detail="Zone not found")

    return {
        "zone": zone_id,
        "schedule": schedules[zone_id]
    }


@app.get("/water/zones")
async def list_zones():
    """List all water supply zones"""
    zones = [
        {"id": "Makongeni", "name": "Makongeni", "population": 50000},
        {"id": "Kiganjo", "name": "Kiganjo", "population": 35000},
        {"id": "Section9", "name": "Section 9", "population": 45000},
        {"id": "Landless", "name": "Landless", "population": 25000}
    ]
    return {"zones": zones}

# ============================================
# INCIDENT REPORTING ENDPOINTS
# ============================================


@app.post("/incidents/report")
async def report_incident(
    incident: IncidentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Report a water-related incident"""

    # AI-like priority assignment
    priority_map = {
        "Burst": 1,
        "NoWater": 1,
        "Contamination": 1,
        "Leak": 2,
        "IllegalConn": 2,
        "LowPressure": 3,
        "MeterFault": 3,
        "Billing": 4
    }

    incident_id = str(uuid.uuid4())
    new_incident = {
        "id": incident_id,
        "category": incident.category,
        "description": incident.description,
        "latitude": incident.latitude,
        "longitude": incident.longitude,
        "status": "Pending",
        "priority": priority_map.get(incident.category, 3),
        "reporter_id": current_user["id"],
        "created_at": datetime.now(),
        "media_urls": []
    }

    db.incidents[incident_id] = new_incident

    # Add reward points for reporting
    current_user["reward_points"] += 10

    return {
        "id": incident_id,
        "status": "Pending",
        "priority": new_incident["priority"],
        "ai_analysis": {
            "duplicate_detected": False,
            "estimated_impact": "Medium",
            "suggested_action": "Dispatch inspection team"
        },
        "reward_earned": 10,
        "message": "Incident reported successfully. Thank you for helping improve water services!"
    }


@app.get("/incidents/nearby")
async def get_nearby_incidents(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    current_user: dict = Depends(get_current_user)
):
    """Get incidents near a location"""
    nearby = []
    for inc in db.incidents.values():
        # Simple distance calculation (in real app, use proper geodesic)
        lat_diff = abs(inc["latitude"] - latitude)
        lon_diff = abs(inc["longitude"] - longitude)
        approx_distance = ((lat_diff ** 2 + lon_diff ** 2)
                           ** 0.5) * 111  # Rough km conversion

        if approx_distance <= radius_km:
            incident_data = {**inc}
            incident_data["distance_km"] = round(approx_distance, 2)
            incident_data["created_at"] = inc["created_at"].isoformat()
            nearby.append(incident_data)

    return sorted(nearby, key=lambda x: x["distance_km"])


@app.get("/incidents/my-reports")
async def get_my_reports(current_user: dict = Depends(get_current_user)):
    """Get incidents reported by current user"""
    my_reports = []
    for inc in db.incidents.values():
        if inc["reporter_id"] == current_user["id"]:
            report_data = {**inc}
            report_data["created_at"] = inc["created_at"].isoformat()
            my_reports.append(report_data)

    return sorted(my_reports, key=lambda x: x["created_at"], reverse=True)


@app.get("/incidents/all")
async def get_all_incidents(
    current_user: dict = Depends(
        role_checker(["Manager", "Executive", "Admin"]))
):
    """Get all incidents (for management)"""
    all_incidents = []
    for inc in db.incidents.values():
        incident_data = {**inc}
        incident_data["created_at"] = inc["created_at"].isoformat()
        all_incidents.append(incident_data)

    return {"total": len(all_incidents), "incidents": all_incidents}


@app.put("/incidents/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    status_update: dict,
    current_user: dict = Depends(role_checker(
        ["Technician", "Manager", "Admin"]))
):
    """Update incident status"""
    if incident_id not in db.incidents:
        raise HTTPException(status_code=404, detail="Incident not found")

    db.incidents[incident_id]["status"] = status_update.get(
        "status", "Pending")

    return {
        "message": "Incident updated",
        "incident": db.incidents[incident_id]
    }

# ============================================
# BILLING ENDPOINTS
# ============================================


@app.get("/billing/current")
async def get_current_bill(current_user: dict = Depends(get_current_user)):
    """Get current bill for user"""
    for bill in db.bills.values():
        if bill["user_id"] == current_user["id"]:
            return {**bill, "due_date": bill["due_date"].isoformat()}

    # Return mock bill if none found
    return {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "period": datetime.now().strftime("%Y-%m"),
        "consumption_m3": 10.5,
        "amount_due": 1050.00,
        "status": "Pending",
        "due_date": (datetime.now() + timedelta(days=15)).isoformat()
    }


@app.get("/billing/history")
async def get_billing_history(current_user: dict = Depends(get_current_user)):
    """Get billing history"""
    history = []
    for i in range(6):
        month = (datetime.now() - timedelta(days=30*i)).strftime("%Y-%m")
        history.append({
            "period": month,
            "consumption_m3": round(10 + i * 0.5, 1),
            "amount_due": round(1000 + i * 50, 2),
            "status": "Paid" if i > 0 else "Pending"
        })

    return {"bills": history}


@app.post("/billing/pay")
async def pay_bill(
    payment: dict,
    current_user: dict = Depends(get_current_user)
):
    """Process bill payment"""
    # Mock payment processing
    payment_methods = {
        "mpesa": "M-Pesa",
        "airtel": "Airtel Money",
        "card": "Credit/Debit Card",
        "bank": "Bank Transfer"
    }

    method = payment.get("method", "mpesa")

    if method not in payment_methods:
        raise HTTPException(status_code=400, detail="Invalid payment method")

    # Update bill status
    for bill in db.bills.values():
        if bill["user_id"] == current_user["id"]:
            bill["status"] = "Paid"
            break

    return {
        "success": True,
        "transaction_id": str(uuid.uuid4()),
        "method": payment_methods[method],
        "amount": payment.get("amount", 1050.00),
        "timestamp": datetime.now().isoformat(),
        "receipt_url": f"https://thiwasco.co.ke/receipts/{uuid.uuid4()}"
    }

# ============================================
# GIS & INFRASTRUCTURE ENDPOINTS
# ============================================


@app.get("/gis/assets")
async def get_water_assets():
    """Get water infrastructure assets for map display"""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [37.0695, -1.0391]
                },
                "properties": {
                    "id": "reservoir-1",
                    "type": "Reservoir",
                    "name": "Thika Main Reservoir",
                    "capacity_m3": 10000,
                    "status": "Active"
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [37.0720, -1.0420]
                },
                "properties": {
                    "id": "pump-1",
                    "type": "Pump Station",
                    "name": "Makongeni Pump Station",
                    "status": "Active"
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [37.0695, -1.0391],
                        [37.0720, -1.0420]
                    ]
                },
                "properties": {
                    "id": "pipe-1",
                    "type": "Pipeline",
                    "diameter_mm": 300,
                    "material": "HDPE",
                    "status": "Active"
                }
            }
        ]
    }


@app.get("/gis/pipelines")
async def get_pipelines():
    """Get pipeline network data"""
    pipelines = [
        {
            "id": f"pipe-{i}",
            "name": f"Pipeline Segment {i}",
            "length_km": round(0.5 + i * 0.3, 2),
            "diameter_mm": [200, 300, 150, 400, 250][i % 5],
            "material": ["HDPE", "PVC", "Steel", "Ductile Iron", "HDPE"][i % 5],
            "age_years": [5, 15, 20, 3, 8][i % 5],
            "status": "Active",
            "coordinates": [
                [37.0695 + i * 0.001, -1.0391 + i * 0.001],
                [37.0695 + (i+1) * 0.001, -1.0391 + (i+1) * 0.001]
            ]
        }
        for i in range(10)
    ]

    return {"total": len(pipelines), "pipelines": pipelines}

# ============================================
# WORK ORDER ENDPOINTS
# ============================================


@app.get("/workorders/assigned")
async def get_assigned_orders(current_user: dict = Depends(get_current_user)):
    """Get work orders assigned to technician"""
    if current_user["role"] != "Technician":
        # Return sample work orders for non-technicians
        return {"work_orders": []}

    # Find unassigned incidents and create work orders
    work_orders = []
    for inc in db.incidents.values():
        if inc["status"] == "Pending":
            work_orders.append({
                "id": str(uuid.uuid4()),
                "incident_id": inc["id"],
                "description": inc["description"],
                "location": {
                    "latitude": inc["latitude"],
                    "longitude": inc["longitude"]
                },
                "priority": inc["priority"],
                "status": "Assigned",
                "assigned_to": current_user["id"],
                "created_at": datetime.now().isoformat()
            })

    return {"work_orders": work_orders}


@app.put("/workorders/{order_id}/complete")
async def complete_workorder(
    order_id: str,
    completion: dict,
    current_user: dict = Depends(role_checker(["Technician"]))
):
    """Complete a work order"""
    # Update associated incident
    incident_id = completion.get("incident_id")
    if incident_id and incident_id in db.incidents:
        db.incidents[incident_id]["status"] = "Resolved"

    return {
        "success": True,
        "message": "Work order completed successfully",
        "timestamp": datetime.now().isoformat()
    }

# ============================================
# IOT & SENSOR DATA ENDPOINTS
# ============================================


@app.get("/iot/sensors")
async def get_sensors():
    """Get all IoT sensors"""
    return {
        "sensors": [
            {"id": "pressure-1", "type": "Pressure",
                "location": "Makongeni", "value": 2.5, "unit": "bar"},
            {"id": "flow-1", "type": "Flow Meter",
                "location": "Main Pipeline", "value": 150, "unit": "L/s"},
            {"id": "level-1", "type": "Tank Level",
                "location": "Main Reservoir", "value": 85, "unit": "%"},
            {"id": "quality-1", "type": "pH Sensor",
                "location": "Treatment Plant", "value": 7.2, "unit": "pH"},
        ]
    }


@app.post("/iot/ingest")
async def ingest_sensor_data(sensor_data: dict):
    """Ingest sensor data (for IoT devices)"""
    sensor_id = sensor_data.get("sensor_id")
    zone = sensor_data.get("zone", "Unknown")

    if zone in db.sensor_data:
        db.sensor_data[zone]["pressure"] = sensor_data.get("pressure", 2.5)
        db.sensor_data[zone]["flow_rate"] = sensor_data.get("flow_rate", 150)
        db.sensor_data[zone]["last_updated"] = datetime.now()

    return {"message": "Data ingested", "sensor_id": sensor_id, "timestamp": datetime.now().isoformat()}

# ============================================
# ANALYTICS & DASHBOARD ENDPOINTS
# ============================================


@app.get("/analytics/kpis")
async def get_kpis(current_user: dict = Depends(role_checker(["Manager", "Executive", "Admin"]))):
    """Get key performance indicators"""
    return {
        "daily_production_m3": 25000,
        "nrw_percentage": 28.5,
        "daily_revenue_kes": 1250000,
        "active_incidents": len([i for i in db.incidents.values() if i["status"] != "Resolved"]),
        "customer_satisfaction": 85,
        "response_time_minutes": 45,
        "collection_rate": 92
    }


@app.get("/analytics/demand-forecast")
async def get_demand_forecast():
    """Get AI-powered demand forecast"""
    return {
        "forecast": [
            {"date": "2024-01-15", "predicted_demand_m3": 22000, "confidence": 0.92},
            {"date": "2024-01-16", "predicted_demand_m3": 23500, "confidence": 0.89},
            {"date": "2024-01-17", "predicted_demand_m3": 21000, "confidence": 0.91},
            {"date": "2024-01-18", "predicted_demand_m3": 24000, "confidence": 0.88},
            {"date": "2024-01-19", "predicted_demand_m3": 25500, "confidence": 0.87},
        ]
    }

# ============================================
# NOTIFICATION ENDPOINTS
# ============================================


@app.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    """Get user notifications"""
    return {
        "notifications": [
            {
                "id": str(uuid.uuid4()),
                "type": "info",
                "title": "Water Supply Update",
                "message": "Water supply will be restored in Makongeni by 6 PM",
                "timestamp": datetime.now().isoformat(),
                "read": False
            },
            {
                "id": str(uuid.uuid4()),
                "type": "warning",
                "title": "Bill Due",
                "message": "Your water bill of KES 1,050 is due in 15 days",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "read": False
            },
            {
                "id": str(uuid.uuid4()),
                "type": "success",
                "title": "Report Received",
                "message": "Your incident report has been received and assigned",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "read": True
            }
        ]
    }

# ============================================
# REWARDS ENDPOINTS
# ============================================


@app.get("/rewards/balance")
async def get_reward_balance(current_user: dict = Depends(get_current_user)):
    """Get reward points balance"""
    return {
        "points": current_user["reward_points"],
        "equivalent_kes": current_user["reward_points"] * 10,
        "recent_earnings": [
            {"description": "Reported water leak", "points": 10,
                "date": datetime.now().isoformat()},
            {"description": "Verified illegal connection", "points": 50,
                "date": (datetime.now() - timedelta(days=7)).isoformat()}
        ]
    }


@app.post("/rewards/redeem")
async def redeem_points(
    redemption: dict,
    current_user: dict = Depends(get_current_user)
):
    """Redeem reward points"""
    points_to_redeem = redemption.get("points", 0)

    if points_to_redeem > current_user["reward_points"]:
        raise HTTPException(status_code=400, detail="Insufficient points")

    current_user["reward_points"] -= points_to_redeem
    bill_credit = points_to_redeem * 10  # 10 KES per point

    return {
        "success": True,
        "points_redeemed": points_to_redeem,
        "bill_credit_kes": bill_credit,
        "remaining_points": current_user["reward_points"]
    }

# ============================================
# MAIN APPLICATION ENTRY POINT
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("  THIWASCO SmartWater Platform v1.0.0")
    print("  Starting server...")
    print("=" * 60)
    print("\n📡 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("👤 Test User: john@example.com / password123")
    print("👨‍💼 Admin User: admin@thiwasco.co.ke / admin123")
    print("\n" + "=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
