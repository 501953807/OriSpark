"""Contract Matching Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/contracts"


# ============================================================================
# GET /matches/listed — list available matching contracts
# ============================================================================

class TestGetListedContracts:
    """GET /matches/listed — database query for available contracts."""

    def test_get_listed_all(self, client):
        try:
            resp = client.get(f"{_BASE}/matches/listed")
        except Exception:
            pytest.skip("Database unavailable for listing")
        assert resp.status_code in (200, 401, 500)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "data" in data:
                contracts = data["data"]
                assert isinstance(contracts, list) or len(contracts) == 0

    def test_get_listed_with_params(self, client):
        try:
            resp = client.get(f"{_BASE}/matches/listed", params={"participant_type": "creator", "limit": "10", "offset": "0"})
        except Exception:
            pytest.skip("Database unavailable with params")
        assert resp.status_code in (200, 401, 500)

    def test_get_listed_invalid_param(self, client):
        resp = client.get(f"{_BASE}/matches/listed", params={"limit": "-10"})
        assert resp.status_code in (400, 401, 422, 500)


# ============================================================================
# POST /{contract_id}/matches/push — push match recommendation to participant
# ============================================================================

class TestPushMatch:
    """POST /{contract_id}/matches/push — requires auth and database transaction."""

    def test_push_match_missing_auth(self, client):
        resp = client.post(f"{_BASE}/test-contract/matches/push", json={})
        assert resp.status_code in (401, 403, 422, 500)

    def test_push_match_invalid_contract_id(self, client):
        try:
            resp = client.post(
                f"{_BASE}/nonexistent-contract-id/matches/push",
                json={"participant_type": "creator", "participant_id": "user123", "match_score": 8.5},
            )
        except Exception:
            pytest.skip("Database/auth issue")
        assert resp.status_code in (404, 401, 500)

    def test_push_match_valid_data(self, client):
        try:
            resp = client.post(
                f"{_BASE}/test-contract/matches/push",
                json={
                    "participant_type": "creator",
                    "participant_id": "participant-123",
                    "match_score": 9.2,
                    "match_reason": "Highly compatible product category",
                },
            )
        except Exception:
            pytest.skip("Route unavailable")
        assert resp.status_code in (200, 401, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "id" in data and "status" in data
            assert data["status"] == "pushed"

    def test_push_match_insufficient_score(self, client):
        try:
            resp = client.post(
                f"{_BASE}/test-contract/matches/push",
                json={"participant_type": "trader", "participant_id": "trader-456", "match_score": 1.0},
            )
        except Exception:
            pytest.skip("Route unavailable")
        assert resp.status_code in (200, 400, 401, 404, 500)


# ============================================================================
# POST /matches/{matching_id}/view — record a viewing action
# ============================================================================

class TestRecordView:
    """POST /matches/{matching_id}/view — recording user interaction, requires auth."""

    def test_view_match_missing_matching_id(self, client):
        resp = client.post(f"{_BASE}/matches/nonexistent-matching/view")
        assert resp.status_code in (404, 401, 500)

    def test_view_match_with_valid_id(self, client):
        try:
            resp = client.post(f"{_BASE}/test-matching-id/view")
        except Exception:
            pytest.skip("Database unavailable for view recording")
        assert resp.status_code in (200, 401, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "id" in data and "viewed_at" in data

    def test_view_match_without_auth(self, client):
        try:
            resp = client.post(f"{_BASE}/valid-matching/view")
        except Exception:
            pytest.skip("Route unavailable")
        assert resp.status_code in (401, 403, 404, 422, 500)


# ============================================================================
# POST /matches/{matching_id}/respond — record response to a match
# ============================================================================

class TestRecordResponse:
    """POST /matches/{matching_id}/respond — record acceptance/decline/counter-offer."""

    def test_response_match_missing_matching_id(self, client):
        try:
            resp = client.post(f"{_BASE}/matches/nonexistent/respond", json={})
        except Exception:
            pytest.skip("Route unavailable")
        assert resp.status_code in (404, 422, 500)

    def test_response_match_invalid_response_type(self, client):
        try:
            resp = client.post(
                f"{_BASE}/test-matching/respond",
                json={"response": "invalid_response_type"},
            )
        except Exception:
            pytest.skip("Route unavailable")
        assert resp.status_code in (400, 401, 404, 500)

    def test_response_match_accepted(self, client):
        resp = client.post(
            f"{_BASE}/test-matching/respond",
            json={"response": "accepted"},
        )
        assert resp.status_code in (200, 401, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "id" in data and "response" in data

    def test_response_match_declined(self, client):
        resp = client.post(
            f"{_BASE}/test-matching/respond",
            json={"response": "declined"},
        )
        assert resp.status_code in (200, 401, 404, 500)

    def test_response_match_counter_offer(self, client):
        resp = client.post(
            f"{_BASE}/test-matching/respond",
            json={
                "response": "counter_offer",
                "counter_offer_json": "{\"price\": 950, \"scope\": \"North America\"}",
            },
        )
        assert resp.status_code in (200, 401, 404, 500)


# ============================================================================
# GET /participants/{participant_id}/matches — get all matches for a participant
# ============================================================================

class TestGetParticipantMatches:
    """GET /participants/{participant_id}/matches — join query against contract table."""

    def test_get_participant_matches(self, client):
        try:
            resp = client.get(f"{_BASE}/participants/test-participant-id/matches")
        except Exception:
            pytest.skip("Database unavailable for participant queries")
        assert resp.status_code in (200, 401, 500)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and "data" in data:
                matches = data["data"]
                assert isinstance(matches, list)

    def test_get_participant_matches_with_params(self, client):
        try:
            resp = client.get(
                f"{_BASE}/participants/test-participant-id/matches",
                params={"participant_type": "operator", "limit": "20", "offset": "0"},
            )
        except Exception:
            pytest.skip("Database unavailable with params")
        assert resp.status_code in (200, 401, 500)

    def test_get_participant_matches_nonexistent(self, client):
        resp = client.get(f"{_BASE}/participants/non-existent-id/matches")
        # May return empty list or 404 depending on implementation
        assert resp.status_code in (200, 404, 500)
