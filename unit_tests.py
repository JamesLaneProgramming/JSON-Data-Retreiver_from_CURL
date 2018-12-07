import unittest
import application

class user_create_test_case(unittest.TestCase):
    def setUp(self):
        application.application.testing = True
        application.load_user('212')
    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
