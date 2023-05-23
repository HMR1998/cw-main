import json
import random
import boto3
import time

def lambda_handler(event, context):
    start_time = time.time()
    min_history = event['min_history']
    shots = event['shots']
    buy_sell = event['buy_sell']
    
    min_history = int(min_history)
    shots = int(shots)
    buy_sell = buy_sell
    results_95 = []
    results_99 = []
    date = []
    mean = 0
    std = 0
    average_95 = 0
    average_99 = 0
    
    s3 = boto3.client('s3')
    bucket_name = 'cwbucket1998'
    object_key = 'data_cw'
    response = s3.get_object(Bucket=bucket_name, Key=object_key)

    serialized_data = response['Body'].read().decode('utf-8')
    data_dict = json.loads(serialized_data)
    
    for i, row in enumerate(data_dict[min_history:], start=min_history):
        if buy_sell == 'buy':
            if row['Buy'] == 1:
                date.append(row['Date'])
                close_values = [r['Close'] for r in data_dict[i - min_history:i]]
                percentage_changes = [(close_values[j] - close_values[j-1]) / close_values[j-1] for j in range(1, len(close_values))]
                mean = sum(percentage_changes) / len(percentage_changes)
                std = (sum([(p - mean) ** 2 for p in percentage_changes]) / len(percentage_changes)) ** 0.5
                simulated = [random.gauss(mean, std) for _ in range(shots)]
                simulated.sort(reverse=True)

                var95 = simulated[int(len(simulated) * 0.95)]
                var99 = simulated[int(len(simulated) * 0.99)]
                results_95.append(var95)
                results_99.append(var99)
                average_95 = sum(results_95) / len(results_95)
                average_99 = sum(results_99) / len(results_99)

                    
        elif buy_sell == 'sell':
            if row['Sell'] == 1:
                date.append(row['Date'])
                close_values = [r['Close'] for r in data_dict[i - min_history:i]]
                percentage_changes = [(close_values[j] - close_values[j-1]) / close_values[j-1] for j in range(1, len(close_values))]
                mean = sum(percentage_changes) / len(percentage_changes)
                std = (sum([(p - mean) ** 2 for p in percentage_changes]) / len(percentage_changes)) ** 0.5
                simulated = [random.gauss(mean, std) for _ in range(shots)]
                simulated.sort(reverse=True)

                var95 = simulated[int(len(simulated) * 0.05)]
                var99 = simulated[int(len(simulated) * 0.01)]
                results_95.append(var95)
                results_99.append(var99)
                average_95 = sum(results_95) / len(results_95)
                average_99 = sum(results_99) / len(results_99)
        
        end_time = time.time()
        execution_time = end_time - start_time


        response = {
            'results_95': results_95,
            'results_99': results_99,
            'mean': mean,
            'std': std,
            'date': date,
            'average_95' : average_95,
            'average_99' : average_99,
            'execution_time': execution_time
        }

    return {
        'body': json.dumps(response)
    }
