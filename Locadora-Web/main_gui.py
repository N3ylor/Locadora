from locadora.database import Database
from locadora.gui import App
from locadora.servicos import Locadora


def main():
    db = Database("locadora.db")
    try:
        App(Locadora(db)).mainloop()
    finally:
        db.fechar()


if __name__ == "__main__":
    main()
