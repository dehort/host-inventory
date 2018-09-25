import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()


class Host(Base):
    __tablename__ = 'host'

    id = Column(String(250), primary_key=True)
    display_name = Column(String(250))
    account_number = Column(Integer)
    created_timestamp = Column(String(250))
    updated_timestamp = Column(String(250))


#class Tag(Base):
#    __tablename__ = 'tag'

#    namespace = Column(String(250))
#    key = Column(String(250))
#    value = Column(String(250))

engine = create_engine('sqlite:///host_inventory.db')
Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)
session = DBSession()

hosts = session.query(Host).all()
for h in hosts:
    print(f"{h.id} - {h.display_name}")


new_host = Host(id="9876", display_name="node4", account_number="1234")
session.add(new_host)
session.commit()

hosts = session.query(Host).all()
for h in hosts:
    print(f"{h.id} - {h.display_name}")


hosts = session.query(Host).filter(Host.account_number=="1234").all()
for h in hosts:
    print(f"{h.id} - {h.display_name}")

