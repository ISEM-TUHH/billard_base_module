# billard-base-module
Parent class for other basic modules of Billard@ISEM

This class provides basic functionalities for setting up the API, loading config/secrets (.json/.env) and provides a page to download stored files.

## Usage
- Add as a submodule to other modules
- Add a .env-file with credentials USER and PASSWORD for the download page in this folder
- Include and use as parent when creating your modules class