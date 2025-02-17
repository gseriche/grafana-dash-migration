import pytest
from unittest.mock import Mock, patch
from migrate import GrafanaMigrator


@pytest.fixture
def mock_response():
    mock = Mock()
    mock.json.return_value = [
        {
            "id": 1,
            "uid": "abc123",
            "title": "Test Folder",
            "url": "/folders/abc123"
        }
    ]
    return mock


@pytest.fixture
def migrator():
    return GrafanaMigrator(
        source_url="http://source-grafana:3000",
        source_token="source-token",
        target_url="http://target-grafana:3000",
        target_token="target-token"
    )


def test_get_all_folders(migrator, mock_response):
    with patch('requests.get') as mock_get:
        mock_get.return_value = mock_response

        folders = migrator.get_all_folders()

        mock_get.assert_called_once_with(
            'http://source-grafana:3000/api/folders',
            headers={'Authorization': 'Bearer source-token'}
        )

        assert len(folders) == 1
        assert folders[0]['title'] == 'Test Folder'
        assert folders[0]['uid'] == 'abc123'
