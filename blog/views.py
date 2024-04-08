from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CommentForm
from .models import Comment, Post

# Create your views here.


class PostListView(ListView):
    queryset = Post.objects.filter(published_date__lte=timezone.now()).order_by("-published_date")
    paginate_by = 2


class DraftPostListView(LoginRequiredMixin, ListView):
    queryset = Post.objects.filter(published_date__isnull=True).order_by("created_date")
    paginate_by = 2
    template_name = "blog/post_draft_list.html"


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/detail.html"

    def get_object(self):
        """
        Hides unpublished posts unless user is logged in.
        """
        # call default method to get object based on request, then check if post is published or user is logged in
        obj = super().get_object()
        if obj.published_date:
            return obj
        elif self.request.user.is_authenticated:
            return obj
        else:
            raise Http404("No post found matching the query")


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ["title", "text"]
    template_name = "blog/post_edit.html"

    def form_valid(self, form):
        # update post author to match current user
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ["title", "text"]
    template_name = "blog/post_edit.html"

    def form_valid(self, form):
        # update post author to match current user
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy("blog:post_list")


@login_required
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    return redirect("blog:detail", pk=pk)


def add_comment_to_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect("blog:detail", pk=post.id)
    else:
        form = CommentForm()
    return render(request, "blog/add_comment_to_post.html", {"form": form})


@login_required
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.approve()
    return redirect("blog:detail", pk=comment.post.id)


@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    return redirect("blog:detail", pk=comment.post.id)
