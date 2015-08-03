from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=50, db_index=True, unique=True)


class Host(models.Model):
    name = models.CharField(max_length=200, db_index=True, unique=True)


class HostRole(models.Model):
    host = models.ForeignKey(Host)
    role = models.ForeignKey(Role)

    class Meta:
        unique_together = ('host', 'role',)


class Service(models.Model):
    name = models.CharField(max_length=200, db_index=True, unique=True)
    hostroles = models.ManyToManyField(HostRole)
    notes = models.TextField(null=True)
    prereqs = models.ManyToManyField("Service")

    def json_data(self):
        base = {
            "name": self.name,
            "notes": self.notes,
            "hosts": [],
            "prereqs": [],
        }

        for req in self.prereqs.all():
            base["prereqs"].append(req.name)

        for obj in self.hostroles.all():
            base["hosts"].append({
                "name": obj.host.name,
                "role": obj.role.name,
            })
        return base


class User(models.Model):
    login = models.CharField(max_length=100, db_index=True, unique=True)


class Deployment(models.Model):
    service = models.ForeignKey(Service, db_index=True)
    deployed_from = models.ForeignKey(Host, db_index=True)
    deployed_by = models.ForeignKey(User, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def json_data(self):
        return {
            "service": self.service.name,
            "host": self.deployed_from.name,
            "user": self.deployed_by.login,
            "timestamp": self.deployed_by.login,
        }
