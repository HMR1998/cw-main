#!/usr/bin/env python3
import os
import logging
import boto3
import time
import http.client
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, render_template

app = Flask(__name__)

def doRender(tname, values={}):
	if not os.path.isfile( os.path.join(os.getcwd(), 'templates/'+tname) ): #No such file
		return render_template('main.htm')
	return render_template(tname, **values) 

@app.route('/')
def index():
    return render_template('form.htm')

@app.route('/submit', methods=['POST'])
def initialisation():
    service = request.form['services']
    resources = int(request.form['resources'])
    start = time.time()
    
    if service == 'EC2':
        launch_ec2_instances(resources)
        return render_template(message = f'{resources} EC2 instances launched. Elapsed Time: {time.time() - start}')
    elif service == 'Lambda':
        launch_lambda(resources)
        return render_template(message = f'{resources} Lambda functions launched. Elapsed Time: {time.time() - start}')
    else:
        return render_template(message = 'Invalid service selected.')
    
    return print( "Elapsed Time: ", time.time() - start)

def launch_ec2_instances(num_instances):
    region = 'us-east-1'
    ec2 = boto3.client('ec2', region)

    response = ec2.run_instances(
        ImageId='ami-07a10007fc2238f96',
        InstanceType='t2.micro',
        MaxCount=num_instances,
        MinCount=num_instances
    )

def lambda_initialization(id):
    count = 1000
    
    try:
        host = "tm3u2wwp4i.execute-api.us-east-1.amazonaws.com"
        c = http.client.HTTPSConnection(host)
        json= '{ "key1": ' + str(count) + '}'
        c.request("POST", "/default/lambda_initialization", json)

        response = c.getresponse()
        data = response.read().decode('utf-8')
        print( data, " from Thread", id )
    except IOError:
        print( 'Failed to open ', host ) # Is the Lambda address correct?
    print(data+" from "+str(id)) # May expose threads as completing in a different order
    return "page "+str(id)

def launch_lambda(num_instances):
    with ThreadPoolExecutor() as executor:
        results = executor.map(lambda_initialization, range(num_instances))
    return results


# catch all other page requests - doRender checks if a page is available (shows it) or not (index)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def mainPage(path):
	return doRender(path)

@app.errorhandler(500)
# A small bit of error handling
def server_error(e):
    logging.exception('ERROR!')
    return """
    An  error occurred: <pre>{}</pre>
    """.format(e), 500

if __name__ == '__main__':
    # Entry point for running on the local machine
    # On GAE, endpoints (e.g. /) would be called.
    # Called as: gunicorn -b :$PORT index:app,
    # host is localhost; port is 8080; this file is index (.py)
    app.run(host='127.0.0.1', port=8080, debug=True)

