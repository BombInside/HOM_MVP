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

## 🛠️ Local Development Setup Instructions

To run the full MVP stack in your development environment, you need **Docker** and **Docker Compose** installed.

### 1. Clone the Repository

```bash
git clone [https://github.com/BombInside/HOM_MVP.git](https://github.com/BombInside/HOM_MVP.git)
cd HOM_MVP