# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import User

# automatically assign group once a user is created

@receiver(post_save, sender=User)
def assign_group(sender, instance, created, **kwargs):
    if created:
        group_map = {
            "trainer": "Trainer",
            "student": "Student",
            "telecaller": "TeleCaller",
            "counselor": "Counselor",
        }
        if instance.role in group_map:
            instance.groups.add(Group.objects.get(name=group_map[instance.role]))
            
            
# trainers & students profile created automatically once user is created

from trainer.models import Trainer
from student.models import Student

@receiver(post_save, sender=User)
def create_profile_for_role(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.role == "trainer":
        Trainer.objects.create(user=instance)

    elif instance.role == "student":
        Student.objects.create(user=instance)
            