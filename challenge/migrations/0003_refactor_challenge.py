# Generated by Django 5.0.2 on 2024-02-14 15:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challenge", "0002_alter_useracceptchallenge_unique_together_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.DeleteModel("UserAcceptChallenge"),
        migrations.DeleteModel("Challenge"),
        migrations.CreateModel(
            name="Challenge",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("accepted", "Accepted"),
                            ("failed", "Failed"),
                            ("completed", "Completed"),
                        ],
                        default="accepted",
                        max_length=10,
                    ),
                ),
                ("start_time", models.DateTimeField(auto_now_add=True)),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accepted_users",
                        to="post.post",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accepted_challenges",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="challenge",
            constraint=models.UniqueConstraint(
                fields=("user", "post"), name="challenge_challenge_unique_user_post"
            ),
        ),
    ]
