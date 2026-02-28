from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.utils.timezone import now

User = get_user_model()

@receiver(post_save, sender=User, dispatch_uid="user_role_setup_signal")
def setup_user_role(sender, instance, created, **kwargs):
    role = getattr(instance, "role", None)

    if not role:
        return

    # Prevent duplicate profile creation
    if hasattr(instance, "_role_processed"):
        return

    instance._role_processed = True

    # -------------------------
    # GROUP ASSIGNMENT
    # -------------------------
    group_map = {
        "admin":"Admin",
        "trainer": "Trainer",
        "student": "Student",
        "tele_caller": "Tele_Caller",
        "counselor": "Counselor",
    }

    group, _ = Group.objects.get_or_create(name=group_map[role])
    instance.groups.add(group)

    # -------------------------
    # PROFILE CREATION
    # -------------------------
    if role == "trainer":
        from apps.bdm.models import Trainer
        Trainer.objects.get_or_create(
            user=instance
           
        )

    # elif role == "student":
    #     from apps.bdm.models import Student
    #     Student.objects.get_or_create(
    #         user=instance,
    #     )

    print("🔥 ROLE SETUP DONE FOR:", instance.username)
