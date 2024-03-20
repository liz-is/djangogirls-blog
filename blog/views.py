from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.generic import ListView, DetailView

from .models import Post, Comment
from .forms import PostForm, CommentForm

# Create your views here.

class PostListView(ListView):
    model = Post
    context_object_name = "published_post_list"
    queryset = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
    paginate_by = 2


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/detail.html"


@login_required
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            # post.published_date = timezone.now()
            post.save()
            return redirect('blog:detail', post_id=post.id) # kwargs here need to match what is used in urls.py - no magic
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            # post.published_date = timezone.now()
            post.save()
            return redirect('blog:detail', post_id=post.id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})


@login_required
def post_draft_list(request):
    posts = Post.objects.filter(published_date__isnull=True).order_by('created_date')
    return render(request, 'blog/post_draft_list.html', {'posts': posts})


@login_required
def post_publish(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post.publish()
    return redirect('blog:detail', post_id=post_id)


@login_required
def post_remove(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post.delete()
    return redirect('blog:post_list')


def add_comment_to_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect('blog:detail', post_id=post.id)
    else:
        form = CommentForm()
    return render(request, 'blog/add_comment_to_post.html', {'form': form})


@login_required
def comment_approve(request, post_id):
    comment = get_object_or_404(Comment, pk=post_id)
    comment.approve()
    return redirect('blog:detail', post_id=comment.post.id)

@login_required
def comment_remove(request, post_id):
    comment = get_object_or_404(Comment, pk=post_id)
    comment.delete()
    return redirect('blog:detail', post_id=comment.post.id)