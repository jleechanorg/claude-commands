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
