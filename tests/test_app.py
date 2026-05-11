"""
Tests for the Mergington High School Activities API
Using the AAA (Arrange-Act-Assert) testing pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities(monkeypatch):
    """Reset activities to a known state before each test"""
    # Arrange: Set up test data
    test_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    from src import app as app_module
    monkeypatch.setattr(app_module, "activities", test_activities)
    
    return test_activities


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Verify that all activities are returned from the endpoint"""
        # Arrange
        expected_activity_count = 3
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(data) == expected_activity_count
        for activity_name in expected_activities:
            assert activity_name in data
    
    def test_get_activities_includes_full_activity_details(self, client, reset_activities):
        """Verify that each activity contains all required detail fields"""
        # Arrange
        expected_description = "Learn strategies and compete in chess tournaments"
        expected_schedule = "Fridays, 3:30 PM - 5:00 PM"
        expected_max_participants = 12
        expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        # Assert
        assert chess_club["description"] == expected_description
        assert chess_club["schedule"] == expected_schedule
        assert chess_club["max_participants"] == expected_max_participants
        assert chess_club["participants"] == expected_participants
    
    def test_get_activities_each_activity_has_participants_list(self, client, reset_activities):
        """Verify that each activity has a participants list"""
        # Arrange
        required_fields = ["participants", "description", "schedule", "max_participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in {activity_name}"
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful_for_new_participant(self, client, reset_activities):
        """Verify successful signup adds student to activity"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        expected_message_contains = "Signed up"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert expected_message_contains in response.json()["message"]
        assert new_email in response.json()["message"]
    
    def test_signup_actually_adds_participant_to_activity(self, client, reset_activities):
        """Verify that participant is actually added to the activity's list"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newadd@mergington.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act
        client.post(f"/activities/{activity_name}/signup?email={new_email}")
        verify_response = client.get("/activities")
        updated_participants = verify_response.json()[activity_name]["participants"]
        updated_count = len(updated_participants)
        
        # Assert
        assert new_email in updated_participants
        assert updated_count == initial_count + 1
    
    def test_signup_fails_for_nonexistent_activity(self, client, reset_activities):
        """Verify signup returns 404 for non-existent activity"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        valid_email = "student@mergington.edu"
        expected_status = 404
        expected_error = "Activity not found"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup?email={valid_email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert response.json()["detail"] == expected_error
    
    def test_signup_fails_for_duplicate_student(self, client, reset_activities):
        """Verify duplicate signup is prevented with appropriate error"""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        expected_status = 400
        expected_error = "Student already signed up for this activity"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert response.json()["detail"] == expected_error
    
    def test_signup_allows_student_to_join_multiple_activities(self, client, reset_activities):
        """Verify a student can register for different activities"""
        # Arrange
        student_email = "multiactivity@mergington.edu"
        activity_1 = "Chess Club"
        activity_2 = "Programming Class"
        
        # Act
        response_1 = client.post(f"/activities/{activity_1}/signup?email={student_email}")
        response_2 = client.post(f"/activities/{activity_2}/signup?email={student_email}")
        
        # Verify
        verify_response = client.get("/activities")
        activities = verify_response.json()
        
        # Assert
        assert response_1.status_code == 200
        assert response_2.status_code == 200
        assert student_email in activities[activity_1]["participants"]
        assert student_email in activities[activity_2]["participants"]
    
    def test_signup_handles_special_characters_in_email(self, client, reset_activities):
        """Verify signup works with emails containing special characters"""
        # Arrange
        activity_name = "Gym Class"
        special_email = "john.doe+1@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={special_email}"
        )
        
        # Assert
        assert response.status_code == 200


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""
    
    def test_unregister_successful_for_existing_participant(self, client, reset_activities):
        """Verify successful removal of a participant"""
        # Arrange
        activity_name = "Chess Club"
        participant_email = "michael@mergington.edu"
        expected_message_contains = "Removed"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={participant_email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert expected_message_contains in response.json()["message"]
        assert participant_email in response.json()["message"]
    
    def test_unregister_actually_removes_participant(self, client, reset_activities):
        """Verify participant is actually removed from the activity"""
        # Arrange
        activity_name = "Chess Club"
        participant_email = "michael@mergington.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act
        client.delete(f"/activities/{activity_name}/participants?email={participant_email}")
        verify_response = client.get("/activities")
        updated_participants = verify_response.json()[activity_name]["participants"]
        updated_count = len(updated_participants)
        
        # Assert
        assert participant_email not in updated_participants
        assert updated_count == initial_count - 1
    
    def test_unregister_fails_for_nonexistent_activity(self, client, reset_activities):
        """Verify removal from non-existent activity returns 404"""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        any_email = "student@mergington.edu"
        expected_status = 404
        expected_error = "Activity not found"
        
        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/participants?email={any_email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert response.json()["detail"] == expected_error
    
    def test_unregister_fails_for_nonexistent_participant(self, client, reset_activities):
        """Verify removal of non-existent participant returns 404"""
        # Arrange
        activity_name = "Chess Club"
        nonexistent_email = "notasigned@mergington.edu"
        expected_status = 404
        expected_error = "Participant not found for this activity"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={nonexistent_email}"
        )
        
        # Assert
        assert response.status_code == expected_status
        assert response.json()["detail"] == expected_error
    
    def test_unregister_then_signup_again(self, client, reset_activities):
        """Verify student can re-register after being removed"""
        # Arrange
        activity_name = "Chess Club"
        participant_email = "michael@mergington.edu"
        
        # Act - Remove
        delete_response = client.delete(
            f"/activities/{activity_name}/participants?email={participant_email}"
        )
        
        # Act - Re-register
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={participant_email}"
        )
        
        # Verify
        verify_response = client.get("/activities")
        participants = verify_response.json()[activity_name]["participants"]
        
        # Assert
        assert delete_response.status_code == 200
        assert signup_response.status_code == 200
        assert participant_email in participants


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_signup_and_unregister_workflow(self, client, reset_activities):
        """Verify complete flow: signup, verify change, unregister, verify removal"""
        # Arrange
        activity_name = "Chess Club"
        new_student = "integration@test.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={new_student}"
        )
        mid_response = client.get("/activities")
        mid_count = len(mid_response.json()[activity_name]["participants"])
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/participants?email={new_student}"
        )
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity_name]["participants"])
        
        # Assert
        assert signup_response.status_code == 200
        assert mid_count == initial_count + 1
        assert unregister_response.status_code == 200
        assert final_count == initial_count
    
    def test_root_endpoint_redirects_to_static(self, client):
        """Verify root endpoint redirects to static/index.html"""
        # Arrange
        expected_status = 307
        expected_location = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == expected_status
        assert response.headers["location"] == expected_location
    
    def test_multiple_concurrent_signups(self, client, reset_activities):
        """Verify multiple students can sign up for the same activity"""
        # Arrange
        activity_name = "Gym Class"
        new_students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu",
        ]
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act
        responses = [
            client.post(f"/activities/{activity_name}/signup?email={email}")
            for email in new_students
        ]
        final_response = client.get("/activities")
        final_participants = final_response.json()[activity_name]["participants"]
        
        # Assert
        assert all(response.status_code == 200 for response in responses)
        assert len(final_participants) == initial_count + len(new_students)
        for student in new_students:
            assert student in final_participants
