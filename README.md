# H.O.M – History of Machines (MVP)

The Minimum Viable Product (MVP) for the H.O.M. system, designed for tracking machine repairs, downtimes, and collecting primary data from production lines. The architecture is built on an asynchronous Python stack utilizing GraphQL for efficient data interaction.

## 🚀 Core Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | `FastAPI` | Asynchronous framework for high-performance API development. |
| **API** | `Strawberry GraphQL` | GraphQL implementation to prevent over-fetching and under-fetching of data. |
| **ORM/DB** | `SQLAlchemy` (SQLModel recommended) | Asynchronous interaction with the **PostgreSQL** database. |
| **Frontend** | `React` + `TypeScript` | Modern, strongly typed interface. |
| **Styling** | `Tailwind CSS` | Utility-first CSS framework for rapid UI development and **Dark/Light Theme** implementation. |
| **DevOps** | `Docker Compose` + `GitHub Actions` | Containerization and automation of the CI/CD pipeline. |

## 💡 MVP Core Functionality (Auth + Repairs + Downtimes)

This MVP version focuses on implementing the key modules required for data collection and access control, as prioritized by the Technical Specification.

### 1. Authentication and RBAC
* **Authentication:** Users log in to receive a JWT token for secure access to GraphQL endpoints.
* **RBAC (Role-Based Access Control):** A foundation for the role model (`User`, `Admin`, `Technician`, etc.) is implemented to restrict access to mutations (write operations), crucial for system security.

### 2. Repair Tracking (`Repairs`)
* Ability to **create** and **update** repair records via GraphQL mutations.
* Each record is linked to a specific **Machine** and **Line**.
* Records capture the **start_datetime** and **end_datetime** of the repair event.

### 3. Downtime Recording (`Downtimes`)
* Functionality to register unplanned production downtimes.
* Data collection includes the **reason for downtime** and its **duration**.

### 4. Infrastructure & Monitoring
* **Migrations:** Database schema updates are handled automatically using Alembic upon service start.
* **Monitoring:** Basic **Prometheus** and **Grafana** services are included in the local `docker-compose.yml` for collecting service health and custom metrics.

---

## 🛠️ Deployment Instructions

The project uses Docker for local development and a GitHub Actions pipeline for deployment to Staging/Production environments.

### 1. Local Development (`docker compose up`)

This setup is used for development, testing, and debugging. It includes the Backend API, Database, Frontend App, and the Monitoring stack.

#### Prerequisites
1.  **Git**
2.  **Docker** and **Docker Compose**

#### Steps
1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/BombInside/HOM_MVP.git](https://github.com/BombInside/HOM_MVP.git)
    cd HOM_MVP
    ```

2.  **Create Environment Variables:**
    Create a file named **`.env`** in the root directory and fill it with your local settings:

    ```bash
    # .env
    # Application Secrets
    SECRET_KEY="YOUR_SECRET_KEY_FOR_JWT"
    ALGORITHM="HS256"

    # PostgreSQL/CockroachDB Settings
    POSTGRES_USER=hom_user
    POSTGRES_PASSWORD=hom_pass
    POSTGRES_DB=hom_db

    # Ports
    BACKEND_PORT=8000
    FRONTEND_PORT=3000
    ```

3.  **Build and Start Services:**
    The `--build` flag ensures that the latest code changes are included in the Docker images.

    ```bash
    docker compose up --build -d
    ```

4.  **Access:**
    * **Frontend App:** `http://localhost:3000`
    * **Backend GraphQL Playground:** `http://localhost:8000/graphql`
    * **Monitoring (Grafana/Prometheus):** `http://localhost:9090` (Ports may vary based on your local `docker-compose.yml`).

### 2. Staging Deployment (DigitalOcean Droplet via GitHub Actions)

This scenario describes the deployment process to a remote VPS (like a DigitalOcean Droplet), orchestrated by the automated CI/CD pipeline. This process adheres to the TZ requirements for GitHub Actions, Staging environment, and secure secret management (Vault).

#### Prerequisites
1.  **Remote Server (Droplet):** A running Linux VPS with Docker and Docker Compose installed.
2.  **User Access:** A non-root user (`deployer`) with SSH access and permissions to run Docker commands.
3.  **GitHub Secrets:** Repository secrets configured for SSH and Vault access.
    * `SSH_PRIVATE_KEY`: Private key for the `deployer` user.
    * `REMOTE_HOST`: IP address of the DigitalOcean Droplet.
    * `VAULT_TOKEN`: Token or credentials for HashiCorp Vault access.

#### Steps (Executed by GitHub Actions)

The deployment is triggered automatically upon merging changes into the `main` branch. The process involves the following key stages within the `.github/workflows/ci.yml` file:

1.  **Build and Test (CI Stage):**
    * Build Docker images for Backend and Frontend.
    * Run Unit and E2E tests against the built images. (Fails if code coverage is below 70%).

2.  **Prepare Secrets (CD Stage - Vault Integration):**
    * **Authentication:** The GitHub Actions runner uses the `VAULT_TOKEN` to authenticate with the **HashiCorp Vault** instance (running on a separate, secure host).
    * **Retrieval:** Secrets (e.g., `DB_PASSWORD_STAGE`, API Keys) are retrieved securely from the designated path (`/secret/hom/stage`). **These secrets are never exposed in the logs.**

3.  **Deploy to Droplet (CD Stage - SSH/Docker):**
    * **SSH Connection:** The workflow connects to the Droplet using the `SSH_PRIVATE_KEY` and `REMOTE_HOST`.
    * **Pull Images:** Pull the newly built Docker images from the container registry (e.g., GitHub Packages).
    * **Configuration:** A deployment script on the Droplet:
        * Creates a `stage.env` file on the remote server using the secrets retrieved from Vault.
        * Updates the `docker-compose.stage.yml` file (which includes Nginx/Traefik as a Reverse Proxy and Prometheus/Grafana).
    * **Run Services:** Executes the final deployment command:
        ```bash
        ssh deployer@${{ secrets.REMOTE_HOST }} "
          cd /path/to/hom_mvp/stage && 
          docker compose -f docker-compose.stage.yml pull && 
          docker compose -f docker-compose.stage.yml up -d --force-recreate
        "
        ```

4.  **Database Migrations:**
    * The deployment script (or a separate service in `docker-compose.stage.yml`) ensures that **Alembic migrations** are run automatically and successfully **before** the main API service starts.

---
*(End of README.md content)*