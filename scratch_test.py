import json
import subprocess

req = {
    "display_name": "Test Filter Dashboard",
    "serialized_dashboard": json.dumps({
        "datasets": [
            {
                "name": "test_ds",
                "query": "SELECT 1 AS car"
            }
        ],
        "pages": [
            {
                "name": "p1",
                "layout": [
                    {
                        "widget": {
                            "name": "f1",
                            "spec": {
                                "version": 1,
                                "widgetType": "fieldFilter",
                                "filterDataset": "test_ds",
                                "filterField": "car"
                            }
                        },
                        "position": {"x": 0, "y": 0, "width": 2, "height": 2}
                    }
                ]
            }
        ]
    })
}

with open("scratch_test.json", "w", encoding="utf-8") as f:
    json.dump(req, f)

result = subprocess.run(["databricks", "lakeview", "create", "--json", "@scratch_test.json"], capture_output=True, text=True, encoding="utf-8")
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
