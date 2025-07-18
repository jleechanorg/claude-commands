import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

from integration_test_lib import IntegrationTestSetup
from main import create_app

# Load test data
with open("data/sariel_campaign_prompts.json") as f:
    sariel_data = json.load(f)

app = create_app()
app.config["TESTING"] = True
client = app.test_client()
user_id = "test-cassian-" + sys.argv[1]

# Create campaign
initial_prompt = sariel_data["prompts"][0]
campaign_data = {
    "prompt": initial_prompt["input"],
    "title": "Cassian Test " + sys.argv[1],
    "selected_prompts": ["narrative", "mechanics"],
}

response = client.post(
    "/api/campaigns",
    headers=IntegrationTestSetup.create_test_headers(user_id),
    data=json.dumps(campaign_data),
)

if response.status_code == 201:
    campaign_id = response.get_json()["campaign_id"]

    # Run Cassian interaction
    cassian_prompt = sariel_data["prompts"][2]  # The Cassian problem prompt
    interaction_data = {"input": cassian_prompt["input"]}

    response = client.post(
        f"/api/campaigns/{campaign_id}/interaction",
        headers=IntegrationTestSetup.create_test_headers(user_id),
        data=json.dumps(interaction_data),
    )

    if response.status_code == 200:
        result = response.get_json()
        narrative = result.get("narrative", "")
        print(
            json.dumps(
                {
                    "success": True,
                    "cassian_mentioned": "cassian" in narrative.lower(),
                    "narrative_length": len(narrative),
                }
            )
        )
    else:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": f"Interaction failed: {response.status_code}",
                }
            )
        )
else:
    print(
        json.dumps(
            {
                "success": False,
                "error": f"Campaign creation failed: {response.status_code}",
            }
        )
    )
