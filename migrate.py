import requests
import os

from typing import List, Dict, Optional
from collections import defaultdict


class GrafanaMigrator:
    def __init__(self, source_url: str, source_token: str, target_url: str, target_token: str):
        self.source_url = source_url.rstrip('/')
        self.target_url = target_url.rstrip('/')
        self.source_headers = {'Authorization': f'Bearer {source_token}'}
        self.target_headers = {'Authorization': f'Bearer {target_token}'}
        self.folder_mapping = {}

    def get_all_folders(self) -> List[Dict]:
        """Get all folders from source Grafana"""
        response = requests.get(
            f'{self.source_url}/api/folders',
            headers=self.source_headers
        )
        response.raise_for_status()
        return response.json()

    def create_folder(self, title: str) -> Dict:
        """Create a folder in target Grafana"""
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
        """Get list of all dashboards from source Grafana"""
        response = requests.get(
            f'{self.source_url}/api/search?type=dash-db',
            headers=self.source_headers
        )
        response.raise_for_status()
        return response.json()

    def get_dashboard_json(self, uid: str) -> Dict:
        """Get complete dashboard configuration"""
        response = requests.get(
            f'{self.source_url}/api/dashboards/uid/{uid}',
            headers=self.source_headers
        )
        response.raise_for_status()
        return response.json()

    def import_dashboard(self, dashboard_json: Dict, folder_id: Optional[int] = None) -> None:
        """Import dashboard to target Grafana in specified folder"""
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
        print(f"Imported dashboard: {dashboard['title']} to folder ID: {folder_id}")

    def migrate_folders_and_dashboards(self) -> None:
        """Migrate folder structure and dashboards"""
        print("Migrating folder structure...")
        source_folders = self.get_all_folders()

        for folder in source_folders:
            try:
                new_folder = self.create_folder(folder['title'])
                self.folder_mapping[folder['uid']] = new_folder['id']
                print(f"Created folder: {folder['title']}")
            except Exception as e:
                print(f"Error creating folder {folder['title']}: {str(e)}")

        print("\nGetting dashboards...")
        dashboards = self.get_all_dashboards()
        dashboards_by_folder = defaultdict(list)

        for dash in dashboards:
            folder_uid = dash.get('folderUid', '')
            dashboards_by_folder[folder_uid].append(dash)

        total_dashboards = len(dashboards)
        migrated = 0

        print(f"\nMigrating {total_dashboards} dashboards...")

        for dash in dashboards_by_folder['']:
            try:
                dash_json = self.get_dashboard_json(dash['uid'])
                self.import_dashboard(dash_json, None)
                migrated += 1
                print(f"Progress: {migrated}/{total_dashboards}")
            except Exception as e:
                print(f"Error migrating dashboard {dash['title']}: {str(e)}")

        for folder_uid, folder_dashboards in dashboards_by_folder.items():
            if folder_uid == '':
                continue

            folder_id = self.folder_mapping.get(folder_uid)
            if not folder_id:
                print(f"Target folder ID not found for UID: {folder_uid}")
                continue

            for dash in folder_dashboards:
                try:
                    dash_json = self.get_dashboard_json(dash['uid'])
                    self.import_dashboard(dash_json, folder_id)
                    migrated += 1
                    print(f"Progress: {migrated}/{total_dashboards}")
                except Exception as e:
                    print(f"Error migrating dashboard {dash['title']}: {str(e)}")


def main():
    SOURCE_URL = "http://old-grafana:3000"
    TARGET_URL = "http://new-grafana:3000"
    SOURCE_TOKEN = os.getenv("SOURCE_TOKEN")
    TARGET_TOKEN = os.getenv("TARGET_TOKEN")

    if not all([SOURCE_TOKEN, TARGET_TOKEN]):
        raise ValueError("Please set SOURCE_TOKEN and TARGET_TOKEN environment variables")

    migrator = GrafanaMigrator(SOURCE_URL, SOURCE_TOKEN, TARGET_URL, TARGET_TOKEN)
    migrator.migrate_folders_and_dashboards()


if __name__ == "__main__":
    main()
