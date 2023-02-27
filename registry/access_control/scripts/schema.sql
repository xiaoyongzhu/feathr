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

create table captcha
(
	id varchar(50) not null
		constraint captcha_pk
			primary key nonclustered,
	receiver varchar(64) not null,
	type varchar(32) not null,
	code varchar(10) not null,
	status varchar(32) not null,
	create_time datetime not null
)

CREATE TABLE users (
  id VARCHAR(50) NOT NULL,
  email VARCHAR(50) NOT NULL,
  password VARCHAR(64) NULL,
  phone VARCHAR(50) NULL,
  status VARCHAR(50) NULL,
  create_time DATETIME NOT NULL,
  update_time DATETIME NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT email_UNIQUE UNIQUE (email ASC));

create table sso_users
(
	id varchar(50) not null
		constraint sso_user_pk
			primary key nonclustered,
	sso_user_id varchar(128) not null,
	sso_email varchar(128) null,
	user_id varchar(50) not null,
	platform varchar(50) not null,
	access_token varchar(1024),
	source_str varchar(1024),
	create_time datetime not null,
	update_time datetime not null
)

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
  organization_id VARCHAR(50) NOT NULL,
  project_id VARCHAR(50) NOT NULL,
  user_id VARCHAR(50) NOT NULL,
  role VARCHAR(50) NOT NULL,
  create_time DATETIME NOT NULL,
  PRIMARY KEY (id));