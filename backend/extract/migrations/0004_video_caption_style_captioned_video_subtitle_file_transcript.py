from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("extract", "0003_video_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="video",
            name="caption_style",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="video",
            name="captioned_video",
            field=models.FileField(blank=True, null=True, upload_to=""),
        ),
        migrations.AddField(
            model_name="video",
            name="subtitle_file",
            field=models.FileField(blank=True, null=True, upload_to=""),
        ),
        migrations.AddField(
            model_name="video",
            name="transcript",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
