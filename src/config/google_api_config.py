import json
from dataclasses import dataclass
from pathlib import Path

from src.config import config_utils


@dataclass
class GoogleApiConfig:
    private_key: str
    client_email: str
    project_id: str
    private_key_id: str
    client_id: str
    calendar_id: str

    def __post_init__(self):
        # Ensure the private key is formatted correctly
        if self.private_key:
            self.private_key = self.private_key.replace("\\n", "\n")


def get_google_api_config() -> GoogleApiConfig:
    return GoogleApiConfig(
        private_key=config_utils.get_mandatory_env_variable("GC_PRIVATE_KEY"),
        client_email=config_utils.get_mandatory_env_variable("GC_CLIENT_EMAIL"),
        project_id=config_utils.get_mandatory_env_variable("GC_PROJECT_ID"),
        private_key_id=config_utils.get_mandatory_env_variable("GC_PRIVATE_KEY_ID"),
        client_id=config_utils.get_mandatory_env_variable("GC_CLIENT_ID"),
        calendar_id=config_utils.get_mandatory_env_variable("GC_CALENDAR_ID"),
    )


def get_service_account_info(config: GoogleApiConfig) -> Path:
    service_account_info = {
        "type": "service_account",
        "project_id": config.project_id,
        "private_key_id": config.private_key_id,
        "private_key": config.private_key,
        "client_email": config.client_email,
        "client_id": config.client_id,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{config.client_email}",
        "universe_domain": "googleapis.com",
    }

    save_credentials_in_file(service_account_info)

    return service_account_info


def save_credentials_in_file(service_account_info: dict) -> None:
    working_dir = Path.cwd()
    base_dir = find_base_dir(working_dir, "dialogue_praktikum")

    if base_dir is None:
        base_dir = working_dir

    cred_folder = base_dir / ".cred"
    service_account_file = cred_folder / "google_account_file_save.json"
    cred_folder.mkdir(parents=True, exist_ok=True)
    with service_account_file.open("w") as f:
        json.dump(service_account_info, f)


def find_base_dir(current_path, target_dir_name):
    if current_path.name == target_dir_name:
        return current_path
    for parent in current_path.parents:
        if parent.name == target_dir_name:
            return parent
    return None
