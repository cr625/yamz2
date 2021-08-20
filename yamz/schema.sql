DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS term;
CREATE TABLE user (
    id SERIAL PRIMARY KEY NOT NULL,
    authority VARCHAR(64) NOT NULL,
    auth_id VARCHAR(64) NOT NULL,
    email VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    first_name VARCHAR(64) NOT NULL,
    reputation INTEGER default 1 NOT NULL,
    enotify BOOLEAN default true,
    super_user BOOLEAN default false,
    UNIQUE (email)
);
CREATE TABLE term (
    id SERIAL PRIMARY KEY NOT NULL,
    owner_id INTEGER DEFAULT 0 NOT NULL,
    term_string TEXT NOT NULL,
    def TEXT NOT NULL,
    examples TEXT NOT NULL,
    concept_id VARCHAR(64) DEFAULT NULL,
    persistent_id TEXT
);