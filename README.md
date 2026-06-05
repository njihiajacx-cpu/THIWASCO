# THIWASCO SmartWater Platform

THIWASCO SmartWater Platform is a cloud-ready water management ecosystem for Thika, Kenya. It combines a citizen-facing mobile experience, an operations dashboard, incident reporting, GIS infrastructure visibility, billing support, IoT sensor monitoring, and AI-assisted analytics in one integrated solution.

## 1. Project Overview

The platform is designed to solve common water utility challenges such as:

- water shortages and irregular supply
- leakages and pipe bursts
- poor communication with customers
- delayed maintenance response
- illegal connections
- weak visibility into infrastructure
- limited data-driven planning

The goal is to provide a scalable, secure, and production-ready platform that can support current operations and future expansion across counties in Kenya.

## 2. Core Objectives

The system aims to:

- improve water availability and reliability
- support real-time monitoring of water zones and infrastructure
- allow citizens to report incidents quickly
- empower technicians with work order handling
- give managers and executives KPI and analytics visibility
- reduce water losses and improve service responsiveness
- support future multi-tenant expansion for other utilities

## 3. Main Capabilities

### Citizen Experience
- view water availability
- check supply schedules
- report outages, leaks, and illegal connections
- view and pay bills
- receive notifications and updates

### Operations Dashboard
- monitor incidents and work orders
- review infrastructure and GIS layers
- inspect water supply status
- track KPIs and revenue signals

### Field Technician Support
- receive assignments
- navigate to incidents
- upload repair notes and photos
- close work orders

### IoT and Analytics
- ingest sensor data from pressure, flow, tank, and quality systems
- support analytics for leak detection, forecasting, and outage prediction
- provide data for predictive maintenance and decision support

## 4. Architecture Summary

The current implementation includes:

- a FastAPI backend in `backend/`
- a dashboard front end in `backend/web/dashboard/`
- a mobile app placeholder under `mobile/citizen_app/`
- infrastructure and deployment folders under `infrastructure/`
- tests under `tests/`

The backend provides:
- authentication and user management
- water zone status and scheduling
- incident reporting and management
- billing APIs
- GIS asset data
- work orders
- IoT sensor endpoints
- analytics and notifications

## 5. Current Repository Structure

- `backend/` – backend services and dashboard assets
  - `main.py` – FastAPI application entry point
  - `Requirement.txt` – Python dependencies
  - `web/dashboard/` – dashboard UI
- `mobile/` – mobile app source placeholder
- `infrastructure/` – deployment and infrastructure assets
- `tests/` – automated tests
- `run.sh` – startup script for the application

## 6. Running the Project

### Backend

From the repository root:

1. Install dependencies:
   `pip install -r backend/Requirement.txt`

2. Start the backend:
   `python backend/main.py`

3. Open the dashboard:
   `backend/web/dashboard/index.html`

### Quick launch

The project also includes a launcher script:

`./run.sh`

If your shell environment does not support `bash`, run the backend directly with Python as shown above.

## 7. API Highlights

The current API exposes endpoints for:

- authentication (`/auth/login`, `/auth/register`)
- water status (`/water/status/{zone_id}`)
- supply schedules (`/water/schedule/{zone_id}`)
- incident reporting (`/incidents/report`)
- billing (`/billing/current`, `/billing/history`, `/billing/pay`)
- GIS assets (`/gis/assets`, `/gis/pipelines`)
- work orders (`/workorders/assigned`)
- IoT sensors (`/iot/sensors`, `/iot/ingest`)
- analytics (`/analytics/kpis`, `/analytics/demand-forecast`)
- notifications and rewards

## 8. Security and Reliability Considerations

The platform is designed with production-minded practices in mind, including:

- authentication and role-aware access control
- secure password handling
- CORS configuration for API access
- modular API structure for future microservice expansion
- testable backend endpoints for validation

## 9. Future Roadmap

Planned evolution includes:

- full mobile app development for Android and iOS
- dedicated field technician app
- GIS map integration with live infrastructure layers
- IoT device ingestion and time-series analytics
- payment gateway integration
- Kubernetes, Docker, and Terraform deployment automation
- multi-tenant support for additional counties

## 10. Summary

THIWASCO SmartWater Platform is a practical foundation for a modern water utility platform. It is already structured to support citizen engagement, operations visibility, incident response, and future expansion into a full enterprise-grade smart water ecosystem.
