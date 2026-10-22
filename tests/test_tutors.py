def test_tutors_directory(client, sample_tutor):
    response = client.get('/tutors')
    assert response.status_code == 200
    assert b"Prof. Sharma" in response.data
    assert b"Expert Math Educator" in response.data
    assert b"1000" in response.data


def test_tutors_filter_by_subject(client, sample_tutor):
    # Filter matching subject
    res_match = client.get('/tutors?subject=Mathematics')
    assert res_match.status_code == 200
    assert b"Prof. Sharma" in res_match.data

    # Filter non-matching subject
    res_nomatch = client.get('/tutors?subject=Zoology')
    assert res_nomatch.status_code == 200
    assert b"No Tutors Match Your Current Filters" in res_nomatch.data


def test_tutor_profile_view(client, sample_tutor):
    tutor_profile_id = sample_tutor[1]
    response = client.get(f'/tutor/{tutor_profile_id}')
    assert response.status_code == 200
    assert b"Prof. Sharma" in response.data
    assert b"Expert Math Educator" in response.data
    assert b"M.Sc. Mathematics" in response.data

    # Privacy check: sensitive info must not be exposed
    assert b"prof.sharma@example.com" not in response.data
    assert b"password_hash" not in response.data


def test_api_tutors(client, sample_tutor):
    response = client.get('/api/tutors')
    assert response.status_code == 200
    data = response.get_json()
    assert 'tutors' in data
    assert len(data['tutors']) >= 1
    assert data['tutors'][0]['headline'] == "Expert Math Educator"
    assert 'password_hash' not in data['tutors'][0]
