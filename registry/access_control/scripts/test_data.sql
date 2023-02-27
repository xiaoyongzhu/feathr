insert into userroles (project_name, user_name, role_name, create_by, create_reason, create_time) values ('global', 'abc@microsoft.com','admin', 'test_data@microsoft.com', 'test data',  getutcdate())
insert into userroles (project_name, user_name, role_name, create_by, create_reason, create_time) values ('global', 'efg@microsoft.com','admin', 'test_data@microsoft.com', 'test data',  getutcdate())
insert into userroles (project_name, user_name, role_name, create_by, create_reason, create_time) values ('feathr_ci_registry_12_33_182947', 'efg@microsoft.com','admin','test_data@microsoft.com',  'test data',  getutcdate())
insert into userroles (project_name, user_name, role_name, create_by, create_reason, create_time) values ('feathr_ci_registry_12_33_182947', 'hij@microsoft.com','consumer', 'test_data@microsoft.com', 'test data',  getutcdate())


INSERT INTO organizations (id, name, create_time, update_time, remark, status) VALUES ('a1ccf112-3367-4c13-8c38-b4a8555497c2', 'org_feathr6', '2023-02-09 08:52:43.423', '2023-02-09 08:52:43.423', 'This is a inner test organization', 'ACTIVE');
INSERT INTO users (id, email, password, create_time, update_time, status) VALUES ('eacb8307-6e2b-4b8e-abbd-67c5ef7acb79', 'maioria@163.com', '8bb0cf6eb9b17d0f7d22b456f121257dc1254e1f01665370476383ea776df414', '2023-02-14 06:33:35.757', '2023-02-14 06:33:35.757', 'ACTIVE');
INSERT INTO organization_user (id, organization_id, user_id, role, create_time) VALUES ('23bf0a86-14e0-43e8-88b2-0f08f0de90ad', 'a1ccf112-3367-4c13-8c38-b4a8555497c2', 'eacb8307-6e2b-4b8e-abbd-67c5ef7acb79', 'ADMIN', '2023-02-16 03:14:28.340');

