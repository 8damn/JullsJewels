#!/usr/bin/env python3
"""
Vytvoří admin účet. Spustit jednou při prvním nasazení.

    python create_admin.py
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import bcrypt
import app.models  # noqa: F401 — registrace modelů před create_all

from app.database import Base, engine, SessionLocal
from app.models import User, UserRole


def main():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(User).filter(User.role == UserRole.admin).first():
            print("Admin účet již existuje. Pokud chcete vytvořit dalšího, přidejte ho přímo v DB.")
            return

        print("=== Vytvoření admin účtu ===\n")
        email = input("E-mail: ").strip()
        if not email:
            print("E-mail nesmí být prázdný.")
            return

        password = getpass.getpass("Heslo: ")
        if len(password) < 6:
            print("Heslo musí mít alespoň 6 znaků.")
            return

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        admin = User(
            email=email,
            hashed_password=hashed,
            role=UserRole.admin,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"\n✓ Admin účet '{email}' vytvořen. Přihlaste se na /auth/login")

    finally:
        db.close()


if __name__ == "__main__":
    main()
