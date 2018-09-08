import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy_imageattach.entity import Image, image_attachment

Base = declarative_base()


class Category(Base):
    __tablename__ = 'catalog'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class CatalogItem(Base):
    __tablename__ = 'catalog_item'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('catalog.id'))
    picture = Column(String(250))
    category = relationship(Category)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'picture': self.picture
        }

#class ItemPicture(Base, Image):
#    __tablename__ = 'item_picture'

#    item_id = Column(Integer, ForeignKey('catalog_item.id'), primary_key=True)
#    item = relationship('CatalogItem')



engine = create_engine('sqlite:///catalog.db')


Base.metadata.create_all(engine)
