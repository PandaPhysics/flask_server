create user 'snarayan';
create database `bird_watcher`;
grant all privileges on `bird_watcher`.* to 'snarayan'@localhost ;
CREATE TABLE IF NOT EXISTS jobs (task TEXT, arg TEXT, job_id TEXT, timestamp INTEGER, starttime INTEGER, host TEXT, host_id INTEGER, exit_code INTEGER DEFAULT -1);
CREATE TABLE IF NOT EXISTS nodes (host TEXT, lat REAL, lon REAL, id INTEGER PRIMARY KEY AUTO_INCREMENT);
