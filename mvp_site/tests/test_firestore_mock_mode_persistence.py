from __future__ import annotations

import os

from mvp_site import firestore_service


def test_mock_services_mode_get_db_is_singleton(monkeypatch):
    monkeypatch.setenv("MOCK_SERVICES_MODE", "true")

    db1 = firestore_service.get_db()
    db2 = firestore_service.get_db()

    assert db1 is db2


def test_mock_services_mode_persists_documents(monkeypatch):
    monkeypatch.setenv("MOCK_SERVICES_MODE", "true")

    db = firestore_service.get_db()
    doc = (
        db.collection("users")
        .document("u1")
        .collection("campaigns")
        .document("c1")
    )
    doc.set({"ok": True})

    # New get_db() call should see same document.
    db2 = firestore_service.get_db()
    doc2 = (
        db2.collection("users")
        .document("u1")
        .collection("campaigns")
        .document("c1")
        .get()
    )

    assert doc2.exists
    assert doc2.to_dict()["ok"] is True


def test_update_campaign_dot_notation(monkeypatch):
    """Test that update_campaign correctly handles dot-notation paths.

    This is the core fix for the issue where dot-notation updates like
    'game_state.custom_campaign_state.arc_milestones.wedding_tour' were
    creating literal field names instead of nested structures.
    """
    monkeypatch.setenv("MOCK_SERVICES_MODE", "true")
    # Reset mock singleton to get clean state
    firestore_service.reset_mock_firestore()

    db = firestore_service.get_db()
    user_id = "test_user"
    campaign_id = "test_campaign"

    # Create initial campaign document with nested structure
    doc = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
    )
    doc.set({
        "title": "Test Campaign",
        "game_state": {
            "custom_campaign_state": {
                "arc_milestones": {}
            }
        }
    })

    # Update using dot-notation (the problematic case from the issue)
    updates = {
        "game_state.custom_campaign_state.arc_milestones.wedding_tour": {
            "status": "completed",
            "phase": "ceremony_complete"
        }
    }

    # Call the function under test
    result = firestore_service.update_campaign(user_id, campaign_id, updates)
    assert result is True

    # Verify the update was applied correctly as nested structure
    updated_doc = doc.get()
    data = updated_doc.to_dict()

    # The dot-notation should have been expanded to nested dicts
    assert "game_state" in data
    assert "custom_campaign_state" in data["game_state"]
    assert "arc_milestones" in data["game_state"]["custom_campaign_state"]
    assert "wedding_tour" in data["game_state"]["custom_campaign_state"]["arc_milestones"]

    wedding_tour = data["game_state"]["custom_campaign_state"]["arc_milestones"]["wedding_tour"]
    assert wedding_tour["status"] == "completed"
    assert wedding_tour["phase"] == "ceremony_complete"
    assert data["title"] == "Test Campaign"


def test_update_campaign_without_dot_notation(monkeypatch):
    """Test that update_campaign still works for regular (non-dot-notation) updates."""
    monkeypatch.setenv("MOCK_SERVICES_MODE", "true")
    # Reset mock singleton to get clean state
    firestore_service.reset_mock_firestore()

    db = firestore_service.get_db()
    user_id = "test_user2"
    campaign_id = "test_campaign2"

    # Create initial campaign document
    doc = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
    )
    doc.set({"title": "Original Title", "status": "active"})

    # Update using simple keys (no dots)
    updates = {
        "title": "Updated Title",
        "status": "completed"
    }

    result = firestore_service.update_campaign(user_id, campaign_id, updates)
    assert result is True

    # Verify the update was applied correctly
    updated_doc = doc.get()
    data = updated_doc.to_dict()

    assert data["title"] == "Updated Title"
    assert data["status"] == "completed"


def test_update_campaign_dot_notation_existing_nested(monkeypatch):
    """Test that dot-notation updates merge into existing nested fields."""
    monkeypatch.setenv("MOCK_SERVICES_MODE", "true")
    firestore_service.reset_mock_firestore()

    db = firestore_service.get_db()
    user_id = "test_user3"
    campaign_id = "test_campaign3"

    doc = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
    )
    doc.set({
        "title": "Existing Campaign",
        "game_state": {
            "custom_campaign_state": {
                "arc_milestones": {
                    "wedding_tour": {"status": "in_progress"}
                }
            }
        },
    })

    updates = {
        "game_state.custom_campaign_state.arc_milestones.wedding_tour": {
            "status": "completed",
            "phase": "ceremony_complete",
        }
    }

    result = firestore_service.update_campaign(user_id, campaign_id, updates)
    assert result is True

    updated_doc = doc.get()
    data = updated_doc.to_dict()
    wedding_tour = data["game_state"]["custom_campaign_state"]["arc_milestones"]["wedding_tour"]

    assert data["title"] == "Existing Campaign"
    assert wedding_tour == {
        "status": "completed",
        "phase": "ceremony_complete",
    }
