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

category1 = Category(name="Mathematics", user_id=1)

session.add(category1)
session.commit()

category2 = Category(name="Humanities")

session.add(category2)
session.commit()

category3 = Category(name="Computer Science")

session.add(category3)
session.commit()

catalogItem1 = CatalogItem(name="Calculus 1",
                           description="A math course about Calculus.",
                           category=category1, picture="testImg1.jpg",
                           user_id=1)

session.add(catalogItem1)
session.commit()

catalogItem2 = CatalogItem(name="Calculus 2",
                           description='''A math course about Calculus,
                           but tougher.''', category=category1,
                           picture="testImg2.jpg")

session.add(catalogItem2)
session.commit()

catalogItem3 = CatalogItem(name="Ancient Greek Philosophy",
                           description='''Socrates, Plato, Aristole;
                           The list goes on...''',
                           category=category2, picture="testImg3.jpg")

session.add(catalogItem3)
session.commit()

catalogItem4 = CatalogItem(name="Sartre and Philosophy of Mind",
                           description='''This course will really get
                           you thinking.''', category=category2)

session.add(catalogItem4)
session.commit()

catalogItem5 = CatalogItem(name="Database Technologies",
                           description='''A course about tables and all
                           that jazz.''',
                           category=category3, picture="testImg4.jpg")

session.add(catalogItem5)
session.commit()

catalogItem6 = CatalogItem(name="Software Architecture",
                           description='''Mind your components and beware
                           of your dependencies.''',
                           category=category3, picture="testImg5.jpg")

session.add(catalogItem6)
session.commit()
