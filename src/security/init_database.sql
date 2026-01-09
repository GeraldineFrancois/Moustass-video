-- Database initialization for Security Service

-- Create database
CREATE DATABASE IF NOT EXISTS security_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- First, create user if not exists (root creates it)
CREATE USER IF NOT EXISTS 'security_user'@'%' IDENTIFIED BY 'security_password';
CREATE USER IF NOT EXISTS 'security_user'@'localhost' IDENTIFIED BY 'security_password';

-- Grant ALL privileges on security_db to security_user
GRANT ALL PRIVILEGES ON security_db.* TO 'security_user'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;

USE security_db;

-- Security audit logs table
CREATE TABLE IF NOT EXISTS security_audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    service_name VARCHAR(50) NOT NULL,
    user_id INT NULL,
    operation_details TEXT NULL,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT NULL,
    ip_address VARCHAR(45) NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_type (event_type),
    INDEX idx_service (service_name),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Scan results table
CREATE TABLE IF NOT EXISTS scan_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scan_type VARCHAR(50) NOT NULL,
    service_name VARCHAR(50) NOT NULL,
    severity_critical INT DEFAULT 0,
    severity_high INT DEFAULT 0,
    severity_medium INT DEFAULT 0,
    severity_low INT DEFAULT 0,
    total_issues INT DEFAULT 0,
    scan_details TEXT NULL,
    scan_status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_scan_type (scan_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
