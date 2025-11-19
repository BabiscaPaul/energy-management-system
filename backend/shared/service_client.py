"""
Service client for internal microservice communication.
Used to maintain data consistency across services.
"""

import httpx
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Internal service URLs
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8002")
DEVICE_SERVICE_URL = os.getenv("DEVICE_SERVICE_URL", "http://localhost:8003")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")


class ServiceClient:
    """Client for internal service-to-service communication"""
    
    @staticmethod
    async def create_user_profile(user_id: int, email: str, full_name: str = "New User") -> Optional[Dict[Any, Any]]:
        """
        Create user profile in user-service after registration.
        This ensures consistency between auth and user databases.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{USER_SERVICE_URL}/users",
                    json={
                        "id": user_id,
                        "full_name": full_name,
                        "email": email,
                        "phone_number": None,
                        "address": None
                    },
                    headers={
                        "X-Internal-Call": "true",
                        "X-User-Role": "admin"  # Internal calls have admin privileges
                    },
                    timeout=10.0
                )
                
                if response.status_code == 201:
                    return response.json()
                else:
                    print(f"Failed to create user profile: {response.status_code} - {response.text}")
                    return None
                    
            except httpx.RequestError as e:
                print(f"Error creating user profile: {str(e)}")
                return None
    
    @staticmethod
    async def delete_user_cascade(user_id: int) -> bool:
        """
        Delete user and all associated data across services.
        Ensures cascade deletion: auth -> devices -> user profile
        """
        success = True
        
        # 1. Delete all user's devices
        async with httpx.AsyncClient() as client:
            try:
                # Get user's devices
                devices_response = await client.get(
                    f"{DEVICE_SERVICE_URL}/devices/user/{user_id}",
                    headers={"X-Internal-Call": "true", "X-User-Role": "admin"},
                    timeout=10.0
                )
                
                if devices_response.status_code == 200:
                    devices = devices_response.json()
                    
                    # Delete each device
                    for device in devices:
                        delete_response = await client.delete(
                            f"{DEVICE_SERVICE_URL}/devices/{device['id']}",
                            headers={"X-Internal-Call": "true", "X-User-Role": "admin"},
                            timeout=10.0
                        )
                        if delete_response.status_code != 200:
                            print(f"Failed to delete device {device['id']}")
                            success = False
                            
            except httpx.RequestError as e:
                print(f"Error deleting user devices: {str(e)}")
                success = False
        
        # 2. Delete user profile
        async with httpx.AsyncClient() as client:
            try:
                profile_response = await client.delete(
                    f"{USER_SERVICE_URL}/users/{user_id}",
                    headers={"X-Internal-Call": "true", "X-User-Role": "admin"},
                    timeout=10.0
                )
                
                if profile_response.status_code != 200:
                    print(f"Failed to delete user profile: {profile_response.status_code}")
                    success = False
                    
            except httpx.RequestError as e:
                print(f"Error deleting user profile: {str(e)}")
                success = False
        
        return success
    
    @staticmethod
    async def update_user_devices_owner(old_user_id: int, new_user_id: int) -> bool:
        """
        Transfer device ownership from one user to another.
        Useful for user migration or admin operations.
        """
        async with httpx.AsyncClient() as client:
            try:
                # Get devices for old user
                devices_response = await client.get(
                    f"{DEVICE_SERVICE_URL}/devices/user/{old_user_id}",
                    headers={"X-Internal-Call": "true", "X-User-Role": "admin"},
                    timeout=10.0
                )
                
                if devices_response.status_code != 200:
                    return False
                
                devices = devices_response.json()
                
                # Update each device's owner
                for device in devices:
                    update_response = await client.put(
                        f"{DEVICE_SERVICE_URL}/devices/{device['id']}",
                        json={"user_id": new_user_id},
                        headers={"X-Internal-Call": "true", "X-User-Role": "admin"},
                        timeout=10.0
                    )
                    
                    if update_response.status_code != 200:
                        print(f"Failed to update device {device['id']} owner")
                        return False
                
                return True
                
            except httpx.RequestError as e:
                print(f"Error updating device ownership: {str(e)}")
                return False
