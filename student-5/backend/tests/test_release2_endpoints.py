"""Release 2 post-commit tests: two different backend endpoint functions."""
import app


def test_get_spaces_returns_database_records(monkeypatch):
    records=[{'space_id':1,'space_name':'Test Room'}]
    def fake_db(method,path,**kwargs):
        assert method=='GET' and path=='/spaces'
        return 200,records
    monkeypatch.setattr(app,'db_request',fake_db)
    result=app.app.test_client().get('/api/spaces')
    assert result.status_code==200
    assert result.get_json()==records


def test_create_space_posts_valid_payload_to_database_api(monkeypatch):
    def fake_db(method,path,**kwargs):
        assert method=='POST' and path=='/spaces'
        assert kwargs['json']['space_name']=='New Study Room'
        return 201,{'space_id':20,'space_name':'New Study Room'}
    monkeypatch.setattr(app,'db_request',fake_db)
    result=app.app.test_client().post('/api/spaces',json={'space_name':'New Study Room'})
    assert result.status_code==201
    assert result.get_json()['space_id']==20


def test_cloud_baseline_multi_agent_disabled_by_default(monkeypatch):
    import release2
    monkeypatch.setattr(release2,'MULTI_AGENT_MODE',False)
    response=app.app.test_client().post('/api/multi-agent/workflows',json={'query':'Find a space'})
    assert response.status_code==503
    assert response.get_json()['status']=='disabled'
