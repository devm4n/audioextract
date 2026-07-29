from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("extract", "0004_video_caption_style_captioned_video_subtitle_file_transcript"),
    ]

    operations = [
        migrations.AddField(
            model_name="video",
            name="audio_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="video",
            name="captioned_video_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="video",
            name="subtitle_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="video",
            name="video_url",
            field=models.URLField(blank=True, null=True),
        ),
    ]
