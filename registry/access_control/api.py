import json
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, Response, Header, Query
from rbac import config
from rbac.access import *
from rbac.db_rbac import DbRBAC
from rbac.models import User

from iam.orm_iam import OrmIAM, secret_key, ALGORITHM
from iam.models import AddOrganization, RegisterUser, UserLogin
from iam.models import UserRole
iam = OrmIAM()

router = APIRouter()
rbac = DbRBAC()
registry_url = config.RBAC_REGISTRY_URL


class ResponseWrapper:
    def __init__(self, data, status='SUCCESS', message='Success'):
        self.status = status
        self.data = data
        self.message = message


def get_current_user(x_token: str = Header(None)):
    if x_token is None:
        raise HTTPException(status_code=400, detail="X-Token header is missing")
    try:
        decoded_token = jwt.decode(x_token, secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        print(jwt.PyJWTError)
        raise HTTPException(status_code=400, detail="Invalid token")
    user_id = decoded_token.get("sub")
    if user_id is None:
        raise HTTPException(status_code=400, detail="User not found in token")
    return user_id


@router.get('/projects', name="Get a list of Project Names [No Auth Required]")
async def get_projects(response: Response) -> list[str]:
    response.status_code, res = check(
        requests.get(url=f"{registry_url}/projects"))
    return res


@router.get('/projects/{project}', name="Get My Project [Read Access Required]")
async def get_project(project: str, response: Response, access: UserAccess = Depends(project_read_access)):
    response.status_code, res = check(requests.get(url=f"{registry_url}/projects/{project}",
                                                   headers=get_api_header(access.user_name)))
    return res


@router.get("/dependent/{entity}", name="Get downstream/dependent entitites for a given entity [Read Access Required]")
def get_dependent_entities(entity: str, access: UserAccess = Depends(project_read_access)):
    response = requests.get(url=f"{registry_url}/dependent/{entity}",
                            headers=get_api_header(access.user_name)).content.decode('utf-8')
    return json.loads(response)


@router.get("/projects/{project}/datasources", name="Get data sources of my project [Read Access Required]")
def get_project_datasources(project: str, response: Response, access: UserAccess = Depends(project_read_access)) -> list:
    response.status_code, res = check(requests.get(url=f"{registry_url}/projects/{project}/datasources",
                                                   headers=get_api_header(access.user_name)))
    return res


@router.get("/projects/{project}/datasources/{datasource}", name="Get a single data source by datasource Id [Read Access Required]")
def get_project_datasource(project: str, datasource: str, response: Response, requestor: UserAccess = Depends(project_read_access)) -> list:
    response.status_code, res = check(requests.get(url=f"{registry_url}/projects/{project}/datasources/{datasource}",
                                                   headers=get_api_header(requestor.user_name)))
    return res


@router.get("/projects/{project}/features", name="Get features under my project [Read Access Required]")
def get_project_features(project: str, response: Response, keyword: Optional[str] = None, access: UserAccess = Depends(project_read_access)) -> list:
    response.status_code, res = check(requests.get(url=f"{registry_url}/projects/{project}/features",
                                                   headers=get_api_header(access.user_name)))
    return res


@router.get("/features/{feature}", name="Get a single feature by feature Id [Read Access Required]")
def get_feature(feature: str, response: Response, requestor: User = Depends(get_user)) -> dict:
    response.status_code, res = check(requests.get(url=f"{registry_url}/features/{feature}",
                                                   headers=get_api_header(requestor.username)))

    feature_qualifiedName = res['attributes']['qualifiedName']
    validate_project_access_for_feature(
        feature_qualifiedName, requestor, AccessType.READ)
    return res


@router.delete("/entity/{entity}", name="Deletes a single entity by qualified name [Write Access Required]")
def delete_entity(entity: str, response: Response, access: UserAccess = Depends(project_write_access)) -> str:
    response.status_code, res = check(requests.delete(
        url=f"{registry_url}/entity/{entity}", headers=get_api_header(access.user_name)))
    return res


@router.get("/features/{feature}/lineage", name="Get Feature Lineage [Read Access Required]")
def get_feature_lineage(feature: str, response: Response, requestor: User = Depends(get_user)) -> dict:
    response.status_code, res = check(requests.get(url=f"{registry_url}/features/{feature}/lineage",
                                                   headers=get_api_header(requestor.username)))

    feature_qualifiedName = res['guidEntityMap'][feature]['attributes']['qualifiedName']
    validate_project_access_for_feature(
        feature_qualifiedName, requestor, AccessType.READ)
    return res


@router.post("/projects", name="Create new project with definition [Auth Required]")
def new_project(definition: dict, response: Response, requestor: User = Depends(get_user)) -> dict:
    rbac.init_userrole(requestor.username, definition["name"])
    response.status_code, res = check(requests.post(url=f"{registry_url}/projects", json=definition,
                                                    headers=get_api_header(requestor.username)))
    return res


@router.post("/projects/{project}/datasources", name="Create new data source of my project [Write Access Required]")
def new_project_datasource(project: str, definition: dict, response: Response, access: UserAccess = Depends(project_write_access)) -> dict:
    response.status_code, res = check(requests.post(url=f"{registry_url}/projects/{project}/datasources", json=definition, headers=get_api_header(
        access.user_name)))
    return res


@router.post("/projects/{project}/anchors", name="Create new anchors of my project [Write Access Required]")
def new_project_anchor(project: str, definition: dict, response: Response, access: UserAccess = Depends(project_write_access)) -> dict:
    response.status_code, res = check(requests.post(url=f"{registry_url}/projects/{project}/anchors", json=definition, headers=get_api_header(
        access.user_name)))
    return res


@router.post("/projects/{project}/anchors/{anchor}/features", name="Create new anchor features of my project [Write Access Required]")
def new_project_anchor_feature(project: str, anchor: str, definition: dict, response: Response, access: UserAccess = Depends(project_write_access)) -> dict:
    response.status_code, res = check(requests.post(url=f"{registry_url}/projects/{project}/anchors/{anchor}/features", json=definition, headers=get_api_header(
        access.user_name)))
    return res


@router.post("/projects/{project}/derivedfeatures", name="Create new derived features of my project [Write Access Required]")
def new_project_derived_feature(project: str, definition: dict, response: Response, access: UserAccess = Depends(project_write_access)) -> dict:
    response.status_code, res = check(requests.post(url=f"{registry_url}/projects/{project}/derivedfeatures",
                                                    json=definition, headers=get_api_header(access.user_name)))
    return res

# Below are access control management APIs


@router.get("/userroles", name="List all active user role records [Project Manage Access Required]")
def get_userroles(requestor: User = Depends(get_user)) -> list:
    return rbac.list_userroles(requestor.username)


@router.post("/users/{user}/userroles/add", name="Add a new user role [Project Manage Access Required]")
def add_userrole(project: str, user: str, role: str, reason: str, access: UserAccess = Depends(project_manage_access)):
    return rbac.add_userrole(access.project_name, user, role, reason, access.user_name)


@router.delete("/users/{user}/userroles/delete", name="Delete a user role [Project Manage Access Required]")
def delete_userrole(user: str, role: str, reason: str, access: UserAccess = Depends(project_manage_access)):
    return rbac.delete_userrole(access.project_name, user, role, reason, access.user_name)


# Below are IAM management APIs


@router.post("/signup", name="Register a new User")
def register_user(user: RegisterUser):
    return ResponseWrapper(iam.signup(user))


@router.post("/login", name="User login")
def register_user(user_login: UserLogin):
    return ResponseWrapper(iam.login(user_login.email, user_login.password))


@router.post("/users/email/check", name="Check Email if exists")
def register_user(email: str):
    return ResponseWrapper(iam.get_user_by_email(email))


@router.post("/organizations", name="Add a new Organization")
def add_organization(organization: AddOrganization):
    return ResponseWrapper(iam.add_organization(organization))


@router.post("/organizations/{organization_id}/invite", name="Invite a User")
def invite_user(organization_id: str, email: str,
                role: UserRole = Query(..., title='role',
                                       enum=UserRole.__members__.values()),
                operator_id: str = Depends(get_current_user)):
    return ResponseWrapper(iam.invite_user(organization_id, email, role, operator_id))


@router.get("/organizations/{organization_id}/users", name="Get all users of organization")
def add_organization(organization_id: str, keyword: str = None,
                     page_size: int = 20, page_no: int = 1,
                     operator_id: str = Depends(get_current_user)):
    return ResponseWrapper(iam.get_users(organization_id, keyword, operator_id, page_size, page_no))


@router.delete("/organizations/{organization_id}/users/{user_id}", name="Remove user from organization")
def delete_organization_user(organization_id: str, user_id: str, operator_id: str = Depends(get_current_user)):
    iam.remove_organization_user(organization_id, user_id, operator_id)
    return ResponseWrapper(True)


@router.delete("/organizations/{organization_id}", name="Delete a organization")
def delete_organization(organization_id: str, operator_id: str = Depends(get_current_user)):
    return ResponseWrapper(iam.delete_organization(organization_id, operator_id))


def check(r):
    return r.status_code, json.loads(r.content.decode("utf-8"))
