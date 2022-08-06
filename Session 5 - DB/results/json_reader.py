import json


with open('strategy_performance.json', encoding='utf-8') as file:
    data = json.load(file)
data = json.loads(data)

# print(data)

avg_r = 0
p_win = 0

stats = []

for strategy in data:

    count = 0
    for symbol in strategy.keys():
        for timeframe in strategy[symbol].keys():
            for trade in strategy[symbol][timeframe].keys():
                avg_r += strategy[symbol][timeframe][trade]['avg_r']
                p_win += strategy[symbol][timeframe][trade]['p_win']
                count += 1

    avg_r = avg_r / count
    p_win = p_win / count
    stats.append({
        list(strategy.keys())[0]: {
            'avg_r': avg_r,
            'p_win': p_win,
        }
    })

print(stats)
