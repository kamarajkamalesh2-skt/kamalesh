-- ============================================================
--  EduNova College Registration — MySQL Schema
--  HOW TO RUN:
--    mysql -u root -p < schema.sql
--  OR paste this inside MySQL Workbench / phpMyAdmin
-- ============================================================

-- 1. Create database
CREATE DATABASE IF NOT EXISTS edunova_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE edunova_db;

-- 2. Drop old table (only during development)
-- DROP TABLE IF EXISTS students;

-- 3. Create students table
CREATE TABLE IF NOT EXISTS students (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  application_id  VARCHAR(20)   NOT NULL UNIQUE,

  -- Personal info
  first_name      VARCHAR(80)   NOT NULL,
  last_name       VARCHAR(80)   NOT NULL,
  email           VARCHAR(150)  NOT NULL UNIQUE,
  phone           VARCHAR(25)   NOT NULL,
  dob             DATE          NOT NULL,
  gender          ENUM('Male','Female','Non-binary','Prefer not to say') NOT NULL,
  address         TEXT          NOT NULL,
  password_hash   VARCHAR(255)  NOT NULL,

  -- Academic
  school_10       VARCHAR(150)  NOT NULL,
  marks_10        DECIMAL(5,2)  NOT NULL,
  school_12       VARCHAR(150)  NOT NULL,
  marks_12        DECIMAL(5,2)  NOT NULL,
  exam_type       VARCHAR(60)   DEFAULT 'None',
  exam_score      VARCHAR(60)   DEFAULT '-',
  achievements    TEXT,

  -- Program
  program         VARCHAR(120)  NOT NULL,
  degree_level    VARCHAR(40)   NOT NULL,
  hostel          VARCHAR(40)   DEFAULT 'Not specified',
  heard_from      VARCHAR(80),
  sop             TEXT          NOT NULL,

  -- Status
  status          ENUM('Pending','Under Review','Accepted','Rejected') DEFAULT 'Pending',
  remarks         TEXT,

  -- Timestamps
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 4. Indexes
CREATE INDEX IF NOT EXISTS idx_email   ON students(email);
CREATE INDEX IF NOT EXISTS idx_status  ON students(status);
CREATE INDEX IF NOT EXISTS idx_prog    ON students(program);

-- 5. Verify
SHOW TABLES;
DESCRIBE students;
SELECT 'Schema created successfully!' AS result;