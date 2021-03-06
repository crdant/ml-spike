#!/usr/bin/env python

from oauth2client.client import GoogleCredentials
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.crypt import RsaSigner

from googleapiclient import discovery
from googleapiclient import errors
from googleapiclient.http import MediaInMemoryUpload
from googleapiclient.http import MediaIoBaseDownload

from flask import Flask, request
from flask_restful import Resource, Api

import os
import time
import json
import base64
import StringIO

port = 8003
if 'PORT' in os.environ:
    port = int(os.getenv("PORT"))

Flask.get = lambda self, path: self.route(path, methods=['get'])

app = Flask(__name__)
api = Api(app)

credentials=None
ml=None
storage=None
storageBinding=None

# Store your full project ID in a variable in the format the API needs.
projectID = 'projects/{0}'.format(os.environ['GCP_PROJECT'])
services = json.loads(os.environ['VCAP_SERVICES'])

if 'google-ml-apis' in services:
    for service in services['google-ml-apis']:
            if service.get('name') == 'prediction-apis':
                # authenticate
                mlBinding = service.get('credentials')
                service_account = json.loads(base64.b64decode(mlBinding.get('PrivateKeyData')))
                credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account)
                # Build a representation of the Cloud ML API.
                ml = discovery.build('ml', 'v1beta1', credentials=credentials)
else:
    raise EnvironmentError(1,"Learning service not bound in environment")

if 'google-storage' in services:
    for service in services['google-storage']:
            if service.get('name') == 'model-storage':
                # authenticate
                storageBinding = service.get('credentials')
                service_account = json.loads(base64.b64decode(storageBinding.get('PrivateKeyData')))
                credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account)
                # Build a representation of the Cloud Storage API.
                storage = discovery.build('storage', 'v1', credentials=credentials)
else:
    raise EnvironmentError(1,"Storage service not bound in environment")

# Make the call.
class GoogleMachineLearningModel(Resource):
    def put(self, name):
        try:
            # Create a dictionary with the fields from the request body.
            requestBody = {'name': name,
                'description': 'a spike to experiment with connecting to the ML APIs'}
            # Create a request to call projects.models.create.
            request = ml.projects().models().create(
                parent=projectID, body=requestBody)
            response = request.execute()
            return response
        except errors.HttpError, err:
            # Something went wrong, print out some information.
            return 'There was an error creating the model. Check the details:' + err._get_reason()

    def delete(self, name):
        try:
            # Create a dictionary with the fields from the request body.
            modelName = '{0}/models/{1}'.format(projectID, name)

            # Create a request to call projects.models.create.
            request = ml.projects().models().delete( name=modelName )
            response = request.execute()
            return response
        except errors.HttpError, err:
            # Something went wrong, print out some information.
            return 'There was an error deleting the model. Check the details:' + err._get_reason()

    def get(self, name):
        try:
            modelName = '{0}/models/{1}'.format(projectID, name)

            # Create a request to call projects.models.create.
            request = ml.projects().models().get( name=modelName )
            response = request.execute()
            return response
        except errors.HttpError, err:
            # Something went wrong, print out some information.
            return 'There was an error getting the model. Check the details:' + err._get_reason()

api.add_resource(GoogleMachineLearningModel, '/model/<string:name>')

class GoogleMachineLearningJob(Resource):
    def post(self, name):
        try:
            # Create a dictionary with the fields from the request body.
            jobId = "{0}_{1}_{2}".format(name, time.strftime('%Y%m%d'), time.strftime('%S%M%H'))
            requestBody = {
                   "jobId": jobId,
                   "trainingInput": {
                       "args": ["--train_dir=gs://{0}/{1}/train".format(storageBinding['bucket_name'], jobId)],
                       "packageUris": ["gs://fe-cdantonio-ml/mnist_crdant_20161215_0117292/454e901f09767005b057fd41cb223de84329b09d/trainer-0.0.0.tar.gz"],
                       "pythonModule": "trainer.task",
                       "region": "us-central1"
                   }
                }
            # Create a request to call projects.models.create.
            request = ml.projects().jobs().create(
                parent=projectID, body=requestBody)
            response = request.execute()
            return response
        except errors.HttpError, err:
            # Something went wrong, print out some information.
            return 'There was an error creating the job. Check the details:' + err._get_reason()

    def delete(self, name):
        try:
            name = '{0}/jobs/{1}'.format(projectID, name)

            # Create a request to call projects.models.create.
            request = ml.projects().jobs().cancel( name=name, body={} )
            response = request.execute()
            return response
        except errors.HttpError, err:
            # Something went wrong, print out some information.
            return 'There was an error deleting the job. Check the details:' + err._get_reason()

    def get(self, name):
        try:
            jobName = '{0}/jobs/{1}'.format(projectID, name)

            # Create a request to call projects.models.create.
            request = ml.projects().jobs().get( name=jobName )
            response = request.execute()
            return response
        except errors.HttpError, err:
            # Something went wrong, print out some information.
            return 'There was an error getting the job. Check the details:' + err._get_reason()

api.add_resource(GoogleMachineLearningJob, '/job/<string:name>')

class GoogleStorageObject(Resource):
    def __init__(self):
        self.bucketName=storageBinding.get('bucket_name')
    def put(self, name):
        try:
            # Create a dictionary with the fields from the request body.
            requestBody = {'name': name }
            objectBody = MediaInMemoryUpload("hello world", mimetype="text/plain")
            request = storage.objects().insert(bucket=self.bucketName, media_body=objectBody, body=requestBody)
            response = request.execute()
            return response
        except errors.HttpError, err:
            # Something went wrong, print out some information.
            return 'There was an error creating the object. Check the details:' + err._get_reason()

    def delete(self, name):
        try:
            request = storage.objects().delete(bucket=self.bucketName, object=name)
            response = request.execute()
            return response
        except errors.HttpError, err:
            # Something went wrong, print out some information.
            return 'There was an error deleting the object. Check the details:' + err._get_reason()

    def get(self, name):
        try:
            request = storage.objects().get_media(bucket=self.bucketName, object=name)
            responseBuffer = StringIO.StringIO()
            content = MediaIoBaseDownload(responseBuffer, request)
            download_complete = False
            error_counter = 0

            while not download_complete:
                    progress, download_complete = content.next_chunk()

            return responseBuffer.getvalue()
        except errors.HttpError, err:
            # Something went wrong, print out some information.
            return 'There was an error getting the object. Check the details:' + err._get_reason()

api.add_resource(GoogleStorageObject, '/object/<string:name>')

@app.get('/')
def list():
    try:
        request = ml.projects().models().list( parent=projectID )
        response = request.execute()
        if response:
            models = "<h4>Models</h4><ul>"
            for i, v in enumerate(response['models']):
               models = models + v['name'] + "&nbsp;&nbsp;&nbsp;" + v['description'] + '<br> '
            models = models + "</ul>"
        else:
            models = "<h4>No models</h4><br/>"

        request = storage.objects().list(bucket=storageBinding.get("bucket_name"))
        response = request.execute()
        if response:
            items = "<h4>Items</h4><ul>"
            for i, v in enumerate(response['items']):
               items = items + v['name'] + "&nbsp;&nbsp;&nbsp;" + v['contentType'] + '<br> '
            items = items + "</ul>"
        else:
            items = "<h4>No files</h4><br/>"

        result = models + items

        return result

    except errors.HttpError, err:
        # Something went wrong, print out some information.
        return 'There was an error creating the model. Check the details:' + err._get_reason()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)
