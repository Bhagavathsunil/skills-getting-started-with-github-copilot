import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_get_activities_has_required_fields(self):
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_existing_activity(self):
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
    
    def test_signup_for_nonexistent_activity(self):
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_adds_participant_to_list(self):
        # Get initial state
        initial = client.get("/activities").json()
        initial_count = len(initial["Chess Club"]["participants"])
        
        # Sign up
        client.post(
            "/activities/Chess Club/signup?email=unique-test@mergington.edu"
        )
        
        # Verify participant was added
        updated = client.get("/activities").json()
        updated_count = len(updated["Chess Club"]["participants"])
        assert updated_count == initial_count + 1
        assert "unique-test@mergington.edu" in updated["Chess Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self):
        # First, sign up
        email = "remove-me@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
    
    def test_unregister_nonexistent_participant(self):
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_from_nonexistent_activity(self):
        response = client.delete(
            "/activities/Fake Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_removes_participant_from_list(self):
        email = "remove-test@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Programming Class/signup?email={email}")
        
        # Verify added
        activities = client.get("/activities").json()
        assert email in activities["Programming Class"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Programming Class/unregister?email={email}")
        
        # Verify removed
        activities = client.get("/activities").json()
        assert email not in activities["Programming Class"]["participants"]


class TestBusinessLogic:
    """Tests for business logic validation"""
    
    def test_availability_decreases_on_signup(self):
        initial = client.get("/activities").json()
        initial_spots = initial["Gym Class"]["max_participants"] - len(
            initial["Gym Class"]["participants"]
        )
        
        client.post(
            "/activities/Gym Class/signup?email=spots-test@mergington.edu"
        )
        
        updated = client.get("/activities").json()
        updated_spots = updated["Gym Class"]["max_participants"] - len(
            updated["Gym Class"]["participants"]
        )
        
        assert updated_spots == initial_spots - 1
    
    def test_availability_increases_on_unregister(self):
        email = "availability-test@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Tennis Club/signup?email={email}")
        initial = client.get("/activities").json()
        initial_spots = initial["Tennis Club"]["max_participants"] - len(
            initial["Tennis Club"]["participants"]
        )
        
        # Unregister
        client.delete(f"/activities/Tennis Club/unregister?email={email}")
        updated = client.get("/activities").json()
        updated_spots = updated["Tennis Club"]["max_participants"] - len(
            updated["Tennis Club"]["participants"]
        )
        
        assert updated_spots == initial_spots + 1
