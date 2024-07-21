from django.contrib import admin

from .models import Category, Comment, Location, Post


class PostInline(admin.TabularInline):
    model = Post
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'title',
        'description',
        'slug',
        'is_published',
        'created_at'
    )
    list_editable = (
        'description',
        'slug',
        'is_published',
    )
    list_display_links = ('title',)


class LocationAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'name',
        'is_published',
        'created_at'
    )
    list_editable = (
        'is_published',
    )
    list_display_links = ('name',)


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published',
        'created_at'
    )
    list_editable = (
        'text',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published',
    )
    list_display_links = ('title',)


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'post',
        'created_at',
        'author',
    )
    list_editable = (
        'text',
    )


admin.site.register(Category, CategoryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
