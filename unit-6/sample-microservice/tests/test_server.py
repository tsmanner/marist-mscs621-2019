# Copyright 2018 Jinho Hwang. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Data API Service Test Suite

Test cases can be run with the following:
nosetests -v --with-spec --spec-color
"""

import unittest
import logging
import json
import server

# Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_405_METHOD_NOT_ALLOWED = 405
HTTP_409_CONFLICT = 409

######################################################################
#  T E S T   C A S E S
######################################################################
class TestDataServer(unittest.TestCase):
    """ Data Service tests """

    def setUp(self):
        self.app = server.app.test_client()
        server.initialize_logging(logging.CRITICAL)
        server.init_db()
        server.data_reset()
        server.data_load({"name": "fido", "category": "dog", "available": True})
        server.data_load({"name": "kitty", "category": "cat", "available": True})

    def test_index(self):
        """ Test the index page """
        resp = self.app.get('/')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertIn('Data Demo REST API Service', resp.data)

    def test_get_data_list(self):
        """ Get a list of Data """
        resp = self.app.get('/data')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertTrue(len(resp.data) > 0)

    def test_get_data(self):
        """ get a single Data """
        resp = self.app.get('/data/2')
        #print 'resp_data: ' + resp.data
        self.assertEqual(resp.status_code, HTTP_200_OK)
        data = json.loads(resp.data)
        self.assertEqual(data['name'], 'kitty')

    def test_get_data_not_found(self):
        """ Get a Data that doesn't exist """
        resp = self.app.get('/data/0')
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)
        data = json.loads(resp.data)
        self.assertIn('was not found', data['message'])

    def test_create_data(self):
        """ Create a new Data """
        # save the current number of Data for later comparrison
        data_count = self.get_data_count()
        # add a new data 
        new_data = {'name': 'sammy', 'category': 'snake', 'available': True}
        data = json.dumps(new_data)
        resp = self.app.post('/data', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_201_CREATED)
        # Make sure location header is set
        location = resp.headers.get('Location', None)
        self.assertNotEqual(location, None)
        # Check the data is correct
        new_json = json.loads(resp.data)
        self.assertEqual(new_json['name'], 'sammy')
        # check that count has gone up and includes sammy
        resp = self.app.get('/data')
        # print 'resp_data(2): ' + resp.data
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(len(data), data_count + 1)
        self.assertIn(new_json, data)

    def test_update_data(self):
        """ Update a Data """
        new_kitty = {'name': 'kitty', 'category': 'tabby', 'available': True}
        data = json.dumps(new_kitty)
        resp = self.app.put('/data/2', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        resp = self.app.get('/data/2', content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        new_json = json.loads(resp.data)
        self.assertEqual(new_json['category'], 'tabby')

    def test_update_data_with_no_name(self):
        """ Update a Data without assigning a name """
        new_data = {'category': 'dog'}
        data = json.dumps(new_data)
        resp = self.app.put('/data/2', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_400_BAD_REQUEST)

    def test_update_data_not_found(self):
        """ Update a Data that doesn't exist """
        new_kitty = {"name": "timothy", "category": "mouse"}
        data = json.dumps(new_kitty)
        resp = self.app.put('/data/0', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)

    def test_delete_data(self):
        """ Delete a Data """
        # save the current number of data for later comparrison
        data_count = self.get_data_count()
        # delete a data
        resp = self.app.delete('/data/2', content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(len(resp.data), 0)
        new_count = self.get_data_count()
        self.assertEqual(new_count, data_count - 1)

    def test_create_data_with_no_name(self):
        """ Create a Data without a name """
        new_data = {'category': 'dog'}
        data = json.dumps(new_data)
        resp = self.app.post('/data', data=data, content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_400_BAD_REQUEST)

    def test_create_data_no_content_type(self):
        """ Create a Data with no Content-Type """
        new_data = {'category': 'dog'}
        data = json.dumps(new_data)
        resp = self.app.post('/data', data=data)
        self.assertEqual(resp.status_code, HTTP_400_BAD_REQUEST)

    def test_get_nonexisting_data(self):
        """ Get a nonexisting Data """
        resp = self.app.get('/data/5')
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)

    def test_call_create_with_an_id(self):
        """ Call create passing anid """
        new_data = {'name': 'sammy', 'category': 'snake'}
        data = json.dumps(new_data)
        resp = self.app.post('/data/1', data=data)
        self.assertEqual(resp.status_code, HTTP_405_METHOD_NOT_ALLOWED)

    def test_query_data_list(self):
        """ Query Data by category """
        resp = self.app.get('/data', query_string='category=dog')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertTrue(len(resp.data) > 0)
        self.assertIn('fido', resp.data)
        self.assertNotIn('kitty', resp.data)
        data = json.loads(resp.data)
        query_item = data[0]
        self.assertEqual(query_item['category'], 'dog')

    def test_purchase_a_data(self):
        """ Purchase a Data """
        resp = self.app.put('/data/2/purchase', content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        resp = self.app.get('/data/2', content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        data_data = json.loads(resp.data)
        self.assertEqual(data_data['available'], False)

    def test_purchase_not_available(self):
        """ Purchase a data that is not available """
        resp = self.app.put('/data/2/purchase', content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        resp = self.app.put('/data/2/purchase', content_type='application/json')
        self.assertEqual(resp.status_code, HTTP_400_BAD_REQUEST)
        resp_json = json.loads(resp.get_data())
        self.assertIn('not available', resp_json['message'])


######################################################################
# Utility functions
######################################################################

    def get_data_count(self):
        """ save the current number of data """
        resp = self.app.get('/data')
        self.assertEqual(resp.status_code, HTTP_200_OK)
        data = json.loads(resp.data)
        return len(data)


######################################################################
#   M A I N
######################################################################
if __name__ == '__main__':
    unittest.main()
