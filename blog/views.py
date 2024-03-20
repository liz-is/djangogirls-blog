from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
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

from .forms import CommentForm, PostForm
from .models import Comment, Post

# Create your views here.

class PostListView(ListView):
    queryset = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
    paginate_by = 2


class DraftPostListView(LoginRequiredMixin, ListView):
    queryset = Post.objects.filter(published_date__isnull=True).order_by('created_date')
    paginate_by = 2
    template_name = "blog/post_draft_list.html"


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/detail.html"


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'text']
    template_name = "blog/post_edit.html"

    def form_valid(self, form):
        # update post author to match current user
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ['title', 'text']
    template_name = "blog/post_edit.html"

    def form_valid(self, form):
        # update post author to match current user
        form.instance.author = self.request.user
        return super().form_valid(form) 


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    success_url = reverse_lazy("blog:post_list")


@login_required
def post_publish(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post.publish()
    return redirect('blog:detail', pk=post_id)



def add_comment_to_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect('blog:detail', pk=post.id)
    else:
        form = CommentForm()
    return render(request, 'blog/add_comment_to_post.html', {'form': form})


@login_required
def comment_approve(request, post_id):
    comment = get_object_or_404(Comment, pk=post_id)
    comment.approve()
    return redirect('blog:detail', pk=comment.post.id)

@login_required
def comment_remove(request, post_id):
    comment = get_object_or_404(Comment, pk=post_id)
    comment.delete()
    return redirect('blog:detail', pk=comment.post.id)