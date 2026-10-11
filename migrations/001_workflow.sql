ALTER TABLE person ADD COLUMN active TINYINT NOT NULL DEFAULT 1;
ALTER TABLE work ADD COLUMN version INT NOT NULL DEFAULT 1;
ALTER TABLE work ADD COLUMN archived TINYINT NOT NULL DEFAULT 0;
CREATE UNIQUE INDEX work_identifier_unique ON work (workIdentifier);
CREATE TABLE work_history (
 historyId BIGINT PRIMARY KEY AUTO_INCREMENT,
 workIdentifier VARCHAR(128) NOT NULL,
 action VARCHAR(32) NOT NULL,
 actor VARCHAR(128) NOT NULL,
 beforeData LONGTEXT,
 afterData LONGTEXT,
 reason TEXT,
 createdAt VARCHAR(40) NOT NULL,
 INDEX history_work (workIdentifier)
);
