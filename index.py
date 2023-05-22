#!/usr/bin/env python3
import os
from urllib.parse import urlencode

import requests
os.environ['AWS_SHARED_CREDENTIALS_FILE']='./cred'
import os
import logging
import random
import boto3
import time
import http.client
from concurrent.futures import ThreadPoolExecutor
# from data import data
import statistics
import numpy as np
import json
import urllib
from datetime import date, timedelta
from pandas_datareader import data as pdr
import yfinance as yf
yf.pdr_override()

from flask import Flask, redirect, request, render_template, session, url_for

app = Flask(__name__)
app.secret_key = 'password'

def doRender(tname, values={}):
	if not os.path.isfile( os.path.join(os.getcwd(), 'templates/'+tname) ): #No such file
		return render_template('form.htm')
	return render_template(tname, **values) 

@app.route('/')
def index():
    return render_template('form.htm')


@app.route('/results')
def result_page():
    
    service = session.get('service')
    resources = session.get('resources')
    
    return render_template('results.htm', service=service, resources=resources)

@app.route('/submit', methods=['POST'])
def initialisation():
    service = request.form['services']
    resources = int(request.form['resources'])
    min_history = 100
    shots = 200
    buy_sell = 'buy'
    eta_time = []
    
    if service == 'EC2':
        launch_ec2_instances(resources)
    elif service == 'Lambda':
        start_time = time.time()
        w = launch_lambda(resources, min_history, shots, buy_sell)
        end_time = time.time()
        eta_time = end_time - start_time
        # eta_time.append(w[0]['execution_time'])
    else:
        return render_template('form.htm', message='Invalid service selected.')
    
    session['service'] = service
    session['resources'] = resources
    session['eta_time'] = eta_time
    
    return redirect(url_for('result_page'))
        
def launch_ec2_instances(num_instances):
    region = 'us-east-1'
    ec2 = boto3.client('ec2', region)

    response = ec2.run_instances(
        ImageId='ami-07a10007fc2238f96',
        InstanceType='t2.micro',
        MaxCount=num_instances,
        MinCount=num_instances
    )
import http.client

def lambda_initialization(min_history, shots, buy_sell):
        c = http.client.HTTPSConnection("tm3u2wwp4i.execute-api.us-east-1.amazonaws.com")
        json_data = '{ "min_history": "' + str(min_history) + '", "shots": "' + str(shots) + '", "buy_sell": "' + str(buy_sell) + '"}'
        c.request("POST", "/default/lambda_initialization", json_data)
        response = c.getresponse()
        data = response.read().decode('utf-8')
        parsed_data = json.loads(data)
        parsed_data = json.loads(parsed_data['body'])
        print( parsed_data, " from Thread", id )
        return(parsed_data)

def launch_lambda(num_instances, min_history, shots, buy_sell):
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda_initialization, [min_history] * num_instances, 
                                    [shots] * num_instances, [buy_sell] * num_instances))
    return results

def data():
    today = date.today()
    decadeAgo = today - timedelta(days=1095)

    data = pdr.get_data_yahoo('BP.L', start=decadeAgo, end=today)

    data['Buy'] = 0
    data['Sell'] = 0

    for i in range(2, len(data)):
        body = 0.01

        # Three Soldiers
        if (
            (data.Close[i] - data.Open[i]) >= body and
            data.Close[i] > data.Close[i-1] and
            (data.Close[i-1] - data.Open[i-1]) >= body and
            data.Close[i-1] > data.Close[i-2] and
            (data.Close[i-2] - data.Open[i-2]) >= body
        ):
            data.at[data.index[i], 'Buy'] = 1

        # Three Crows
        if (
            (data.Open[i] - data.Close[i]) >= body and
            data.Close[i] < data.Close[i-1] and
            (data.Open[i-1] - data.Close[i-1]) >= body and
            data.Close[i-1] < data.Close[i-2] and
            (data.Open[i-2] - data.Close[i-2]) >= body
        ):
            data.at[data.index[i], 'Sell'] = 1
            
    data.reset_index(drop=False, inplace=True)
    data['Date'] = data['Date'].dt.strftime('%Y-%m-%d')
    data = data.to_dict(orient='records')
            
    return data

def s3_storage(d):
    json_data = json.dumps(d)
    
    s3 = boto3.client('s3')
    bucket_name = 'cwbucket1998'
    object_key = 'data_cw'
    json_data = json_data
    
    return s3.put_object(Body=json_data, Bucket=bucket_name, Key=object_key)

data_dict = data()
s3_storage(data_dict)


