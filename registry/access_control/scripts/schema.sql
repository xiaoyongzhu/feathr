create table userroles
(
    record_id int IDENTITY(1,1), 
    project_name varchar(50) not null,
    user_name varchar(50) not null,
    role_name varchar(50) not null,
    create_by varchar(50) not null,
    create_reason varchar(50) not null,
    create_time datetime not null,
    delete_by varchar(50),
    delete_reason varchar(50),
    delete_time datetime,
);

CREATE TABLE users (
  id VARCHAR(50) NOT NULL,
  email VARCHAR(50) NOT NULL,
  password VARCHAR(64) NOT NULL,
  phone VARCHAR(50) NULL,
  status VARCHAR(50) NULL,
  create_time DATETIME NOT NULL,
  update_time DATETIME NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT email_UNIQUE UNIQUE (email ASC));

CREATE TABLE organizations (
  id VARCHAR(50) NOT NULL,
  name VARCHAR(50) NOT NULL,
  remark VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL,
  create_time DATETIME NOT NULL,
  update_time DATETIME NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT name_UNIQUE UNIQUE (name ASC));

CREATE TABLE organization_user (
  id VARCHAR(50) NOT NULL,
  organization_id VARCHAR(50) NOT NULL,
  user_id VARCHAR(50) NOT NULL,
  role VARCHAR(50) NULL,
  create_time DATETIME NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT organization_user_UNIQUE UNIQUE (organization_id ASC, user_id ASC) );

CREATE TABLE project_user (
  id VARCHAR(50) NOT NULL,
  project_id VARCHAR(50) NOT NULL,
  user_id VARCHAR(50) NOT NULL,
  role VARCHAR(50) NOT NULL,
  create_time DATETIME NOT NULL,
  PRIMARY KEY (id));