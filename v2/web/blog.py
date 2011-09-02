#!/usr/bin/env python
# encoding: utf-8

import re
import os.path
import datetime
import tornado.web
import unicodedata

from mongoengine import *

from v2.lib import markdown
import v2.web

categories = [
    ('website-optimize', 'Website optimize'),
    ('user-experience-studios', 'User experience studios'),
    ('case-study', 'Case study'),
    ('user-manual', 'User manual'),
    ('free-resources', 'Free resources'),
    ('uncategorized', 'Uncategorized')
]

class Comment(EmbeddedDocument):
    """docstring for Comment"""
    name = StringField(max_length=120)
    email = StringField(max_length=255)
    content = StringField()
    published = DateTimeField()

class User(Document):
    """docstring for User"""
    name = StringField(max_length=120)
    email = StringField(max_length=255)

class Article(Document):
    slug = StringField(required=True)
    title = StringField(required=True)
    author = ReferenceField(User)
    text = StringField()
    html = StringField()
    published = DateTimeField()
    updated   = DateTimeField()
    tags = ListField(StringField(max_length=30))
    category = StringField()
    comments = ListField(EmbeddedDocumentField(Comment))
    
    title_link = StringField()
    parent_url = StringField()
    
    format = StringField(default="html")
    is_page = BooleanField(default=False)
    is_for_sidebar = BooleanField(default=False)
    hits    = IntField(default=0)
    hits_feed = IntField(default=0)

class BaseHandler(v2.web.BaseHandler):
    
    def render_string(self, template_name, **kwargs):
        args = dict(
            system_version='0.1(previeew)',
            categories = categories
        )
        
        args.update(kwargs)
        
        if not template_name.startswith("admin") \
            and not template_name.startswith("shared"):
            template_name = "blog/themes/%s/%s" % (self.application.settings['theme'], template_name)
        else:
            template_name = "blog/" + template_name
        
        return super(BaseHandler, self).render_string(template_name, **args)

class HomeHandler(BaseHandler):
    def get(self):
        articles = Article.objects().order_by('-published')
        if not articles:
            self.redirect("/admin/write")
            return
            
        self.render("home.html", articles=articles)

class ArticleHandler(BaseHandler):
    def get(self, slug):
        article = Article.objects(slug=slug).first()
        if not article: raise tornado.web.HTTPError(404)
        self.render("article.html", article=article)

class ArchiveHandler(BaseHandler):
    def get(self):
        articles = Article.objects().order_by('-published').limit(10)
        self.render("archive.html", articles=articles)

class CategoryHandler(BaseHandler):
    """docstring for ClassName"""
    
    def get(self, category):
        """docstring for get"""
        
        articles = Article.objects(category=category).order_by('-published').limit(10)
        self.render("category.html", articles=articles)

class FeedHandler(BaseHandler):
    def get(self):
        articles = Article.objects().limit(10)
        self.set_header("Content-Type", "application/atom+xml")
        self.render("shared/feed.xml", articles=articles)

class OverviewHandler(BaseHandler):
    """docstring for OverviewHandler"""
    
    def get(self):
        """docstring for get"""
        
        articles = Article.objects().order_by('-published')
        self.render("admin/overview.html", articles=articles, page_title="")
        
class RemoveHandler(BaseHandler):
    """docstring for RemoveHandler"""
    
    def get(self, id):
        """docstring for get"""
        
        article  = Article.objects(id=id).first()
        
        if article:
            article.delete()
            
        self.redirect("/admin")
        
class ComposeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, id=None):

        article = None
        page_mode = 'new'
        if id:
            article = Article.objects(id=id).first()
            
        if article:
            page_mode = 'edit'
            
        self.render("admin/write.html", 
                article=article, 
                page_mode=page_mode, 
                page_title="", 
                page=1,
                message=None
            )

    @tornado.web.authenticated
    def post(self, id=None):

        title = self.get_argument("title", '')
        text = self.get_argument("content", '')
        category = self.get_argument("category", 'uncategorized')
        parent_url = self.get_argument("parent_url", '')
        format = self.get_argument("format", 'html')
        is_for_sidebar = self.get_argument("is_for_sidebar", 'False') == 'True' and True or False
        is_page = self.get_argument("is_page", 'False') == 'True' and True or False
        
        if format == 'markdown':
            html = markdown.markdown(text)
        else:
            html = text
        
        article,slug = None, None
        if id:
            article = Article.objects(id=id).first()
            if not article: raise tornado.web.HTTPError(404)
            slug = article.slug
            
            message = "Changes has been saved"
        else:
            
            if title:
                slug = unicodedata.normalize("NFKD", title).encode(
                    "ascii", "ignore")
            
                slug = re.sub(r"[^\w]+", " ", slug)
                slug = "-".join(slug.lower().strip().split())
                
            if not slug: slug = "entry"
            
            while True:
                e = Article.objects(slug=slug).first()
                if not e: break
                slug += "-2"
            
            user = self.get_current_user()
            author = User.objects(email=user['email']).first()
            
            if not author:
                author = User(email=user['email'], name=user['name'])
                author.save()
                
            article = Article(slug=slug)
            article.author = author
            article.published = datetime.datetime.now()
            
            message = "New article has been created"

        article.parent_url = parent_url
        article.category = category
        article.title = title
        article.text  = text
        article.html  = html
        article.format = format
        article.is_page = is_page
        article.is_for_sidebar = is_for_sidebar
        article.updated = datetime.datetime.now()
        article.save()
        
        self.render("admin/write.html", 
                article=article, 
                page_mode='edit', 
                page_title="", 
                page=1,
                message=message
            )