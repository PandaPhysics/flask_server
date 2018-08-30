CREATE user 'snarayan';
CREATE database `bird_watcher`;
GRANT all privileges ON  `bird_watcher`.* TO 'snarayan'@localhost ;
CREATE TABLE IF NOT EXISTS jobs (task TEXT, arg TEXT, job_id TEXT, timestamp INTEGER, starttime INTEGER, host TEXT, host_id INTEGER, exit_code INTEGER DEFAULT -1, id INTEGER PRIMARY KEY AUTO_INCREMENT);
CREATE TABLE IF NOT EXISTS nodes (host TEXT, lat REAL, lon REAL, id INTEGER PRIMARY KEY AUTO_INCREMENT);
CREATE TABLE IF NOT EXISTS files (path TEXT, last_access INTEGER, mbytes INTEGER); 
