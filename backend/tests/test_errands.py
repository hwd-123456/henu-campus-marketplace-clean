"""Errand API contract tests (delivery package 03 - Zhang Xian).

Covers the state machine: open -> claimed -> completed,
auth requirements, and the unified field contract.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import create_session_token
from app.core.mongodb import mongo_manager
from app.main import app


pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def clean_errands():
    """Clear errands before each test (teardown runs on a closed loop with
    pytest-asyncio's function-scoped event loops, so we clean up-front)."""
    db = mongo_manager.db
    if db is not None:
        await db["errands"].delete_many({})
    yield


@pytest.fixture
def user_token():
    return create_session_token("user-001", "user001@henu.edu.cn", "Zhang Xian")


@pytest.fixture
def other_token():
    return create_session_token("user-002", "user002@henu.edu.cn", "Other User")


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _create_errand(client, user_token, **overrides):
    payload = {
        "campus": "金明校区",
        "title": "代取快递",
        "origin": "金明校区北门",
        "destination": "生活服务中心",
        "reward": 3,
    }
    payload.update(overrides)
    return await client.post(
        "/api/v1/errands",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"},
    )


class TestCreateErrand:
    async def test_create_returns_open_task_with_contract_fields(self, client, user_token):
        resp = await _create_errand(client, user_token)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        # unified field contract
        for field in ("task_id", "creator_id", "claimer_id", "campus",
                      "title", "origin", "destination", "reward", "status"):
            assert field in body, f"missing contract field {field}"
        assert body["status"] == "open"
        assert body["claimer_id"] is None
        assert body["title"] == "代取快递"
        assert body["reward"] == 3

    async def test_create_requires_auth(self, client):
        resp = await client.post("/api/v1/errands", json={
            "campus": "金明校区", "title": "x", "origin": "a",
            "destination": "b", "reward": 1,
        })
        assert resp.status_code == 401

    async def test_create_rejects_negative_reward(self, client, user_token):
        resp = await _create_errand(client, user_token, reward=-1)
        assert resp.status_code == 422


class TestListErrands:
    async def test_list_returns_created_errand(self, client, user_token):
        await _create_errand(client, user_token, title="列表测试单")
        resp = await client.get("/api/v1/errands")
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        assert any(i["title"] == "列表测试单" for i in items)

    async def test_list_filter_by_status(self, client, user_token):
        await _create_errand(client, user_token, title="筛选用open单")
        resp = await client.get("/api/v1/errands", params={"status": "completed"})
        assert resp.status_code == 200
        assert all(i["status"] == "completed" for i in resp.json())


class TestClaimErrand:
    async def test_claim_open_task_becomes_claimed(self, client, other_token):
        created = (await _create_errand(client, create_session_token(
            "user-001", "u1@henu.edu.cn"), title="待接单")).json()
        resp = await client.post(
            f"/api/v1/errands/{created['task_id']}/claim",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "claimed"
        assert body["claimer_id"] == "user-002"

    async def test_claim_requires_auth(self, client, user_token):
        created = (await _create_errand(client, user_token)).json()
        resp = await client.post(f"/api/v1/errands/{created['task_id']}/claim")
        assert resp.status_code == 401

    async def test_claim_missing_task_404(self, client, user_token):
        resp = await client.post(
            "/api/v1/errands/task-nonexistent/claim",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    async def test_claim_twice_409(self, client, user_token, other_token):
        created = (await _create_errand(client, user_token)).json()
        h = {"Authorization": f"Bearer {other_token}"}
        await client.post(f"/api/v1/errands/{created['task_id']}/claim", headers=h)
        resp = await client.post(f"/api/v1/errands/{created['task_id']}/claim", headers=h)
        assert resp.status_code == 409

    async def test_creator_cannot_claim_own_task(self, client, user_token):
        created = (await _create_errand(client, user_token)).json()
        resp = await client.post(
            f"/api/v1/errands/{created['task_id']}/claim",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 409


class TestCompleteErrand:
    async def _claimed_errand(self, client, user_token, other_token):
        created = (await _create_errand(client, user_token, title="完成流程单")).json()
        await client.post(
            f"/api/v1/errands/{created['task_id']}/claim",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        return created

    async def test_complete_claimed_task_becomes_completed(self, client, user_token, other_token):
        created = await self._claimed_errand(client, user_token, other_token)
        resp = await client.post(
            f"/api/v1/errands/{created['task_id']}/complete",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "completed"

    async def test_complete_requires_auth(self, client, user_token, other_token):
        created = await self._claimed_errand(client, user_token, other_token)
        resp = await client.post(f"/api/v1/errands/{created['task_id']}/complete")
        assert resp.status_code == 401

    async def test_complete_open_task_409(self, client, user_token):
        created = (await _create_errand(client, user_token)).json()
        resp = await client.post(
            f"/api/v1/errands/{created['task_id']}/complete",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 409

    async def test_completed_task_cannot_be_claimed_again(self, client, user_token, other_token):
        created = await self._claimed_errand(client, user_token, other_token)
        await client.post(
            f"/api/v1/errands/{created['task_id']}/complete",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        third = {"Authorization": f"Bearer {create_session_token('user-003', 'u3@henu.edu.cn')}"}
        resp = await client.post(f"/api/v1/errands/{created['task_id']}/claim", headers=third)
        assert resp.status_code == 409

    async def test_third_party_cannot_complete(self, client, user_token, other_token):
        created = await self._claimed_errand(client, user_token, other_token)
        third = {"Authorization": f"Bearer {create_session_token('user-003', 'u3@henu.edu.cn')}"}
        resp = await client.post(f"/api/v1/errands/{created['task_id']}/complete", headers=third)
        assert resp.status_code == 403
