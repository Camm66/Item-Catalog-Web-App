from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, CatalogItem

engine = create_engine('sqlite:///catalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

category1 = Category(name="Mathematics")

session.add(category1)
session.commit()

catalogItem1 = CatalogItem(name="Calculus 1",
    description="A math course about Calculus.", category=category1, picture="testImg1.jpg")

session.add(catalogItem1)
session.commit()

catalogItem2 = CatalogItem(name="Calculus 2",
    description="A math course about Calculus, but tougher.", category=category1, picture="testImg2.jpg")

session.add(catalogItem2)
session.commit()
