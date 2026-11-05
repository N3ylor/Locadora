from locadora.database import Database
from locadora.menu import Menu
from locadora.servicos import Locadora


def main():
    db = Database("locadora.db")
    try:
        Menu(Locadora(db)).principal()
    except (KeyboardInterrupt, EOFError):
        print("\nEncerrado.")
    finally:
        db.fechar()


if __name__ == "__main__":
    main()
