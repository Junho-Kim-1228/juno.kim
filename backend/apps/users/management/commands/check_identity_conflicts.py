from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError

from apps.users.identity import validate_display_name, validate_username
from apps.users.models import Profile, User


class Command(BaseCommand):
    help = "Read-only check for user and display names that conflict with the current identity policy."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit with an error when conflicts are found.",
        )

    def handle(self, *args, **options):
        conflicts = []
        usernames_by_casefold = defaultdict(list)

        for user in User.objects.only("id", "username").order_by("id"):
            usernames_by_casefold[user.username.casefold()].append(user)
            try:
                validate_username(user.username)
            except Exception as error:
                conflicts.append(f"user #{user.pk}: {user.username!r} ({error})")

        for duplicate_users in usernames_by_casefold.values():
            if len(duplicate_users) > 1:
                identifiers = ", ".join(f"#{user.pk} {user.username!r}" for user in duplicate_users)
                conflicts.append(f"case-insensitive duplicate usernames: {identifiers}")

        for profile in Profile.objects.select_related("user").only("id", "display_name", "user__username").order_by("id"):
            try:
                validate_display_name(profile.display_name)
            except Exception as error:
                conflicts.append(
                    f"profile #{profile.pk} for @{profile.user.username}: {profile.display_name!r} ({error})"
                )

        if not conflicts:
            self.stdout.write(self.style.SUCCESS("No identity-policy conflicts found."))
            return

        self.stdout.write(self.style.WARNING("Identity-policy conflicts found (no data was changed):"))
        for conflict in conflicts:
            self.stdout.write(f"- {conflict}")
        if options["strict"]:
            raise CommandError(f"{len(conflicts)} identity-policy conflict(s) found.")
