from google.appengine.ext import db
from google.appengine.ext import search  
from google.appengine.api import users


class Person(search.SearchableModel):
	create_date 	= db.DateTimeProperty(auto_now_add=True)
	forename   		= db.StringProperty()
	surname   		= db.StringProperty()
	person_id  		= db.StringProperty()
	gender     		= db.StringProperty()
	birth_date 		= db.DateProperty()
	identities		= db.StringListProperty()
	language		= db.StringProperty()
	avatar			= db.BlobProperty()


class Contact(db.Model):
	create_date 	= db.DateTimeProperty(auto_now_add=True)
	person 			= db.ReferenceProperty(Person, collection_name='contacts')
	type   			= db.StringProperty()
	value  			= db.StringProperty()
	activation_key	= db.StringProperty()


class Role(db.Model):
	create_date 	= db.DateTimeProperty(auto_now_add=True)
	person 			= db.ReferenceProperty(Person, collection_name='roles')
	value  			= db.StringProperty()
