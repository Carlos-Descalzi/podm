import unittest
from podm import JsonObject, Property, Handler
from collections import OrderedDict
from datetime import datetime

class Entity(JsonObject):
	"""
	A base class for the object model
	"""
	oid = Property('oid')
	created = Property('created', default=datetime.now)

class Company(Entity):
	"""
	This class represents a kitchen.
	"""
	company_name = Property('company-name')
	description = Property('description')        

	def __init__(self,**kwargs):
		super(Company, self).__init__(**kwargs)
		# I use this field only for checking that the field "description"
		# is accessed from the getter instead of using default accessor.
		self._used_getter = False

	def get_description(self):
		# Set _used_getter to True if this getter has been called. 
		self._used_getter = True
		return self._description


class Sector(Entity):
	"""
	This class represents an order (serving book).
	"""
	employees = Property('employees')

	def __init__(self,**kwargs):
		super(Sector, self).__init__(**kwargs)
		# Default value for _employees
		self._employees = []

class Employee(Entity):
	"""
	This class represents an order run. 
	"""
	recipe_id = Property('recipe-id')


class DateTimeHandler(Handler):

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

class TestObject(JsonObject):

	date_time = Property('date-time',handler=DateTimeHandler(),default=datetime.now)

	def __init__(self,**kwargs):
		JsonObject.__init__(self,**kwargs)
		self._deserialized = False

	def _after_deserialize(self):
		self._deserialized = True

class TestDKJSON(unittest.TestCase):

	def test_properties(self):
		self.assertEqual(set(Entity.property_names()),set(['oid','created']))
		self.assertEqual(set(Company.property_names()),set(['oid','created','description','company_name']))
		self.assertEqual(set(Company.json_field_names()),set(['oid','created','description','company-name']))

	def test_accessors(self):
		kitchen = Company()
		kitchen.oid = '123123123'
		kitchen.company_name = 'master'
		kitchen.description = 'master kitchen'

		self.assertEqual('master',kitchen.company_name)

		self.assertEqual('master',kitchen.get_company_name())
		self.assertEqual('master kitchen',kitchen.description)
		self.assertTrue(kitchen._used_getter)
		kitchen._used_getter = False
		self.assertEqual('master kitchen',kitchen.get_description())
		self.assertTrue(kitchen._used_getter)

		kitchen.set_description('desc 2')
		self.assertEqual('desc 2',kitchen.description)
		self.assertEqual('desc 2',kitchen._description)


	def test_to_dict(self):
		kitchen = Company()
		kitchen.company_name = 'master'
		kitchen.description = 'master kitchen'

		data = kitchen.to_dict()

		self.assertTrue('py/object' in data)
		self.assertTrue('oid' in data)
		self.assertTrue('created' in data)
		self.assertIsNotNone(data['created'])
		self.assertTrue('company-name' in data)
		self.assertEqual('master', data['company-name'])
		self.assertTrue('description' in data)
		self.assertEqual('master kitchen',data['description'])


	def test_deserialize(self):
		data = {
			'py/object' : 'Company',
			'py/state'	: {
				'company-name' : 'master',
				'description'  : 'some description'
			}

		}
		kitchen = JsonObject.parse(data,__name__)
		self.assertTrue(isinstance(kitchen,Company))
		self.assertEqual('master',kitchen.company_name)
		self.assertEqual('some description',kitchen.description)

	def test_deserialize_2(self):
		data = {
			'py/object' : 'Company',
			'company-name' : 'master',
			'description'  : 'some description'
		}
		kitchen = JsonObject.parse(data,__name__)
		self.assertTrue(isinstance(kitchen,Company))
		self.assertEqual('master',kitchen.company_name)
		self.assertEqual('some description',kitchen.description)

	def test_deserialize_3(self):
		data = {
			'company-name' : 'master',
			'description'  : 'some description'
		}
		kitchen = Company.from_dict(data)
		self.assertTrue(isinstance(kitchen,Company))
		self.assertEqual('master',kitchen.company_name)
		self.assertEqual('some description',kitchen.description)

	def test_kwargs_constructor(self):
		kitchen = Company(
			company_name = 'master',
			description = 'some description'
		)

		# check accessors
		self.assertEqual('master',kitchen.company_name)
		self.assertEqual('some description',kitchen.description)

		# check internal state
		self.assertEqual('master',kitchen._company_name)
		self.assertEqual('some description',kitchen._description)

	def test_collections(self):
		serving_book = Sector()
		serving = Employee(oid='1234',recipe_id='xx1')

		serving_book.employees.append(serving)

		data = serving_book.to_dict()

		self.assertTrue(isinstance(data['employees'],list))

		for serving in data['employees']:
			self.assertEqual('1234',serving['oid'])
			self.assertEqual('xx1',serving['recipe-id'])

		new_serving_book = Sector.from_dict(data)

		self.assertTrue(isinstance(new_serving_book.employees,list))
		self.assertEqual(1,len(new_serving_book.employees))

		self.assertTrue(isinstance(new_serving_book.employees[0],Employee))
		self.assertEqual('1234',new_serving_book.employees[0].oid)
		self.assertEqual('xx1',new_serving_book.employees[0].recipe_id)

	def test_default(self):
		k1 = Company()
		k2 = Company()

		self.assertIsNotNone(k1.created)
		self.assertIsNotNone(k2.created)

		self.assertNotEqual(k1.created,k2.created)

	def test_custom_objects(self):

		kitchen = Company(created=datetime.now())

		kitchen_dict = kitchen.to_dict()

		self.assertTrue('created' in kitchen_dict)
		self.assertTrue(isinstance(kitchen_dict['created'],datetime))

	def test_handler(self):

		obj = TestObject()

		obj_dict = obj.to_dict()
		self.assertTrue(isinstance(obj_dict['date-time'],dict))
		self.assertTrue('year' in obj_dict['date-time'])


		obj2 = TestObject.from_dict(obj_dict)
		self.assertTrue(isinstance(obj2.date_time,datetime))

		self.assertTrue(obj2._deserialized)


	def test_handler_2(self):

		class BoolHandler(Handler):
			def encode(self, val):
				return val

			def decode(self, val):
				return str(val).lower() == 'true' \
					if val is not None else None

		bool_handler = BoolHandler()

		class TestObject2(JsonObject):
			some_boolean_1 = Property(handler=bool_handler)
			some_boolean_2 = Property(handler=bool_handler)
			some_boolean_3 = Property(handler=bool_handler)

		obj_dict = {
			'some_boolean_1' : 'True',
			'some_boolean_2' : 'false',
			'some_boolean_3' : None
		}

		obj = TestObject2.from_dict(obj_dict)

		self.assertTrue(isinstance(obj.some_boolean_1,bool))
		self.assertTrue(isinstance(obj.some_boolean_2,bool))
		self.assertIsNone(obj.some_boolean_3)

	def test_str(self):
		class TestObject3(JsonObject):
			val1 = Property()
			val2 = Property()
			val3 = Property()

		obj_dict = {
			'val1' : 'Hi',
			'val2' : True,
			'val3' : None
		}

		obj = TestObject3.from_dict(obj_dict)

		obj_str = str(obj)

		self.assertEqual(
			'TestObject3:val1=Hi;val2=True;val3=None',
			obj_str
		)





if __name__ == '__main__':
	unittest.main()
