from django.test import TestCase
from oauth_provider.models import Consumer
import json
import hashlib
import time
import random
from servicemap.models import Service


class TestFrontendViews(TestCase):
    def test_service_view(self):
        consumer_name = "Test client - for frontend"
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

        for i in range(5):
            # Create 5 existing deployments, then a more recent deployment
            # with another user/host
            data = {
                "name": "TestServiceF",
                "prereqs": ["sws-dev", "pws-dev", "made-up-dev"],
                "deployment_host": "dha.example.com",
                "deployment_user": "dusera",
                "hosts": [
                    {"name": "ts-app01", "role": "Application Server"},
                    {"name": "ts-app02", "role": "Application Server"},
                    {"name": "ts-app03", "role": "Application Server"},
                    {"name": "ts-app04", "role": "Application Server"},
                    {"name": "ts-db01", "role": "Database Server"},
                ]
            }

            headers = {
                "HTTP_AUTHORIZATION": header,
            }
            response = self.client.post("/api/v1/service",
                                        json.dumps(data),
                                        content_type="application/json",
                                        **headers
                                        )

            self.assertEquals(response.status_code, 201)

        data = {
            "name": "TestServiceF",
            "notes": "haz notes",
            "prereqs": ["sws-dev", "pws-dev", "made-up-dev-fe"],
            "deployment_host": "dhb.example.com",
            "deployment_user": "duserb",
            "hosts": [
                {"name": "ts-app01", "role": "application"},
                {"name": "ts-app02", "role": "application"},
                {"name": "ts-app03", "role": "application"},
                {"name": "ts-app04", "role": "application"},
                {"name": "ts-db01", "role": "database"},
                {"name": "ts-db02", "role": "database-master"},
                {"name": "ts-db04", "role": "database-slave"},
                {"name": "ts-db03", "role": "database-slave"},
                {"name": "ts-rdis", "role": "RDIS Server"},
            ]
        }

        headers = {
            "HTTP_AUTHORIZATION": header,
        }
        response = self.client.post("/api/v1/service",
                                    json.dumps(data),
                                    content_type="application/json",
                                    **headers
                                    )

        self.assertEquals(response.status_code, 201)

        response = self.client.get("/service/TestServiceF")
        self.assertEquals(response.templates[0].name,
                          "servicemap/service.html")

        context = response.context
        self.assertEquals(context["service_name"], "TestServiceF")
        self.assertEquals(context["notes"], "haz notes")
        self.assertEquals(context["deployments"][4]["user"], "dusera")
        self.assertEquals(context["deployments"][4]["host"], "dha.example.com")
        self.assertEquals(context["deployments"][3]["user"], "dusera")
        self.assertEquals(context["deployments"][3]["host"], "dha.example.com")
        self.assertEquals(context["deployments"][2]["user"], "dusera")
        self.assertEquals(context["deployments"][2]["host"], "dha.example.com")
        self.assertEquals(context["deployments"][1]["user"], "dusera")
        self.assertEquals(context["deployments"][1]["host"], "dha.example.com")
        self.assertEquals(context["deployments"][0]["user"], "duserb")
        self.assertEquals(context["deployments"][0]["host"], "dhb.example.com")
        self.assertNotEquals(context["deployments"][0]["timestamp"], "")
        self.assertEquals(len(context["deployments"]), 5)

        self.assertEquals(context["prereqs"][0]["name"], "made-up-dev-fe")
        self.assertEquals(context["prereqs"][1]["name"], "pws-dev")
        self.assertEquals(context["prereqs"][2]["name"], "sws-dev")

        self.assertEquals(context["hosts"]["application"][0], "ts-app01")
        self.assertEquals(context["hosts"]["application"][1], "ts-app02")
        self.assertEquals(context["hosts"]["application"][2], "ts-app03")

        self.assertEquals(context["hosts"]["database"][0], "ts-db01")
        self.assertEquals(context["hosts"]["master_db"][0], "ts-db02")
        self.assertEquals(context["hosts"]["slave_db"][0], "ts-db03")
        self.assertEquals(context["hosts"]["slave_db"][1], "ts-db04")

        self.assertEquals(context["hosts"]["other"][0]["name"], "ts-rdis")
        self.assertEquals(context["hosts"]["other"][0]["role"], "RDIS Server")

        self.assertEquals(context["dependency_of"], [])

        # Check the reverse dependency mapping
        response = self.client.get("/service/made-up-dev-fe")
        context = response.context

        self.assertEquals(context["dependency_of"], ["TestServiceF"])

    def test_homepage_list(self):
        s1 = Service.objects.create(name="HP_Test1")
        s2 = Service.objects.create(name="HP_Test2")

        response = self.client.get("/")
        self.assertEquals(response.templates[0].name,
                          "servicemap/home.html")

        context = response.context
        has_s1 = False
        has_s2 = False

        for service in context["no_host_services"]:
            if service == "HP_Test1":
                has_s1 = True
            if service == "HP_Test2":
                has_s2 = True

        self.assertTrue(has_s1)
        self.assertTrue(has_s2)
