from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_en', models.CharField(max_length=100, verbose_name='name (English)')),
                ('name_ru', models.CharField(blank=True, max_length=100, verbose_name='name (Russian)')),
                ('name_kk', models.CharField(blank=True, max_length=100, verbose_name='name (Kazakh)')),
                ('description', models.TextField(blank=True, verbose_name='description')),
            ],
            options={'verbose_name': 'category', 'verbose_name_plural': 'categories'},
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('slug', models.SlugField(unique=True, verbose_name='slug')),
            ],
            options={'verbose_name': 'tag', 'verbose_name_plural': 'tags'},
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='title')),
                ('body', models.TextField(verbose_name='body')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='slug')),
                ('status', models.CharField(
                    choices=[('draft', 'Draft'), ('published', 'Published')],
                    default='draft', max_length=10, verbose_name='status'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='posts', to=settings.AUTH_USER_MODEL, verbose_name='author'
                )),
                ('category', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='posts', to='blogs.category', verbose_name='category'
                )),
                ('tags', models.ManyToManyField(blank=True, related_name='posts', to='blogs.tag', verbose_name='tags')),
            ],
            options={'verbose_name': 'post', 'verbose_name_plural': 'posts', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(verbose_name='body')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comments', to=settings.AUTH_USER_MODEL, verbose_name='author'
                )),
                ('post', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comments', to='blogs.post', verbose_name='post'
                )),
            ],
            options={'verbose_name': 'comment', 'verbose_name_plural': 'comments', 'ordering': ['created_at']},
        ),
    ]
