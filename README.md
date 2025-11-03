# 🛒 E-Commerce Backend API using FastAPI

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-brightgreen)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-lightblue)
![Docker](https://img.shields.io/badge/Containerized-Docker-blue)
![JWT](https://img.shields.io/badge/Auth-JWT-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📘 Overview

This project is a **fully functional backend system for an E-Commerce platform**, built using **FastAPI**.  
It is designed with scalability, modularity, and performance in mind — supporting authentication, product management, and user operations.  
The backend exposes RESTful APIs that can easily integrate with any frontend (React, Angular, etc.).

---

## ⚙️ Tech Stack

| Category | Technologies Used |
|-----------|-------------------|
| **Language** | Python 3.11 |
| **Framework** | FastAPI |
| **Database** | PostgreSQL / MySQL |
| **ORM** | SQLAlchemy |
| **Authentication** | JWT Tokens |
| **Containerization** | Docker |
| **API Testing** | Postman |
| **Version Control** | Git & GitHub |

---

## 🚀 Features

✅ **User Authentication & Authorization**  
- Register and Login using JWT tokens  
- Secure password hashing using `passlib`  

✅ **Product Management**  
- Add, update, delete, and view products  
- Pagination and category filtering  

✅ **Order Management**  
- Users can place, view, and cancel orders  
- Admins can update order status  

✅ **Cart System**  
- Add/remove items from cart  
- Automatic total amount calculation  

✅ **Role-Based Access**  
- Separate permissions for Admin and Customer  

✅ **API Documentation**  
- Auto-generated Swagger UI and ReDoc at runtime  

---

## 🏗️ Project Structure
E_Commerce_FastAPI_Backend/
│
├── app/
│ ├── main.py # Entry point
│ ├── models.py # SQLAlchemy models
│ ├── schemas.py # Pydantic models
│ ├── database.py # Database configuration
│ ├── crud.py # Database operations
│ ├── auth.py # Authentication logic (JWT)
│ └── routes/
│ ├── users.py
│ ├── products.py
│ └── orders.py
│
├── requirements.txt # Dependencies
├── Dockerfile # Docker configuration
├── .env # Environment variables
└── README.md


---

## 🧩 Installation & Setup

### 1️⃣ Clone the Repository
git clone https://github.com/jumbovardan/E_Commerce_FastAPI_Backend.git
cd E_Commerce_FastAPI_Backend

2️⃣ Create Virtual Environment
python -m venv myenv
source myenv/bin/activate   # for Linux/Mac
myenv\Scripts\activate      # for Windows

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Setup Environment Variables

Create a .env file in the project root:

DATABASE_URL=postgresql://username:password@localhost/ecommerce_db
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

5️⃣ Run the Server
uvicorn app.main:app --reload

6️⃣ Access API Docs

Swagger UI → http://127.0.0.1:8000/docs




