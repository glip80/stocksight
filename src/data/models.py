# models.py
from django.db import models, connection
from django.contrib import admin
from django.forms.models import model_to_dict

# try:
# except ImportError:

if connection.vendor == 'postgresql':
    from django_pg_bulk_update.manager import BulkUpdateManager
else:
    from django.db.models import Manager as BulkUpdateManager

class Symbol(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class SymbolAlias(models.Model):
    symbol = models.ForeignKey(Symbol, related_name='symbol_aliases', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class TwitterUser(models.Model):
    username = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    # user_id = models.BigIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

class ArticleAuthor(models.Model):
    objects = BulkUpdateManager()

    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    source = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # twitter_user = models.ManyToManyField(
    #     TwitterUser,
    #     db_column='username',
    #     through='AuthorSocial',
    #     through_fields=('author', 'username'),
    # )

    @classmethod
    def create_from_articles(cls, articles: list, source: str):
        author_records = [
                cls(name=article.author, url=article.author_url, source=source) for article in articles if article.author is not None
            ]
        
        if connection.vendor == 'postgresql':
            cls.objects.pg_bulk_update_or_create([
                model_to_dict(author, fields=['name', 'url', 'source']) for author in author_records
            ], key_fields='url', update=False)
        else:
            existing_records = cls.objects.filter(url__in=[author.url for author in author_records]).values_list('url', flat=True)

            cls.objects.bulk_create([
                author for author in author_records if author.url not in existing_records
            ])

        return author_records

    def __str__(self):
        return self.name

class AuthorSocial(models.Model):
    Medium = models.IntegerChoices('Medium', 'Twitter LinkedIn RSS Website')

    author = models.ForeignKey(ArticleAuthor, related_name='social_accounts', on_delete=models.CASCADE)
    media = models.CharField(blank=True, choices=Medium.choices, max_length=255)
    url = models.CharField(null=True, blank=True, max_length=255)
    username = models.CharField(null=True, blank=True, max_length=255)

    @property
    def twitter_user(self):
        if self.media in {self.Medium.Twitter}:
            return TwitterUser.objects.get(username=self.username)
        return None

    @property
    def account_name(self):
        "{}'s {}".format(self.author.name, self.media)

    def __str__(self):
        return self.account_name


admin.site.register(Symbol)
admin.site.register(SymbolAlias)
admin.site.register(TwitterUser)
# from django.db import models

# class Musician(models.Model):
#     first_name = models.CharField(max_length=50)
#     last_name = models.CharField(max_length=50)
#     instrument = models.CharField(max_length=100)
    # email = models.EmailField(max_length=255)


# class Album(models.Model):
#     artist = models.ForeignKey(Musician, on_delete=models.CASCADE)
#     name = models.CharField(max_length=100)
#     release_date = models.DateField()
#     num_stars = models.IntegerField()