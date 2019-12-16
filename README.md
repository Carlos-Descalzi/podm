# PODM: (P)ython (O)bject-json (D)ocument (M)apper

This library is intended to create objects that easily map to a well defined json format, for cases
where jsonpickle format is not good.
Only available for Python3

## Some use case samples

```
class Entity(JsonObject):
	"""
	A base class for the object model
	"""
	oid = Property()
	created = Property('created', default=datetime.now) # Default value when object is instantiated

class Company(Entity):
	company_name = Property('company-name') # Specify a different field name in json.
	description = Property()        

class Sector(Entity):
	employees = Property('employees')

	def __init__(self,**kwargs):
		super(Sector, self).__init__(**kwargs)
		# Default value for _employees
		self._employees = []

class Employee(Entity):
	name = Property()

company = Company(
  name='My great company',
  description='....'
)

json_data = company.to_dict()

company_2 = Company.from_dict(json_data)
```
