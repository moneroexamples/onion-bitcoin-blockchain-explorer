import pytest

from app import app

@pytest.fixture
def testclient():
    return app.test_client()

@pytest.mark.asyncio
async def test_index(testclient):
    response = await testclient.get('/')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_nonexisting(testclient):
    response = await testclient.get('/nonexisting')
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_getblock(testclient):

    # existing block
    response = await testclient.get('/block/111111')
    assert response.status_code == 200

    # non-existing  block
    response = await testclient.get('/block/44444444111111')
    assert "Wrong block_id" in (await response.data).decode()
    assert response.status_code == 200

