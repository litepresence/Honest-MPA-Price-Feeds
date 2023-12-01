import json
from requests import get
import math

url = "https://api.github.com/repos/{}/contributors"

repos = [
    "bitshares/bitshares-core",
    "bitshares/bitsharesjs",
    "bitshares/python-bitshares",
    "bitshares/bitshares-ui",
    "graphene-blockchain/graphene-core",
]

final_data = {}

for repo in repos:
    data = json.loads(get(url.format(repo)).text)
    for user in data:
        if user["login"] not in final_data:
            final_data[user["login"]] = {
                "contributions": {repo: user["contributions"]},
                "total_contrib": user["contributions"],
                "log_contrib": math.log(user["contributions"] + 1),
                "bitshares_name": "",
                "bitshares_id": "",
            }
        else:
            final_data[user["login"]]["contributions"][repo] = user["contributions"]
            final_data[user["login"]]["total_contrib"] += user["contributions"]
            final_data[user["login"]]["log_contrib"] = math.log(
                final_data[user["login"]]["total_contrib"] + 1
            )

sorted_keys = sorted(list(final_data.keys()))
final_data = {i: final_data[i] for i in sorted_keys}

print(json.dumps(final_data, indent=4))
