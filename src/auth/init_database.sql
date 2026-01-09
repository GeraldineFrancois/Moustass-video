-- Initialisation de la base de données Moustass Auth Service

-- Créer la base de données
CREATE DATABASE IF NOT EXISTS auth_db
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Utiliser la base de données
USE auth_db;

-- Create user if it doesn't exist (MySQL 5.7.6+ syntax)
CREATE USER IF NOT EXISTS 'auth_user'@'%' IDENTIFIED BY 'auth_password';

-- Grant all privileges on auth_db to auth_user
GRANT ALL PRIVILEGES ON auth_db.* TO 'auth_user'@'%';
FLUSH PRIVILEGES;

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID unique de l\'utilisateur',
    firstname VARCHAR(128) NOT NULL COMMENT 'Prénom',
    lastname VARCHAR(128) NOT NULL COMMENT 'Nom',
    email VARCHAR(256) UNIQUE NOT NULL COMMENT 'Email (identifiant unique)',
    role VARCHAR(32) NOT NULL DEFAULT 'USER' COMMENT 'Rôle: ADMIN ou USER',
    password_hash VARCHAR(256) NOT NULL COMMENT 'Hash du mot de passe (bcrypt/pbkdf2)',
    password_salt VARCHAR(128) NOT NULL COMMENT 'Salt pour compatibilité legacy',
    public_key LONGTEXT NULL COMMENT 'Clé publique RSA-3072 (PEM)',
    first_login BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Indicateur de première connexion',
    user_date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date de création du compte',
    
    -- Indexes
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_created (user_date_created)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Table des utilisateurs';

-- Table des fichiers de code
CREATE TABLE IF NOT EXISTS code_files (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID unique du fichier',
    file_name VARCHAR(512) NOT NULL COMMENT 'Nom du fichier',
    file_hash VARCHAR(512) NOT NULL COMMENT 'Hash SHA256 du fichier',
    file_date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date d\'upload',
    user_id INT NOT NULL COMMENT 'ID du propriétaire',
    
    -- Contrainte de clé étrangère
    CONSTRAINT fk_code_files_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_user (user_id),
    INDEX idx_hash (file_hash),
    INDEX idx_created (file_date_created)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Table des fichiers uploadés';

-- Table des signatures
CREATE TABLE IF NOT EXISTS signatures (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID unique de la signature',
    signature_value LONGTEXT NOT NULL COMMENT 'Valeur de la signature RSA (Base64)',
    signature_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date de signature',
    file_id INT NOT NULL COMMENT 'ID du fichier signé',
    user_id INT NOT NULL COMMENT 'ID du signataire',
    
    -- Contraintes de clés étrangères
    CONSTRAINT fk_signatures_file FOREIGN KEY (file_id) REFERENCES code_files(id) ON DELETE CASCADE,
    CONSTRAINT fk_signatures_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_file (file_id),
    INDEX idx_user (user_id),
    INDEX idx_date (signature_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Table des signatures numériques';

-- Table des logs utilisateur
CREATE TABLE IF NOT EXISTS users_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID unique du log',
    action_type VARCHAR(128) NOT NULL COMMENT 'Type d\'action: login, signup, sign, delete, etc.',
    file_name VARCHAR(512) NULL COMMENT 'Nom du fichier (si applicable)',
    file_hash VARCHAR(512) NULL COMMENT 'Hash du fichier (si applicable)',
    signature_value LONGTEXT NULL COMMENT 'Signature (si applicable)',
    public_key LONGTEXT NULL COMMENT 'Clé publique (si applicable)',
    success INT NOT NULL DEFAULT 1 COMMENT '1 si succès, 0 si erreur',
    log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date du log',
    user_id INT NOT NULL COMMENT 'ID de l\'utilisateur',
    
    -- Contrainte de clé étrangère
    CONSTRAINT fk_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_user (user_id),
    INDEX idx_action (action_type),
    INDEX idx_date (log_date),
    INDEX idx_success (success)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Logs d\'audit des actions utilisateur';

SELECT 'Initialisation de la base de données auth_db complétée' AS Status;
