from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_customuser_preffered_language_customuser_timezone_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customuser',
            old_name='preffered_language',
            new_name='preferred_language',
        ),
    ]
