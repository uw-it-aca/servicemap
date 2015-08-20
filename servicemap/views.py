from django.shortcuts import render, render_to_response
from django.template import RequestContext
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
        login_systems = json_data.get("login_systems", [])
        log_services = json_data.get("log_services", [])
        hosts = json_data.get("hosts", [])

        obj, is_new = Service.objects.get_or_create(name=name)

        obj.notes = notes

        # Create as needed and then add prereq services
        prereq_services = _get_services_by_name(prereqs)
        obj.prereqs.clear()

        for req in prereq_services:
            obj.prereqs.add(req)

        # create and add login service providers
        login_services = _get_services_by_name(login_systems)
        obj.login_systems.clear()

        for req in login_services:
            obj.login_systems.add(req)

        # create and add log aggregation providers
        log_service_list = _get_services_by_name(log_services)
        obj.log_services.clear()

        for req in log_service_list:
            obj.log_services.add(req)

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


def _get_services_by_name(names):
    existing = Service.objects.filter(name__in=names)

    lookup = {}
    for service in existing:
        lookup[service.name] = service

    service_list = []
    for name in names:
        if name not in lookup:
            new_service = Service.objects.create(name=name)
            service_list.append(new_service)
        else:
            service_list.append(lookup[name])

    return service_list


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
        "service_name": service.name,
        "notes": service.notes,
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
                                    "timestamp": deployment.timestamp})

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

    return render_to_response("servicemap/service.html",
                              data,
                              context_instance=RequestContext(request))


def home(request):
    data = {"services": []}

    services = Service.objects.all()

    for service in sorted(services, key=lambda x: x.name):
        data["services"].append(service.name)

    return render_to_response("servicemap/home.html",
                              data,
                              context_instance=RequestContext(request))
