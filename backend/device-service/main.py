import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
from shared.database import engine, get_db

from shared.types import RoleEnum
import shared.utils as utils

import schemas

# POST   /devices          - Create device (Admin only)
# GET    /devices          - Get all devices (Admin only)
# GET    /devices/{id}     - Get device by ID (owner or admin)
# PUT    /devices/{id}     - Update device (Admin only)
# DELETE /devices/{id}     - Delete device (Admin only)
# GET    /devices/user/{user_id} - Get devices for a user (Client sees their own)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Device Service")

@app.get("/health")
def health():
    return {"status": "healthy", "service": "device-service"}

@app.post("/devices", response_model=schemas.DeviceResponse, status_code=status.HTTP_201_CREATED)
def create_device(
    device_in: schemas.DeviceCreate,
    current_user: dict = Depends(utils.require_admin),
    db: Session = Depends(get_db)
):
    existing_device = db.query(models.Device).filter(models.Device.name == device_in.name).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="Device with this name already exists")

    new_device = models.Device(
        name=device_in.name,
        max_consumption_value=device_in.max_consumption_value,
        user_id=device_in.user_id,
    )

    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device

@app.get("/devices")
def get_all_devices(
    current_user: dict = Depends(utils.require_admin),
    db: Session = Depends(get_db)
):
    devices = db.query(models.Device).all()
    return devices

@app.get("/devices/{id}", response_model=schemas.DeviceResponse)
def get_device(
    id: int,
    current_user: dict = Depends(utils.get_current_user),
    db: Session = Depends(get_db)
):
    device = db.query(models.Device).filter(models.Device.id == id).first()

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    # Allow admin or the device owner to view
    if current_user["role"] != RoleEnum.ADMIN.value and current_user["user_id"] != device.user_id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own devices.")

    return device

@app.put("/devices/{id}", response_model=schemas.DeviceResponse, status_code=status.HTTP_200_OK)
def update_device(
    id: int,
    device_in: schemas.DeviceUpdate,
    current_user: dict = Depends(utils.require_admin),
    db: Session = Depends(get_db)
):
    device = db.query(models.Device).filter(models.Device.id == id).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    if device_in.name and device_in.name != device.name:
        existing_device = db.query(models.Device).filter(
            models.Device.name == device_in.name,
            models.Device.id != id,
        ).first()
        if existing_device:
            raise HTTPException(status_code=400, detail="Device with this name already exists")

    if device_in.name is not None:
        device.name = device_in.name
    if device_in.max_consumption_value is not None:
        device.max_consumption_value = device_in.max_consumption_value
    if device_in.user_id is not None:
        device.user_id = device_in.user_id

    db.commit()
    db.refresh(device)
    return device

@app.delete("/devices/{id}", status_code=status.HTTP_200_OK)
def delete_device(
    id: int,
    current_user: dict = Depends(utils.require_admin),
    db: Session = Depends(get_db)
):
    """Delete device (Admin only)"""
    device = db.query(models.Device).filter(models.Device.id == id).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()

    return {"message": "Device deleted successfully", "id": id}

@app.get("/devices/user/{user_id}")
def get_devices_for_user(
    user_id: int,
    current_user: dict = Depends(utils.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != RoleEnum.ADMIN.value and current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own devices.")

    devices = db.query(models.Device).filter(models.Device.user_id == user_id).all()
    return devices
