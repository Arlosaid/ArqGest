from django.core.management.base import BaseCommand
from apps.projects.models import ProjectTemplate, PhaseTemplate

class Command(BaseCommand):
    help = 'Creates default project templates and their phases.'

    def handle(self, *args, **options):
        self.stdout.write("Checking for existing project templates...")

        templates_data = [
            {
                "name": "Single-Family Residence",
                "description": "A standard template for single-family residential projects.",
                "phases": [
                    {"name": "Schematic Design", "order": 1},
                    {"name": "Design Development", "order": 2},
                    {"name": "Construction Documents", "order": 3},
                    {"name": "Bidding and Negotiation", "order": 4},
                    {"name": "Construction Administration", "order": 5},
                ],
            },
            {
                "name": "Commercial Building",
                "description": "A template for commercial building projects.",
                "phases": [
                    {"name": "Feasibility and Site Analysis", "order": 1},
                    {"name": "Schematic Design", "order": 2},
                    {"name": "Entitlements and Permits", "order": 3},
                    {"name": "Detailed Design", "order": 4},
                    {"name": "Construction", "order": 5},
                    {"name": "Post-Construction", "order": 6},
                ],
            },
        ]

        for template_data in templates_data:
            template_name = template_data["name"]
            if not ProjectTemplate.objects.filter(name=template_name).exists():
                self.stdout.write(self.style.SUCCESS(f"Creating template: {template_name}"))
                project_template = ProjectTemplate.objects.create(
                    name=template_name,
                    description=template_data["description"]
                )
                
                for phase_data in template_data["phases"]:
                    PhaseTemplate.objects.create(
                        project_template=project_template,
                        name=phase_data["name"],
                        order=phase_data["order"]
                    )
            else:
                self.stdout.write(self.style.WARNING(f"Template '{template_name}' already exists. Skipping."))

        self.stdout.write(self.style.SUCCESS("Default project templates are all set."))
