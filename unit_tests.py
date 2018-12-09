import unittest
import application

class user_create_test_case(unittest.TestCase):
    def add(x, y):
        return x + y
    
    def add_test():
        test_actual = add(1, 9)
        test_expectation = 10
        assert(test_actual, test_expectation)
    
    def setUp(self):
        application.application.testing = True
        application.load_user('212')
    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
