-- Initialisation de la base de données Moustass Videos

-- Créer la base de données
CREATE DATABASE IF NOT EXISTS videos_db
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Utiliser la base de données
USE videos_db;

-- Create user if it doesn't exist (MySQL 5.7.6+ syntax)
CREATE USER IF NOT EXISTS 'video_user'@'%' IDENTIFIED BY 'video_password';

-- Grant all privileges on videos_db to video_user
GRANT ALL PRIVILEGES ON videos_db.* TO 'video_user'@'%';
FLUSH PRIVILEGES;

-- Table des vidéos
CREATE TABLE IF NOT EXISTS videos (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID unique',
    user_id INT NOT NULL COMMENT 'ID utilisateur propriétaire',
    sender_id VARCHAR(36) NOT NULL COMMENT 'ID de l''expéditeur',
    receiver_id VARCHAR(36) NOT NULL COMMENT 'ID du destinataire',
    storage_path VARCHAR(255) NOT NULL COMMENT 'Chemin de stockage du fichier',
    encrypted_key LONGTEXT NOT NULL COMMENT 'Clé AES chiffrée en RSA-3072',
    iv VARCHAR(24) NULL COMMENT 'IV AES-GCM en base64 (12 bytes)',
    amount DECIMAL(15, 2) NOT NULL COMMENT 'Montant en EUR',
    status ENUM('UPLOADED', 'SIGNED', 'VERIFIED', 'DOWNLOADED', 'EXPIRED') DEFAULT 'UPLOADED' COMMENT 'Statut de la vidéo',
    signature LONGTEXT NULL COMMENT 'Signature RSA du hash du fichier',
    is_signed BOOLEAN DEFAULT FALSE COMMENT 'Indique si la vidéo est signée (immuable)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Date de création',
    expires_at TIMESTAMP NULL COMMENT 'Date d''expiration (60 jours)',

    -- Indexes pour les recherches
    INDEX idx_user (user_id),
    INDEX idx_sender (sender_id),
    INDEX idx_receiver (receiver_id),
    INDEX idx_status (status),
    INDEX idx_expires (expires_at),
    INDEX idx_created (created_at),
    INDEX idx_signed (is_signed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Table des vidéos uploadées';

-- Vue pour les vidéos non expirées
CREATE OR REPLACE VIEW active_videos AS
SELECT * FROM videos
WHERE expires_at IS NULL OR expires_at > NOW()
ORDER BY created_at DESC;

-- Procédure pour supprimer les vidéos expirées
DELIMITER $$

CREATE PROCEDURE IF NOT EXISTS cleanup_expired_videos()
BEGIN
    UPDATE videos
    SET status = 'EXPIRED'
    WHERE expires_at IS NOT NULL
    AND expires_at <= NOW()
    AND status != 'EXPIRED';
END$$

DELIMITER ;

-- Event pour nettoyer les vidéos expirées tous les jours
CREATE EVENT IF NOT EXISTS cleanup_expired_videos_event
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO CALL cleanup_expired_videos();

-- Données de test (optionnel)
-- INSERT INTO videos (id, sender_id, receiver_id, storage_path, encrypted_key, amount, status, created_at, expires_at)
-- VALUES (
--     UUID(),
--     'user-test-123',
--     'ADMIN',
--     'uploads/test-video.mp4',
--     'test-encrypted-key-base64',
--     250.00,
--     'UPLOADED',
--     NOW(),
--     DATE_ADD(NOW(), INTERVAL 60 DAY)
-- );

SELECT 'Initialisation de la base de données complétée' AS Status;
