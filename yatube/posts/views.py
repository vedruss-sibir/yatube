from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from posts.utils import paginator_out
from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


def index(request):
    posts = Post.objects.select_related("group").all()
    context = {"index": True}
    context.update(paginator_out(posts, request))
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        "group": group,
    }
    context.update(paginator_out(posts, request))
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(author=author, user=request.user).exists()
    )
    posts = Post.objects.filter(author=author)
    context = {"author": author, "following": following}
    context.update(paginator_out(posts, request))
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None, files=request.FILES or None)
    context = {
        "post": post,
        "form": form,
        "comments": comments,
        "post_id": post_id,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        user_name = request.user
        return redirect("posts:profile", user_name)
    return render(request, "posts/creat_post.html", {"form": form})
    form = PostForm()
    return render(request, "posts/creat_post.html", {"form": form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id=post_id)
    form = PostForm(
        request.POST or None, instance=post, files=request.FILES or None
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)
    context = {
        "form": form,
        "post_id": post_id,
        "is_edit": True,
    }
    return render(request, "posts/creat_post.html", context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    authors = user.follower.all().values("author")
    posts = Post.objects.filter(author__in=authors)
    context = {"follow": True}
    context.update(paginator_out(posts, request))
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    # если убираю проверку pytest не проходит
    follow = Follow.objects.filter(user=request.user, author=author)
    if request.user != author and not follow.exists():
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:profile", username=author)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author, user=user).delete()
    return redirect("posts:profile", username=author)
