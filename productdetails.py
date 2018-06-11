from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Brand, Base, Product, User

engine = create_engine('sqlite:///brand.db')
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
User1 = User(name="krishna", email="krishnamurthy.2797@gmail.com")

brand1 = Brand(name="Lee Cooper")
session.add(brand1)
session.commit()

product1 = Product(name="Black jeans", description="Black shaded", price="$40",
                   costumetype="Bottomwear", brand=brand1)

session.add(product1)
session.commit()

product2 = Product(name="Red shirt", description="checks shirt",
                   price="$45", costumetype="Shirts", brand=brand1)

session.add(product2)
session.commit()

product3 = Product(name="White T-shirt", description="Printed T-shirt",
                   price="$35", costumetype="T-shirts", brand=brand1)

session.add(product3)
session.commit()

brand2 = Brand(name="Levis")
session.add(brand2)
session.commit()

product1 = Product(name="Blue jeans", description="Blue shaded",
                   price="$45", costumetype="Bottomwear", brand=brand2)

session.add(product1)
session.commit()

product2 = Product(name="Yellow shirt", description="Plain shirt",
                   price="$50", costumetype="Shirts", brand=brand2)

session.add(product2)
session.commit()

product3 = Product(name="Blue T-shirt", description="Strechable T-shirt",
                   price="$40", costumetype="T-shirts", brand=brand1)

session.add(product3)
session.commit()

brand3 = Brand(name="Wrangler")
session.add(brand3)
session.commit()

product1 = Product(name="Cargo jeans", description="Heavy pocckets",
                   price="$65", costumetype="Bottomwear", brand=brand3)

session.add(product1)
session.commit()

product2 = Product(name="White shirt", description="Lenin shirt",
                   price="$55", costumetype="Shirts", brand=brand1)

session.add(product2)
session.commit()

product3 = Product(name="Brown T-shirt", description="Plain T-shirt",
                   price="$35", costumetype="T-shirts", brand=brand1)

session.add(product3)
session.commit()

brand4 = Brand(name="Jack&Jones")
session.add(brand4)
session.commit()

product1 = Product(name="White jeans", description="Slim fit",
                   price="$40", costumetype="Bottomwear", brand=brand4)

session.add(product1)
session.commit()

product2 = Product(name="Black shirt", description="Cotton shirt",
                   price="$45", costumetype="Shirts", brand=brand4)

session.add(product2)
session.commit()

product3 = Product(name="Green T-shirt", description="Printed T-shirt",
                   price="$35", costumetype="T-shirts", brand=brand4)

session.add(product3)
session.commit()

print("added product details!")
