from typing import Optional

import jwt
from fastapi import APIRouter, Depends, Response, Header, Query
from pydantic import BaseModel

from rbac import config
from rbac.access import *
from rbac.db_rbac import DbRBAC
from rbac.models import User

from iam.orm_iam import OrmIAM, SECRET_KEY, ALGORITHM
from iam.models import AddOrganization, RegisterUser, UserLogin, CaptchaType, UserResetPassword, OktaLogin, \
    OrganizationUserEdit, EditProjectUsers, UserRole

iam = OrmIAM()

router = APIRouter()
rbac = DbRBAC()
registry_url = config.RBAC_REGISTRY_URL
decoded_token_user_key = "sub"


class ResponseWrapper(BaseModel):
    data: Union[list[dict], dict, list[str]]
    status: str = 'SUCCESS'
    message: str = 'Success'


def get_current_user(x_token: str = Header(None)):
    if not x_token:
        raise HTTPException(status_code=400, detail="X-Token header is missing")
    try:
        decoded_token = jwt.decode(x_token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        print(jwt.PyJWTError)
        raise HTTPException(status_code=400, detail="Invalid token")
    user_id = decoded_token.get(decoded_token_user_key)
    if not user_id:
        raise HTTPException(status_code=400, detail="User not found in token")
    return user_id



@router.post("/organizations/{organization_id}/projects/{project_id}", name="Edit users of project")
def new_project(organization_id: str, project_id: str,
                edit_project_user: EditProjectUsers,
                operator_id: str = Depends(get_current_user)) -> dict:
    iam.edit_project_users(organization_id, project_id, edit_project_user, operator_id)
    return True


@router.get('/organizations/{organization_id}/projects', name="Get a list of Project Names [No Auth Required]")
async def get_projects(response: Response, organization_id: str,
                       operator_id: str = Depends(get_current_user)):
    """If the user is an administrator, retrieve all data directly. If the user is a user and has no projects,
    return empty array"""
    project_ids = iam.get_user_projects(organization_id, operator_id)
    if len(project_ids) == 0:
        return ResponseWrapper(data=[])
    response.status_code, res = check(
        requests.get(url=f"{registry_url}/projects", params={'ids': project_ids}))
    iam.get_projects_users(organization_id, res)
    result = ResponseWrapper(data=res)
    return result


@router.get('/organizations/{organization_id}/projects/{project}', name="Get My Project [Read Access Required]")
async def get_project(organization_id: str, project: str, response: Response,
                      operator_id: str = Depends(get_current_user)):
    iam.check_organization_user_access(organization_id, operator_id)

    response.status_code, res = check(requests.get(url=f"{registry_url}/projects/{project}"))
    return res


@router.get("/dependent/{entity}", name="Get downstream/dependent entitites for a given entity [Read Access Required]")
def get_dependent_entities(entity: str, operator_id: str = Depends(get_current_user)):
    response = requests.get(url=f"{registry_url}/dependent/{entity}",
                            headers=get_api_header(access.user_name)).content.decode('utf-8')
    return json.loads(response)


@router.get("/projects/{project}/datasources", name="Get data sources of my project [Read Access Required]")
def get_project_datasources(project: str, response: Response,
                            access: UserAccess = Depends(project_read_access)) -> list:
    response.status_code, res = check(requests.get(url=f"{registry_url}/projects/{project}/datasources",
                                                   headers=get_api_header(access.user_name)))
    return res


@router.get("/projects/{project}/datasources/{datasource}",
            name="Get a single data source by datasource Id [Read Access Required]")
def get_project_datasource(project: str, datasource: str, response: Response,
                           requestor: UserAccess = Depends(project_read_access)) -> list:
    response.status_code, res = check(requests.get(url=f"{registry_url}/projects/{project}/datasources/{datasource}",
                                                   headers=get_api_header(requestor.user_name)))
    return res


@router.get("/projects/{project}/features", name="Get features under my project [Read Access Required]")
def get_project_features(project: str, response: Response, keyword: Optional[str] = None,
                         access: UserAccess = Depends(project_read_access)) -> list:
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
def new_project(definition: dict, response: Response, operator_id: str = Depends(get_current_user)) -> dict:
    response.status_code, res = check(requests.post(url=f"{registry_url}/projects", json=definition))
    organization_id = ''
    if response.status_code == 200:
        iam.add_project_user(organization_id, operator_id, res['guid'], UserRole.ADMIN)
    return res


@router.post("/projects/{project}/datasources", name="Create new data source of my project [Write Access Required]")
def new_project_datasource(project: str, definition: dict, response: Response,
                           access: UserAccess = Depends(project_write_access)) -> dict:
    response.status_code, res = check(
        requests.post(url=f"{registry_url}/projects/{project}/datasources", json=definition, headers=get_api_header(
            access.user_name)))
    return res


@router.post("/projects/{project}/anchors", name="Create new anchors of my project [Write Access Required]")
def new_project_anchor(project: str, definition: dict, response: Response,
                       access: UserAccess = Depends(project_write_access)) -> dict:
    response.status_code, res = check(
        requests.post(url=f"{registry_url}/projects/{project}/anchors", json=definition, headers=get_api_header(
            access.user_name)))
    return res


@router.post("/projects/{project}/anchors/{anchor}/features",
             name="Create new anchor features of my project [Write Access Required]")
def new_project_anchor_feature(project: str, anchor: str, definition: dict, response: Response,
                               access: UserAccess = Depends(project_write_access)) -> dict:
    response.status_code, res = check(
        requests.post(url=f"{registry_url}/projects/{project}/anchors/{anchor}/features", json=definition,
                      headers=get_api_header(
                          access.user_name)))
    return res


@router.post("/projects/{project}/derivedfeatures",
             name="Create new derived features of my project [Write Access Required]")
def new_project_derived_feature(project: str, definition: dict, response: Response,
                                access: UserAccess = Depends(project_write_access)) -> dict:
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

@router.post("/captcha/send")
def send_captcha(email: str, type: CaptchaType = Query(..., title='type',
                                                       enum=CaptchaType.__members__.values())):
    iam.send_captcha(email, type)
    return ResponseWrapper(data=True)


@router.post("/signup", name="Register a new User")
def register_user(user: RegisterUser):
    return ResponseWrapper(data=iam.signup(user))


@router.post("/okta/login", name="Okta login")
def register_user(okta_login: OktaLogin):
    return ResponseWrapper(data=iam.okta_login(okta_login.code, okta_login.redirect_uri))


@router.post("/login", name="User login")
def register_user(user_login: UserLogin):
    return ResponseWrapper(data=iam.login(user_login.email, user_login.password))


@router.post("/reset-password", name="Reset Password")
def reset_password(user_reset_password: UserResetPassword):
    iam.reset_password(user_reset_password.email, user_reset_password.new_password,
                       user_reset_password.captcha)
    return ResponseWrapper(data=True)


@router.post("/users/email/check", name="Check if email exists")
def register_user(email: str):
    return ResponseWrapper(data=iam.get_user_by_email(email))


@router.post("/organizations", name="Add a new Organization")
def add_organization(organization: AddOrganization):
    return ResponseWrapper(data=iam.add_organization(organization))


@router.post("/organizations/{organization_id}/invite", name="Invite a User")
def invite_user(organization_id: str, email: str,
                role: UserRole = Query(..., title='role',
                                       enum=UserRole.__members__.values()),
                operator_id: str = Depends(get_current_user)):
    return ResponseWrapper(data=iam.invite_user(organization_id, email, role, operator_id))


@router.get("/organizations/{organization_id}/users", name="Get all users of organization")
def get_organization_users(organization_id: str, keyword: str = None,
                           page_size: int = 20, page_no: int = 1,
                           operator_id: str = Depends(get_current_user)):
    return ResponseWrapper(data=iam.get_users(organization_id, keyword, operator_id, page_size, page_no))


@router.post("/organizations/{organization_id}/users/{user_id}", name="Edit user from organization")
def edit_organization_user(organization_id: str, user_id: str, edit_user: OrganizationUserEdit,
                             operator_id: str = Depends(get_current_user)):
    iam.edit_organization_user(organization_id, user_id, edit_user, operator_id)
    return ResponseWrapper(data=True)


@router.delete("/organizations/{organization_id}/users/{user_id}", name="Remove user from organization")
def delete_organization_user(organization_id: str, user_id: str, operator_id: str = Depends(get_current_user)):
    iam.remove_organization_user(organization_id, user_id, operator_id)
    return ResponseWrapper(data=True)


@router.delete("/organizations/{organization_id}", name="Delete an organization")
def delete_organization(organization_id: str, operator_id: str = Depends(get_current_user)):
    return ResponseWrapper(data=iam.delete_organization(organization_id, operator_id))


def check(r):
    return r.status_code, json.loads(r.content.decode("utf-8"))
