"""
Supabase client for backend authentication operations
"""
from typing import Optional
from supabase import create_client
from config import settings


class SupabaseClient:
    """
    Singleton wrapper for Supabase client with auth operations
    """

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            if settings.supabase_url and settings.supabase_service_key:
                cls._client = create_client(
                    settings.supabase_url,
                    settings.supabase_service_key
                )
        return cls._instance

    @staticmethod
    def get_client():
        """Get the Supabase client instance"""
        if not settings.supabase_url or not settings.supabase_service_key:
            raise ValueError(
                "Supabase credentials not configured. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables."
            )
        return create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )

    @staticmethod
    def verify_session(access_token: str) -> Optional[dict]:
        """
        Verify a Supabase session token and get user info

        Args:
            access_token: The Supabase session token

        Returns:
            User dict if valid, None if invalid
        """
        try:
            client = SupabaseClient.get_client()
            # Verify token by attempting to get user
            user = client.auth.get_user(access_token)
            return user.user.model_dump() if user.user else None
        except Exception:
            return None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[dict]:
        """
        Get user by email (admin operation)

        Args:
            email: The user's email

        Returns:
            User dict if found, None otherwise
        """
        try:
            client = SupabaseClient.get_client()
            response = client.auth.admin.list_users()
            if response:
                for user in response.users:
                    if user.email == email:
                        return user.model_dump()
            return None
        except Exception:
            return None

    @staticmethod
    def create_user(email: str, password: str) -> Optional[dict]:
        """
        Create a new user in Supabase Auth

        Args:
            email: The user's email
            password: The user's password

        Returns:
            User dict if successful, None otherwise
        """
        try:
            client = SupabaseClient.get_client()
            response = client.auth.admin.create_user(
                email=email,
                password=password,
                email_confirm=True  # Auto-confirm for MVP
            )
            return response.user.model_dump() if response.user else None
        except Exception:
            return None

    @staticmethod
    def delete_user(user_id: str) -> bool:
        """
        Delete a user from Supabase Auth

        Args:
            user_id: The Supabase user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            client = SupabaseClient.get_client()
            client.auth.admin.delete_user(user_id)
            return True
        except Exception:
            return False