@app.route('/results', methods=['POST'])
def get_calculations():
    service = session.get('service')
    resources = session.get('resources')
    eta_time = session.get('eta_time')
    min_history = int(request.form['min_history'])
    shots = int(request.form['shots'])
    buy_sell = request.form['buy_sell']
    results_95 = []
    results_99 = []
    date = []
    execution_time = []
    average_95 = []
    average_99 = []
    
    for resource in range(resources):
        if service == 'EC2':
            start_time = time.time()
            for i, row in enumerate(data_dict[min_history:], start=min_history):
                if buy_sell == 'buy':
                    if row['Buy'] == 1:
                        date.append(row['Date'])
                        close_values = [r['Close'] for r in data_dict[i - min_history:i]]
                        percentage_changes = [(close_values[j] - close_values[j-1]) / close_values[j-1] for j in range(1, len(close_values))]
                        mean = np.mean(percentage_changes)
                        std = np.std(percentage_changes)
                        simulated = [random.gauss(mean, std) for _ in range(shots)]
                        simulated.sort(reverse=True)
    
                        var95 = simulated[int(len(simulated) * 0.95)]
                        var99 = simulated[int(len(simulated) * 0.99)]
                        results_95.append(var95)
                        results_99.append(var99) 
                    
                elif buy_sell == 'sell':
                    if row['Sell'] == 1:
                        date.append(row['Date'])
                        close_values = [r['Close'] for r in data_dict[i - min_history:i]]
                        percentage_changes = [(close_values[j] - close_values[j-1]) / close_values[j-1] for j in range(1, len(close_values))]
                        mean = np.mean(percentage_changes)
                        std = np.std(percentage_changes)
                        simulated = [random.gauss(mean, std) for _ in range(shots)]
                        simulated.sort(reverse=True)
    
                        var95 = simulated[int(len(simulated) * 0.05)]
                        var99 = simulated[int(len(simulated) * 0.01)]
                        results_95.append(var95)
                        results_99.append(var99) 

            average_95.append(np.mean(results_95))
            average_99.append(np.mean(results_99))
            end_time = time.time()
            execution_time.append(end_time - start_time)
        elif service == 'Lambda':
            # FOR PARALELL LAMBDA
            x = launch_lambda(resources, min_history, shots, buy_sell)
            results_95 = x[0]['results_95']
            results_99 = x[0]['results_99']
            mean = x[0]['mean']
            std = x[0]['std']
            date = x[0]['date']
            average_95.append(x[0]['average_95'])
            average_99.append(x[0]['average_99'])
            execution_time.append(x[0]['execution_time'])
                
            # FOR SERIAL LAMBDA
            # min_history = request.form.get('min_history')
            # shots = request.form.get('shots')
            # buy_sell = request.form.get('buy_sell')
            # c = http.client.HTTPSConnection("tm3u2wwp4i.execute-api.us-east-1.amazonaws.com")
            # for resource in range(resources):
            #     json_data = '{ "min_history": "' + min_history + '", "shots": "' + shots + '", "buy_sell": "' + buy_sell + '"}'
            #     c.request("POST", "/default/lambda_initialization", json_data)
            #     response = c.getresponse()
            #     data = response.read().decode('utf-8')
            #     parsed_data = json.loads(data)
            #     parsed_data = json.loads(parsed_data['body'])
            #     print( parsed_data, " from Thread", id )
                
            #     results_95 = parsed_data['results_95']
            #     results_99 = parsed_data['results_99']
            #     mean = parsed_data['mean']
            #     std = parsed_data['std']
            #     date = parsed_data['date']
            # average_95.append(np.mean(parsed_data['results_95']))
            # average_99.append(np.mean(parsed_data['results_99']))
            # execution_time.append(parsed_data['execution_time'])
                       
    chart_95 = [round(x, 3) for x in results_95]
    chart_99 = [round(x, 3) for x in results_99]

    chart_95_str = [str(x) for x in chart_95]
    chart_99_str = [str(x) for x in chart_99]
    chart_dates =  list(range(1, len(date) + 1))
    chart_date =  [str(x) for x in chart_dates]

    url_template = 'https://image-charts.com/chart?cht=lc&chd=t:{chart_95}|{chart_99}&chs=500x300&chxt=x,y&chxl=0:|&chco=FF2027,FFFF10&chds=a&chdl=var95|var99'

    chart_url = url_template.format(chart_95=','.join(chart_95_str), chart_99=','.join(chart_99_str), chart_date='|'.join(map(urllib.parse.quote,chart_date)))

    return render_template('results.htm', results_95=results_95, results_99=results_99,mean=mean, 
                           std=std, date=date, resource=id, average_95=average_95, average_99=average_99,
                           execution_time=execution_time, chart_url=chart_url, service = service, eta_time=eta_time)
    
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

