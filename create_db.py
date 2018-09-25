import sqlite3
import datetime

conn = sqlite3.connect("host_inventory.db")

c = conn.cursor()

c.execute( '''CREATE TABLE host 
              (id varchar(250) NOT NULL PRIMARY KEY ASC,
               display_name varchar(250),
               account_number INTEGER,
               created_timestamp TEXT,
               updated_timestamp TEXT )''')

c.execute('''CREATE TABLE canonical_fact
              (key TEXT,
               value TEXT,
               host_id varchar(250), FOREIGN KEY(host_id) REFERENCES host(id))''')

c.execute('''CREATE TABLE fact
              (namespace TEXT,
               key TEXT,
               value TEXT,
               host_id varchar(250), FOREIGN KEY(host_id) REFERENCES host(id))''')

c.execute('''CREATE TABLE tag
              (namespace TEXT,
               key TEXT,
               value TEXT,
               host_id varchar(250), FOREIGN KEY(host_id) REFERENCES host(id))''')

c.execute("INSERT INTO host VALUES('12345', 'host1', 1234, datetime('now'), datetime('now'))")
c.execute("INSERT INTO host VALUES('12346', 'host2', 1234, datetime('now'), datetime('now'))")
c.execute("INSERT INTO host VALUES('12347', 'host3', 1234, datetime('now'), datetime('now'))")

conn.commit()
conn.close()

