from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'), 
    ]

    operations = [
        migrations.AlterField(
            model_name='technicalprocess',
            name='PDK_file',
            field=models.FileField(
                blank=True,
                default='',
                upload_to='uploads/PDK/2024/%Y/%m/%d/', 
                verbose_name='Файл КИП'
            ),
        ),
    ]
