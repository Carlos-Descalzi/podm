# PODM: (P)ython (O)bject - (D)ictionary (M)apper

This library is intended to create objects that easily serialize to dictionaries that can be later stored as JSON or YAML.
It is intended as a replacement of jsonpickle for cases where jsonpickle output format is not good at all.

Features:
* Support for ordered dictionaries or custom mapping classes
* Custom field serialization/deserialization
* Validators
* Json Schema generation

## Installation

```
	pip3 install podm
```

## Some use case samples

Very simple case:
```python
from podm import JsonObject, Property

class Person(JsonObject):

   first_name = Property()
   last_name = Property()
   
person = Person(first_name='John',last_name='Doe')
person_dict = person.to_dict()
print(json.dumps(person_dict,indent=4))

# will output
{
    "py/object": "__main__.Person",
    "first_name": "John",
    "last_name": "Doe"
}
```

Notice the field "py/object", if you don't need it, you can specify on the class declaration:

```python

class Person(JsonObject):

    __add_type_identifier__ = False
    
    first_name = Property()
    last_name = Property()

```

If you need to specify a different name when the field is converted to dictionary:

```python

class Person(JsonObject):

    __add_type_identifier__ = False
    
    first_name = Property('first-name')
    last_name = Property('last-name')


person = Person(first_name='John',last_name='Doe')
person_dict = person.to_dict()
print(json.dumps(person_dict,indent=4))

# will output
{
    "first-name": "John",
    "last-name": "Doe"
}
```

Now, when you need to convert the dictionary back to object:
```
person = Person.from_dict({'first-name':'John', 'last-name':'Doe'})
```

In case you don't want to explicitly use the class, or you are working with a hierarchy of classes, you will need the type identifier field in order to let the library recognize the object type:
```python
some_dictionary = {
    "py/object": "__main__.Person",
    "first-name": "John",
    "last-name": "Doe"
}
some_obj = JsonObject.parse(some_dictionary)
```


Handling complex data types:
```python
from podm import JsonObject, Property, Handler

class DateTimeHandler(Handler):
	"""
	Define a custom handler for datetime objects
	"""
	def encode(self, obj):
		return {
			'year' : obj.year,
			'month' : obj.month,
			'day' : obj.day,
			'hour' : obj.hour,
			'minute' : obj.minute,
			'second' : obj.second,
			'microsecond' : obj.microsecond
		}

	def decode(self, obj_data):
		return datetime(**obj_data)

class Entity(JsonObject):
	"""
	A base class for the object model
	"""
	oid = Property()
	created = Property('created', handler=DateTimeHandler(), default=datetime.now) # Default value when object is instantiated

class Company(Entity):
	company_name = Property('company-name') # Specify a different field name in json.
	description = Property()        

class Sector(Entity):
	employees = Property('employees', default=[])

class Employee(Entity):
	name = Property()

company = Company(
  name='My great company',
  description='....'
)

json_data = company.to_dict()

company_2 = Company.from_dict(json_data)
```


## Jsonpickle format support
```python
data = {
	'py/object' : 'Company',
	'py/state': {
		'company-name' : 'master',
		'description'  : 'some description'
	}
}
company = JsonObject.parse(data) 

```

## Automatically generated getters/setters. 
If they are declared property accessors will use them instead.
```python

class Company(JsonObject):
	company_name = Property('company-name') # Specify a different field name in json.
	
# Automatically generated getter
company_name = company.get_company_name()

# Also property accessors
company_name = company.company_name

# And private attributes
company_name = company._company_name
```

## Write custom getters and setters
```python

class Company(JsonObject):
	company_name = Property('company-name') # Specify a different field name in json.

	def get_company_name(self):
		print('Getter called!!!')
		# generated attribute
		return self._company_name

# So, when calling the property getter ...
company_name = company.company_name

# will print 'Getter called!!!'
```

### Enum support
It is possible to decide how to serialize/deserialize enums.
```python
class InvoiceType(Enum):
	TYPE_A = 1
	TYPE_B = 2


class Invoice(JsonObject):
	invoice_type = Property(type=InvoiceType, enum_as_str=True)


invoice = Invoice(invoice_type=InvoiceType.TYPE_A)

serialized = invoice.to_dict()

print(serialized['invice_type'])
# Will print 'TYPE_A'

class Invoice(JsonObject):
	invoice_type = Property(type=InvoiceType)


invoice = Invoice(invoice_type=InvoiceType.TYPE_A)

serializd = invoice.to_dict()
print(serialized['invoice_type'])
# Will print 1

```
### Json Schema generation.

Check test cases for examples.

### Validators.

Check test cases for examples.
