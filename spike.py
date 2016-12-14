#!/usr/bin/env python

from oauth2client.client import GoogleCredentials
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient import discovery
from googleapiclient import errors
from flask import Flask, request
from flask_restful import Resource, Api

import os
import json

port = 8003
if 'PORT' in os.environ:
    port = int(os.getenv("PORT"))

Flask.get = lambda self, path: self.route(path, methods=['get'])

app = Flask(__name__)
api = Api(app)

# Make the call.

class GoogleMachineLearningModel(Resource):
    def __init__(self):
        # Store your full project ID in a variable in the format the API needs.
        projectID = 'projects/{}'.format(os.environ['GCP_PROJECT'])
        services = json.loads(os.environ['VCAP_SERVICES'])
        if 'google-ml-apis' in services:
            for service in services['google-ml-apis']:
                    if s.get('name') == 'prediction-service'
                        # authenticate
                        binding = s.get('credentials')
                        credentials = ServiceAccountCredentials(binding.get('service_account_email'), NEED SIGNER,
                            binding.get('private_key_id'), binding.get('client_id')
                        # Build a representation of the Cloud ML API.
                        ml = discovery.build('ml', 'v1beta1', credentials=credentials)
        else:
            raise EnvironmentError(1,"Service not bound in environment")
    def put(self, name):
        try:
            # Create a dictionary with the fields from the request body.
            requestDict = {'name': name,
                'description': 'a spike to experiment with connecting to the ML APIs'}

            # Create a request to call projects.models.create.
            request = ml.projects().models().create(
            parent=projectID, body=requestDict)
            response = request.execute()
            return response
        except errors.HttpError, err:
            # Something went wrong, print out some information.
            return 'There was an error creating the model. Check the details:' + err._get_reason()

    def delete(self, name):
        try:
            # Create a dictionary with the fields from the request body.
            modelName = 'projects/fe-cdantonio/models/%s' % name

            # Create a request to call projects.models.create.
            request = ml.projects().models().delete( name=modelName )
            response = request.execute()
            return response
        except errors.HttpError, err:
            # Something went wrong, print out some information.
            return 'There was an error creating the model. Check the details:' + err._get_reason()

    def get(self, name):
        try:
            modelName = 'projects/fe-cdantonio/models/%s' % name

            # Create a request to call projects.models.create.
            request = ml.projects().models().get( name=modelName )
            response = request.execute()
            return response
        except errors.HttpError, err:
            # Something went wrong, print out some information.
            return 'There was an error creating the model. Check the details:' + err._get_reason()

api.add_resource(GoogleMachineLearningModel, '/model/<string:name>')

@app.get('/')
def list():
    try:
        # Create a dictionary with the fields from the request body.
        # Create a request to call projects.models.create.
        request = ml.projects().models().list( parent=projectID )
        response = request.execute()
        if response:
            models = "<ul>"
            for i, v in enumerate(response['models']):
               models = models + v['name'] + "&nbsp;&nbsp;&nbsp;" + v['description'] + '<br> '
            models = models + "</ul>"
            return "Models available: " + models
        return "No models"
    except errors.HttpError, err:
        # Something went wrong, print out some information.
        return 'There was an error creating the model. Check the details:' + err._get_reason()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
