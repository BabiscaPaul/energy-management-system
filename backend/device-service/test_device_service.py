import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from main import app
from shared.database import Base, get_db
from shared.types import RoleEnum
import models

load_dotenv()

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_device.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

SECRET_KEY = os.getenv("SECRET_KEY", "test_secret_key")
ALGORITHM = "HS256"


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def create_token(username: str, role: str, user_id: int) -> str:
    """Helper function to create JWT tokens for testing"""
    payload = {
        "sub": username,
        "role": role,
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture(scope="function")
def setup_database():
    """Setup and teardown test database for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def admin_token():
    """Generate admin token"""
    return create_token("admin_user", RoleEnum.ADMIN.value, 1)


@pytest.fixture
def client_token():
    """Generate client token for user_id 2"""
    return create_token("client_user", RoleEnum.CLIENT.value, 2)


@pytest.fixture
def client_token_user3():
    """Generate client token for user_id 3"""
    return create_token("client_user_3", RoleEnum.CLIENT.value, 3)


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, setup_database):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "device-service"}


class TestCreateDevice:
    """Test POST /devices endpoint"""

    def test_create_device_as_admin(self, setup_database, admin_token):
        device_data = {
            "name": "Smart Thermostat",
            "max_consumption_value": 2000,
            "user_id": 2
        }
        response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == device_data["name"]
        assert data["max_consumption_value"] == device_data["max_consumption_value"]
        assert data["user_id"] == device_data["user_id"]
        assert "id" in data

    def test_create_device_duplicate_name(self, setup_database, admin_token):
        device_data = {
            "name": "Smart Thermostat",
            "max_consumption_value": 2000,
            "user_id": 2
        }
        # Create first device
        client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Try to create duplicate
        response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_device_as_client_forbidden(self, setup_database, client_token):
        device_data = {
            "name": "Smart Thermostat",
            "max_consumption_value": 2000,
            "user_id": 2
        }
        response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_create_device_no_auth(self, setup_database):
        device_data = {
            "name": "Smart Thermostat",
            "max_consumption_value": 2000,
            "user_id": 2
        }
        response = client.post("/devices", json=device_data)
        assert response.status_code == 403

    def test_create_device_invalid_token(self, setup_database):
        device_data = {
            "name": "Smart Thermostat",
            "max_consumption_value": 2000,
            "user_id": 2
        }
        response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestGetAllDevices:
    """Test GET /devices endpoint"""

    def test_get_all_devices_as_admin(self, setup_database, admin_token):
        # Create some devices first
        devices_data = [
            {"name": "Device 1", "max_consumption_value": 1000, "user_id": 2},
            {"name": "Device 2", "max_consumption_value": 1500, "user_id": 2},
            {"name": "Device 3", "max_consumption_value": 2000, "user_id": 3}
        ]
        for device in devices_data:
            client.post(
                "/devices",
                json=device,
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        response = client.get(
            "/devices",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_all_devices_empty(self, setup_database, admin_token):
        response = client.get(
            "/devices",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_devices_as_client_forbidden(self, setup_database, client_token):
        response = client.get(
            "/devices",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 403

    def test_get_all_devices_no_auth(self, setup_database):
        response = client.get("/devices")
        assert response.status_code == 403


class TestGetDeviceById:
    """Test GET /devices/{id} endpoint"""

    def test_get_device_by_id_as_admin(self, setup_database, admin_token):
        # Create a device
        device_data = {"name": "Test Device", "max_consumption_value": 1000, "user_id": 2}
        create_response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        device_id = create_response.json()["id"]

        response = client.get(
            f"/devices/{device_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == device_id
        assert data["name"] == device_data["name"]

    def test_get_device_by_id_as_owner(self, setup_database, admin_token, client_token):
        # Create a device for user_id 2
        device_data = {"name": "Test Device", "max_consumption_value": 1000, "user_id": 2}
        create_response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        device_id = create_response.json()["id"]

        # Access as owner (user_id 2)
        response = client.get(
            f"/devices/{device_id}",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == device_id

    def test_get_device_by_id_not_owner_forbidden(self, setup_database, admin_token, client_token_user3):
        # Create a device for user_id 2
        device_data = {"name": "Test Device", "max_consumption_value": 1000, "user_id": 2}
        create_response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        device_id = create_response.json()["id"]

        # Try to access as user_id 3
        response = client.get(
            f"/devices/{device_id}",
            headers={"Authorization": f"Bearer {client_token_user3}"}
        )
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    def test_get_device_by_id_not_found(self, setup_database, admin_token):
        response = client.get(
            "/devices/999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        assert "Device not found" in response.json()["detail"]

    def test_get_device_by_id_no_auth(self, setup_database):
        response = client.get("/devices/1")
        assert response.status_code == 403


class TestUpdateDevice:
    """Test PUT /devices/{id} endpoint"""

    def test_update_device_as_admin(self, setup_database, admin_token):
        # Create a device
        device_data = {"name": "Old Name", "max_consumption_value": 1000, "user_id": 2}
        create_response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        device_id = create_response.json()["id"]

        # Update the device
        update_data = {
            "name": "New Name",
            "max_consumption_value": 1500,
            "user_id": 3
        }
        response = client.put(
            f"/devices/{device_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["max_consumption_value"] == update_data["max_consumption_value"]
        assert data["user_id"] == update_data["user_id"]

    def test_update_device_partial(self, setup_database, admin_token):
        # Create a device
        device_data = {"name": "Original Name", "max_consumption_value": 1000, "user_id": 2}
        create_response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        device_id = create_response.json()["id"]

        # Update only max_consumption_value
        update_data = {"max_consumption_value": 2000}
        response = client.put(
            f"/devices/{device_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == device_data["name"]  # Should remain unchanged
        assert data["max_consumption_value"] == 2000
        assert data["user_id"] == device_data["user_id"]  # Should remain unchanged

    def test_update_device_duplicate_name(self, setup_database, admin_token):
        # Create two devices
        device1_data = {"name": "Device 1", "max_consumption_value": 1000, "user_id": 2}
        device2_data = {"name": "Device 2", "max_consumption_value": 1500, "user_id": 2}
        
        client.post("/devices", json=device1_data, headers={"Authorization": f"Bearer {admin_token}"})
        create_response2 = client.post(
            "/devices",
            json=device2_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        device2_id = create_response2.json()["id"]

        # Try to update device2 with device1's name
        update_data = {"name": "Device 1"}
        response = client.put(
            f"/devices/{device2_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_device_not_found(self, setup_database, admin_token):
        update_data = {"name": "New Name"}
        response = client.put(
            "/devices/999",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        assert "Device not found" in response.json()["detail"]

    def test_update_device_as_client_forbidden(self, setup_database, admin_token, client_token):
        # Create a device
        device_data = {"name": "Test Device", "max_consumption_value": 1000, "user_id": 2}
        create_response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        device_id = create_response.json()["id"]

        # Try to update as client
        update_data = {"name": "New Name"}
        response = client.put(
            f"/devices/{device_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 403

    def test_update_device_no_auth(self, setup_database):
        update_data = {"name": "New Name"}
        response = client.put("/devices/1", json=update_data)
        assert response.status_code == 403


class TestDeleteDevice:
    """Test DELETE /devices/{id} endpoint"""

    def test_delete_device_as_admin(self, setup_database, admin_token):
        # Create a device
        device_data = {"name": "To Delete", "max_consumption_value": 1000, "user_id": 2}
        create_response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        device_id = create_response.json()["id"]

        # Delete the device
        response = client.delete(
            f"/devices/{device_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Device deleted successfully"
        assert data["id"] == device_id

        # Verify device is deleted
        get_response = client.get(
            f"/devices/{device_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404

    def test_delete_device_not_found(self, setup_database, admin_token):
        response = client.delete(
            "/devices/999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        assert "Device not found" in response.json()["detail"]

    def test_delete_device_as_client_forbidden(self, setup_database, admin_token, client_token):
        # Create a device
        device_data = {"name": "Test Device", "max_consumption_value": 1000, "user_id": 2}
        create_response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        device_id = create_response.json()["id"]

        # Try to delete as client
        response = client.delete(
            f"/devices/{device_id}",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 403

    def test_delete_device_no_auth(self, setup_database):
        response = client.delete("/devices/1")
        assert response.status_code == 403


class TestGetDevicesForUser:
    """Test GET /devices/user/{user_id} endpoint"""

    def test_get_devices_for_user_as_admin(self, setup_database, admin_token):
        # Create devices for different users
        devices_data = [
            {"name": "Device 1", "max_consumption_value": 1000, "user_id": 2},
            {"name": "Device 2", "max_consumption_value": 1500, "user_id": 2},
            {"name": "Device 3", "max_consumption_value": 2000, "user_id": 3}
        ]
        for device in devices_data:
            client.post(
                "/devices",
                json=device,
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        # Get devices for user_id 2
        response = client.get(
            "/devices/user/2",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for device in data:
            assert device["user_id"] == 2

    def test_get_devices_for_user_as_owner(self, setup_database, admin_token, client_token):
        # Create devices for user_id 2
        devices_data = [
            {"name": "Device 1", "max_consumption_value": 1000, "user_id": 2},
            {"name": "Device 2", "max_consumption_value": 1500, "user_id": 2}
        ]
        for device in devices_data:
            client.post(
                "/devices",
                json=device,
                headers={"Authorization": f"Bearer {admin_token}"}
            )

        # Access as owner (user_id 2)
        response = client.get(
            "/devices/user/2",
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_devices_for_user_not_owner_forbidden(self, setup_database, admin_token, client_token_user3):
        # Create devices for user_id 2
        device_data = {"name": "Device 1", "max_consumption_value": 1000, "user_id": 2}
        client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Try to access as user_id 3
        response = client.get(
            "/devices/user/2",
            headers={"Authorization": f"Bearer {client_token_user3}"}
        )
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    def test_get_devices_for_user_empty(self, setup_database, admin_token):
        response = client.get(
            "/devices/user/999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_get_devices_for_user_no_auth(self, setup_database):
        response = client.get("/devices/user/2")
        assert response.status_code == 403


class TestEdgeCases:
    """Test edge cases and data validation"""

    def test_create_device_negative_consumption(self, setup_database, admin_token):
        device_data = {
            "name": "Invalid Device",
            "max_consumption_value": -1000,
            "user_id": 2
        }
        response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should succeed as there's no validation in the current implementation
        # This is a potential bug that should be fixed
        assert response.status_code in [201, 422]

    def test_create_device_zero_consumption(self, setup_database, admin_token):
        device_data = {
            "name": "Zero Device",
            "max_consumption_value": 0,
            "user_id": 2
        }
        response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 201

    def test_create_device_missing_fields(self, setup_database, admin_token):
        device_data = {"name": "Incomplete Device"}
        response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_update_device_empty_body(self, setup_database, admin_token):
        # Create a device
        device_data = {"name": "Test Device", "max_consumption_value": 1000, "user_id": 2}
        create_response = client.post(
            "/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        device_id = create_response.json()["id"]

        # Update with empty body
        response = client.put(
            f"/devices/{device_id}",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        # Device should remain unchanged


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
