import requests
import json
import os
from typing import List, Dict, Optional
from collections import defaultdict

class GrafanaMigrator:
    def __init__(self, source_url: str, source_token: str, target_url: str, target_token: str):
        self.source_url = source_url.rstrip('/')
        self.target_url = target_url.rstrip('/')
        self.source_headers = {'Authorization': f'Bearer {source_token}'}
        self.target_headers = {'Authorization': f'Bearer {target_token}'}
        self.folder_mapping = {}  # Mapeo de UIDs de folders origen -> destino

    def get_all_folders(self) -> List[Dict]:
        """Obtiene todos los folders del Grafana origen"""
        response = requests.get(
            f'{self.source_url}/api/folders',
            headers=self.source_headers
        )
        response.raise_for_status()
        return response.json()

    def create_folder(self, title: str) -> Dict:
        """Crea un folder en el Grafana destino"""
        payload = {
            'title': title
        }
        response = requests.post(
            f'{self.target_url}/api/folders',
            headers={**self.target_headers, 'Content-Type': 'application/json'},
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def get_all_dashboards(self) -> List[Dict]:
        """Obtiene lista de todos los dashboards del Grafana origen"""
        response = requests.get(
            f'{self.source_url}/api/search?type=dash-db',
            headers=self.source_headers
        )
        response.raise_for_status()
        return response.json()

    def get_dashboard_json(self, uid: str) -> Dict:
        """Obtiene la configuración completa de un dashboard"""
        response = requests.get(
            f'{self.source_url}/api/dashboards/uid/{uid}',
            headers=self.source_headers
        )
        response.raise_for_status()
        return response.json()

    def import_dashboard(self, dashboard_json: Dict, folder_id: Optional[int] = None) -> None:
        """Importa un dashboard al Grafana destino en el folder especificado"""
        dashboard = dashboard_json['dashboard']
        dashboard['id'] = None
        dashboard['uid'] = None
        
        payload = {
            'dashboard': dashboard,
            'overwrite': True,
            'message': 'Dashboard imported via migration script',
            'folderId': folder_id
        }
        
        response = requests.post(
            f'{self.target_url}/api/dashboards/db',
            headers={**self.target_headers, 'Content-Type': 'application/json'},
            json=payload
        )
        response.raise_for_status()
        print(f"Importado dashboard: {dashboard['title']} en folder ID: {folder_id}")

    def migrate_folders_and_dashboards(self) -> None:
        """Migra la estructura de folders y luego los dashboards"""
        # Primero migramos los folders
        print("Migrando estructura de folders...")
        source_folders = self.get_all_folders()
        
        for folder in source_folders:
            try:
                new_folder = self.create_folder(folder['title'])
                self.folder_mapping[folder['uid']] = new_folder['id']
                print(f"Creado folder: {folder['title']}")
            except Exception as e:
                print(f"Error creando folder {folder['title']}: {str(e)}")

        # Luego obtenemos y organizamos los dashboards por folder
        print("\nObteniendo dashboards...")
        dashboards = self.get_all_dashboards()
        dashboards_by_folder = defaultdict(list)
        
        for dash in dashboards:
            folder_uid = dash.get('folderUid', '')
            dashboards_by_folder[folder_uid].append(dash)

        # Finalmente, migramos los dashboards folder por folder
        total_dashboards = len(dashboards)
        migrated = 0

        print(f"\nMigrando {total_dashboards} dashboards...")
        
        # Primero los dashboards sin folder (General)
        for dash in dashboards_by_folder['']: 
            try:
                dash_json = self.get_dashboard_json(dash['uid'])
                self.import_dashboard(dash_json, None)
                migrated += 1
                print(f"Progreso: {migrated}/{total_dashboards}")
            except Exception as e:
                print(f"Error migrando dashboard {dash['title']}: {str(e)}")

        # Luego los dashboards en folders
        for folder_uid, folder_dashboards in dashboards_by_folder.items():
            if folder_uid == '':  # Ya procesamos los dashboards sin folder
                continue
                
            folder_id = self.folder_mapping.get(folder_uid)
            if not folder_id:
                print(f"No se encontró el ID del folder destino para UID: {folder_uid}")
                continue

            for dash in folder_dashboards:
                try:
                    dash_json = self.get_dashboard_json(dash['uid'])
                    self.import_dashboard(dash_json, folder_id)
                    migrated += 1
                    print(f"Progreso: {migrated}/{total_dashboards}")
                except Exception as e:
                    print(f"Error migrando dashboard {dash['title']}: {str(e)}")

def main():
    # Configuración
    SOURCE_URL = "http://old-grafana:3000"  # URL del Grafana origen
    TARGET_URL = "http://new-grafana:3000"  # URL del Grafana destino
    SOURCE_TOKEN = os.getenv("SOURCE_TOKEN")  # Token API del Grafana origen
    TARGET_TOKEN = os.getenv("TARGET_TOKEN")  # Token API del Grafana destino

    if not all([SOURCE_TOKEN, TARGET_TOKEN]):
        raise ValueError("Por favor configura SOURCE_TOKEN y TARGET_TOKEN como variables de entorno")

    migrator = GrafanaMigrator(SOURCE_URL, SOURCE_TOKEN, TARGET_URL, TARGET_TOKEN)
    migrator.migrate_folders_and_dashboards()

if __name__ == "__main__":
    main()