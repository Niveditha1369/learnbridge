def test_homepage(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"LearnBridge" in response.data
    assert b"Find the Right Tutor for Every Learning Goal" in response.data


def test_about_page(client):
    response = client.get('/about')
    assert response.status_code == 200
    assert b"Our Mission" in response.data


def test_contact_page(client):
    response = client.get('/contact')
    assert response.status_code == 200
    assert b"Get in Touch" in response.data


def test_privacy_page(client):
    response = client.get('/privacy')
    assert response.status_code == 200
    assert b"Privacy Policy" in response.data


def test_terms_page(client):
    response = client.get('/terms')
    assert response.status_code == 200
    assert b"Terms of Service" in response.data


def test_healthz_endpoint(client):
    response = client.get('/healthz')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'healthy'
    assert json_data['database'] == 'connected'


def test_404_error(client):
    response = client.get('/nonexistent-page-route')
    assert response.status_code == 404
    assert b"Page Not Found" in response.data
