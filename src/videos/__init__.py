"""
Service de Upload Vidéo - Microservice Architecture
Permet l'upload, la gestion et le téléchargement sécurisé de vidéos

Ne pas importer `upload_service` au niveau du package pour éviter
les effets de bord (connexion DB) lors d'imports dans les tests.
"""

# Exposer les sous-modules sans les importer ici pour éviter l'initialisation
# de la base de données ou d'autres ressources lors de l'importation du
# package `src.videos`.
__all__ = [
	"upload_service",
	"storage_manager",
	"models",
	"database",
	"metadata_mapper",
	"main_upload",
	"expiration_engine",
	"security",
	"upload_api",
]
