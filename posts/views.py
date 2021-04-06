from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.shortcuts import render
from django.conf import settings

from .forms import CommentForm
from .models import Post, Group, Follow
from .forms import PostForm


User = get_user_model()


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.PAGE_SIZE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "index.html", {"page": page})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, settings.PAGE_SIZE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, "page": page})


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:index")
    context = {"form": form}
    return render(request, "create_or_update_post.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, settings.PAGE_SIZE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    return render(request, "profile.html",
                  {"author": author, "page": page, "following": following})


def post_view(request, username, post_id):
    profile = get_object_or_404(Post, author__username=username, id=post_id)
    comments = profile.comments.all()
    if request.user.is_authenticated:
        fil = Follow.objects.filter(user=request.user,
                                    author=profile.author).exists()
        following = request.user.is_authenticated and fil
    else:
        following = False
    form = CommentForm()
    context = {"author": profile.author, "post": profile, "comments": comments,
               "form": form, "following": following}
    return render(request, "post.html", context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect("posts:post", username, post.id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        edit_post = form.save(commit=False)
        edit_post.save()
        return redirect("posts:post", username, post.id)
    context = {"form": form, "item": post}
    return render(request, "create_or_update_post.html", context)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect("posts:post", username=post.author.username,
                    post_id=post.id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, settings.PAGE_SIZE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {"page": page,
                  "paginator": paginator})


@login_required
def profile_follow(request, username):
    follow_user = get_object_or_404(User, username=username)
    if request.user != follow_user:
        Follow.objects.get_or_create(user=request.user, author=follow_user)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    unfollow_user = get_object_or_404(User, username=username)
    get_object_or_404(Follow, user=request.user, author=unfollow_user).delete()
    return redirect("posts:profile", username=username)


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)
