# AutoDeploy

AutoDeploy is a web application that allows users to deploy, manage, and monitor server instances using Docker containers. It provides a user-friendly interface to start, stop, and remove server deployments, as well as view the status of each deployment.

## Features

- **Deploy New Servers**: Easily deploy new server instances with custom Docker images and flags.
- **Manage Deployments**: Start, stop, and remove server deployments from the dashboard.
- **Monitor Status**: View the status of each server deployment (online/offline) and access server URLs.
- **GitHub OAuth2 Login**: Secure login using GitHub OAuth2.
- **Database Integration**: Store deployment information in an SQLite database.
- **Public View**: Anyone can view your servers but only YOU can edit them

## Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/jeffreywangdev/autoDeploy.git
    cd autoDeploy
    ```

2. **Create a virtual environment and activate it**:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:
    Create a `.env` file in the root directory and add the following:
    ```
    GITHUB_CLIENT_ID=your_github_client_id
    GITHUB_CLIENT_SECRET=your_github_client_secret
    ```
    get all these from [Github API](https://github.com/settings/developers)
5. **Run the application**:
    ```sh
    fastapi run main.py
    ```

6. **Access the application**:
    Open your browser and navigate to `http://localhost:8000`.

## Usage

- **Login**: Click on the login button and authenticate using your GitHub account.
- **Deploy Server**: Fill in the server details and click on the "Deploy" button.
- **Manage Servers**: Use the dashboard to start, stop, or remove server deployments.
- **Monitor Status**: Check the status of each deployment and access the server URLs.

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

![image](https://github.com/user-attachments/assets/4148d7e6-52fe-4446-b26b-749433b1eb91)
![image](https://github.com/user-attachments/assets/5b9b843a-d399-40ad-9b33-f7f0c6e7565c)
![image](https://github.com/user-attachments/assets/5406d465-2ea6-41df-aeab-c8e3ad32db27)



## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [Docker](https://www.docker.com/)
- [GitHub OAuth](https://developer.github.com/apps/building-oauth-apps/)
