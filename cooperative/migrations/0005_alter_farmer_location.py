from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cooperative', '0003_create_default_categories'),  # Change this to match your last applied migration
    ]

    operations = [
        migrations.AlterField(
            model_name='farmer',
            name='location',
            field=models.CharField(choices=[('Kigali City', 'Kigali City'), ('Northern Province', 'Northern Province'), ('Southern Province', 'Southern Province'), ('Eastern Province', 'Eastern Province'), ('Western Province', 'Western Province')], default='', help_text='Province in Rwanda', max_length=100),
        ),
    ]

