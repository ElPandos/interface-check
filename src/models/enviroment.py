from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    settings_file: str
    config_file: str
    pythonpath: str

    project_state: int

    node_env: str
    generated_folder_path: str
