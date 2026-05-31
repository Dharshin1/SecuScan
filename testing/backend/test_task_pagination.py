"""
Tests for pagination metadata in tasks list endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from backend.secuscan.main import app
from backend.secuscan.database import init_db

# IMPORTANT: Initialize database before any tests run
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database for testing"""
    import asyncio
    asyncio.run(init_db())

client = TestClient(app)


class TestTasksPagination:
    """Test pagination metadata for /api/v1/tasks endpoint"""

    def test_pagination_has_next_previous_fields(self):
        """Test that next and previous fields exist in response"""
        response = client.get("/api/v1/tasks")

        # Check if we got a response
        if response.status_code == 200:
            data = response.json()
            assert "pagination" in data
            pagination = data["pagination"]

            # These fields should always exist
            assert "next" in pagination
            assert "previous" in pagination
            assert "page" in pagination
            assert "per_page" in pagination
            assert "total_items" in pagination
            assert "total_pages" in pagination
            print("✅ All pagination fields present!")
        else:
            pytest.fail(f"API returned {response.status_code}")

    def test_default_pagination_values(self):
        """Test default page=1, per_page=25"""
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200

        pagination = response.json()["pagination"]
        assert pagination["page"] == 1
        assert pagination["per_page"] == 25
        print(f"✅ Default values: page={pagination['page']}, per_page={pagination['per_page']}")

    def test_custom_per_page(self):
        """Test that per_page parameter is respected"""
        response = client.get("/api/v1/tasks?page=1&per_page=10")
        assert response.status_code == 200

        pagination = response.json()["pagination"]
        assert pagination["per_page"] == 10
        print(f"✅ Custom per_page=10 works")

    def test_first_page_previous_is_null(self):
        """Test that previous is None on first page"""
        response = client.get("/api/v1/tasks?page=1&per_page=10")
        assert response.status_code == 200

        pagination = response.json()["pagination"]
        assert pagination["previous"] is None
        print("✅ First page has previous=None")

    def test_next_url_preserves_filters(self):
        """Test that next URL keeps filter parameters"""
        response = client.get(
            "/api/v1/tasks?page=1&per_page=5&status=completed&plugin_id=nmap"
        )
        assert response.status_code == 200

        data = response.json()
        next_url = data["pagination"]["next"]

        if next_url:  # If there are more pages
            assert "per_page=5" in next_url
            assert "status=completed" in next_url
            assert "plugin_id=nmap" in next_url
            print(f"✅ Next URL preserves filters: {next_url}")
        else:
            print("ℹ️ No next page (database might be empty)")

    def test_reject_negative_page(self):
        """page must be >= 1"""
        response = client.get("/api/v1/tasks?page=-1")

        assert response.status_code == 422

    def test_reject_zero_page(self):
        """page must be >= 1"""
        response = client.get("/api/v1/tasks?page=0")

        assert response.status_code == 422

    def test_reject_zero_per_page(self):
        """per_page must be >= 1"""
        response = client.get("/api/v1/tasks?per_page=0")

        assert response.status_code == 422

    def test_reject_negative_per_page(self):
        """per_page must be >= 1"""
        response = client.get("/api/v1/tasks?per_page=-5")

        assert response.status_code == 422

    def test_reject_oversized_per_page(self):
        """per_page must be <= 100"""
        response = client.get("/api/v1/tasks?per_page=101")

        assert response.status_code == 422

    def test_accept_max_per_page(self):
        """per_page=100 should be accepted"""
        response = client.get("/api/v1/tasks?per_page=100")

        assert response.status_code == 200