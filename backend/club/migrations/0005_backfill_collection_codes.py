from django.db import migrations


def backfill(apps, schema_editor):
    Collection = apps.get_model('club', 'Collection')
    counters = {}
    collections = Collection.objects.filter(status='published').order_by('published_at', 'created_at')
    for collection in collections:
        if collection.code or not collection.published_at:
            continue
        year = collection.published_at.year
        counters[year] = counters.get(year, 0) + 1
        collection.code = f'{year}-{counters[year]:03d}'
        collection.save(update_fields=['code'])


class Migration(migrations.Migration):
    dependencies = [('club', '0004_collection_code_collection_unique_collection_code')]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
