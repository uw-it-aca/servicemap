from django.test import TestCase
from oauth_provider.models import Consumer
import json
import hashlib
import time
import random


class TestViews(TestCase):
    def setUp(self):
        consumer_name = "Test client"
        key = hashlib.sha1("{0} - {1}".format(random.random(),
                                              time.time())).hexdigest()
        secret = hashlib.sha1("{0} - {1}".format(random.random(),
                                                 time.time())).hexdigest()
        consumer = Consumer.objects.create(name=consumer_name,
                                           key=key,
                                           secret=secret)

        header = 'OAuth oauth_version="1.0", oauth_signature_method="' +\
                 'PLAINTEXT", oauth_nonce="requestnonce", oauth_timestamp=' +\
                 '"%s", oauth_consumer_key="%s", oauth_signature="%s&' \
                 % (str(int(time.time())), key, secret)
        self.client.defaults['Authorization'] = header

    def test_service_basic(self):
        data = {
            "name": "Test Service #1",
        }
        response = self.client.post("/api/v1/service",
                                    json.dumps(data),
                                    content_type="application/json",
                                    )

        self.assertEquals(response.status_code, 201)

        response = self.client.get("/api/v1/service/Test%20Service%20%231")
        self.assertEquals(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEquals(data["name"], "Test Service #1")
        self.assertEquals(data["notes"], "")
        self.assertEquals(data["hosts"], [])
        self.assertEquals(data["prereqs"], [])

        data = {
            "name": "Test Service #1",
            "notes": "has some concerns...",
        }
        response = self.client.post("/api/v1/service",
                                    json.dumps(data),
                                    content_type="application/json",
                                    )

        self.assertEquals(response.status_code, 201)

        response = self.client.get("/api/v1/service/Test%20Service%20%231")
        self.assertEquals(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEquals(data["name"], "Test Service #1")
        self.assertEquals(data["notes"], "has some concerns...")
        self.assertEquals(data["hosts"], [])
        self.assertEquals(data["prereqs"], [])

    def test_service_full(self):
        data = {
            "name": "TestService2",
            "prereqs": ["sws-dev", "pws-dev", "made-up-dev"],
            "hosts": [
                {"name": "ts-app01", "role": "Application Server"},
                {"name": "ts-app02", "role": "Application Server"},
                {"name": "ts-app03", "role": "Application Server"},
                {"name": "ts-app04", "role": "Application Server"},
                {"name": "ts-db01", "role": "Database Server"},
            ]
        }

        response = self.client.post("/api/v1/service",
                                    json.dumps(data),
                                    content_type="application/json",
                                    )

        self.assertEquals(response.status_code, 201)

        response = self.client.get("/api/v1/service/TestService2")
        self.assertEquals(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEquals(data["name"], "TestService2")
        self.assertEquals(data["notes"], "")
        self.assertEquals(data["prereqs"], ["sws-dev", "pws-dev",
                                            "made-up-dev"])
        self.assertEquals(data["hosts"], [{"name": "ts-app01",
                                           "role": "Application Server"},
                                          {"name": "ts-app02",
                                           "role": "Application Server"},
                                          {"name": "ts-app03",
                                           "role": "Application Server"},
                                          {"name": "ts-app04",
                                           "role": "Application Server"},
                                          {"name": "ts-db01",
                                           "role": "Database Server"}, ])
        # Add 1, remove 1...
        data = {
            "name": "TestService2",
            "prereqs": ["new-dev", "pws-dev", "made-up-dev"],
            "hosts": [
                {"name": "ts-app05", "role": "Application Server"},
                {"name": "ts-app02", "role": "Application Server"},
                {"name": "ts-app03", "role": "Application Server"},
                {"name": "ts-app04", "role": "Application Server"},
                {"name": "ts-db01", "role": "Database Server"},
            ]
        }

        response = self.client.post("/api/v1/service",
                                    json.dumps(data),
                                    content_type="application/json",
                                    )

        self.assertEquals(response.status_code, 201)

        response = self.client.get("/api/v1/service/TestService2")
        self.assertEquals(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEquals(data["name"], "TestService2")
        self.assertEquals(data["notes"], "")
        self.assertEquals(data["prereqs"], ["pws-dev",
                                            "made-up-dev", "new-dev"])
        self.assertEquals(data["hosts"], [{"name": "ts-app02",
                                           "role": "Application Server"},
                                          {"name": "ts-app03",
                                           "role": "Application Server"},
                                          {"name": "ts-app04",
                                           "role": "Application Server"},
                                          {"name": "ts-db01",
                                           "role": "Database Server"},
                                          {"name": "ts-app05",
                                           "role": "Application Server"}, ])

    def test_self_dependent(self):
        data = {
            "name": "TestService3",
            "notes": "This is a note",
            "prereqs": ["TestService3"],
        }

        response = self.client.post("/api/v1/service",
                                    json.dumps(data),
                                    content_type="application/json",
                                    )

        self.assertEquals(response.status_code, 201)

        response = self.client.get("/api/v1/service/TestService3")
        self.assertEquals(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEquals(data["name"], "TestService3")
        self.assertEquals(data["notes"], "This is a note")
        self.assertEquals(data["prereqs"], ["TestService3"]),

    def test_deployments(self):
        data = {
            "name": "TS4",
            "deployment_host": "dh1.example.com",
            "deployment_user": "duser1",
        }

        response = self.client.post("/api/v1/service",
                                    json.dumps(data),
                                    content_type="application/json",
                                    )

        self.assertEquals(response.status_code, 201)

        data = {
            "name": "TS4",
            "deployment_host": "dh2.example.com",
            "deployment_user": "duser2",
        }

        response = self.client.post("/api/v1/service",
                                    json.dumps(data),
                                    content_type="application/json",
                                    )

        response = self.client.get("/api/v1/service/TS4/deployments",
                                   content_type="application/json",
                                   )

        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEquals(data[0]["host"], "dh1.example.com")
        self.assertEquals(data[0]["user"], "duser1")
        self.assertEquals(data[1]["host"], "dh2.example.com")
        self.assertEquals(data[1]["user"], "duser2")

        self.assertNotEqual(data[0]["timestamp"], "")
