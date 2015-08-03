from django.shortcuts import render, render_to_response
from django.views.decorators.csrf import csrf_exempt
from oauth_provider.decorators import oauth_required
from django.http import HttpResponse
from servicemap.auth import authenticate_application
from servicemap.models import Service, Host, Role, HostRole, Deployment, User
import json


@csrf_exempt
@authenticate_application
def service_list(request):
    if request.method == "POST":
        json_data = json.loads(request.body)
        name = json_data["name"]
        notes = json_data.get("notes", "")
        prereqs = json_data.get("prereqs", [])
        hosts = json_data.get("hosts", [])

        obj, is_new = Service.objects.get_or_create(name=name)

        obj.notes = notes

        # Create as needed and then add prereq services
        existing_prereqs = Service.objects.filter(name__in=prereqs)
        obj.prereqs.clear()

        prereq_lookup = {}
        for existing in existing_prereqs:
            prereq_lookup[existing.name] = existing

        for req in prereqs:
            if req not in prereq_lookup:
                new_prereq = Service.objects.create(name=req)
                obj.prereqs.add(new_prereq)
            else:
                obj.prereqs.add(prereq_lookup[req])

        # make sure all hosts and roles exist that are used for this service
        hostnames = {}
        hostroles = {}
        for host in hosts:
            name = host["name"]
            role = host["role"]

            hostnames[name] = False
            hostroles[role] = False

        # Make the hosts
        existing_hosts = Host.objects.filter(name__in=hostnames.keys())
        for host in existing_hosts:
            hostnames[host.name] = host

        for host in hostnames.keys():
            if not hostnames[host]:
                new_host = Host.objects.create(name=host)
                hostnames[host] = new_host

        # make the roles...
        existing_roles = Role.objects.filter(name__in=hostroles.keys())
        for role in existing_roles:
            hostroles[role.name] = role

        for role in hostroles.keys():
            if not hostroles[role]:
                new_role = Role.objects.create(name=role)
                hostroles[role] = new_role

        obj.hostroles.clear()
        # Get the role/host/service map in place
        for host in hosts:
            host_obj = hostnames[host["name"]]
            role_obj = hostroles[host["role"]]

            host_role, is_new = HostRole.objects.get_or_create(host=host_obj,
                                                               role=role_obj)

            obj.hostroles.add(host_role)
        obj.save()

        # Create a deployment entry, if there is deployment data
        deployment_hostname = json_data.get("deployment_host", "")
        username = json_data.get("deployment_user", "")

        if username and deployment_hostname:
            host, is_new = Host.objects.get_or_create(name=deployment_hostname)
            user, is_new = User.objects.get_or_create(login=username)

            deployment = Deployment.objects.create(service=obj,
                                                   deployed_from=host,
                                                   deployed_by=user)

        response = HttpResponse("")
        response.status_code = 201
        return response


@csrf_exempt
@authenticate_application
def service(request, name):
    obj = Service.objects.get(name=name)

    return HttpResponse(json.dumps(obj.json_data()))


@csrf_exempt
@authenticate_application
def deployments(request, name):
    obj = Service.objects.get(name=name)

    deployments = Deployment.objects.filter(service=obj)

    data = []
    for deployment in deployments:
        data.append(deployment.json_data())

    return HttpResponse(json.dumps(data))


####
#
# Frontend views
#
###
def display_service(request, name):
    service = Service.objects.get(name=name)

    data = {
        "deployments": [],
        "prereqs": [],
        "hosts": {
            "application": [],
            "database": [],
            "master_db": [],
            "slave_db": [],
            "other": [],
        },
        "dependency_of": []
    }

    filtered = Deployment.objects.filter(service=service)
    deployments = filtered.order_by("-pk")[:5]
    for deployment in deployments:
        data["deployments"].append({"host": deployment.deployed_from.name,
                                    "user": deployment.deployed_by.login,
                                    "timestamp": str(deployment.timestamp)})

    for req in sorted(service.prereqs.all(), key=lambda x: x.name):
        data["prereqs"].append({"name": req.name, "notes": req.notes})

    for hr in sorted(service.hostroles.all(), key=lambda x: x.host.name):
        host = hr.host
        role = hr.role

        if role.name == "application":
            data["hosts"]["application"].append(host.name)
        elif role.name == "database":
            data["hosts"]["database"].append(host.name)
        elif role.name == "database-master":
            data["hosts"]["master_db"].append(host.name)
        elif role.name == "database-slave":
            data["hosts"]["slave_db"].append(host.name)
        else:
            data["hosts"]["other"].append({"name": host.name,
                                           "role": role.name})

    reverse_dependencies = Service.objects.filter(prereqs__name=name)
    for rdep in sorted(reverse_dependencies, key=lambda x: x.name):
        data["dependency_of"].append(rdep.name)

    return render_to_response("servicemap/service.html", data)
