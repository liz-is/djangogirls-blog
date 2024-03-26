from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

import datetime

from .models import Post, Comment

# Create your tests here.

# test index/homepage view
# response if there are no posts?
# posts that are published are listed
# posts that are not published are not listed
# number of comments are correct?

# test that things that should only be shown when logged in are shown correctly

# test detail view of posts
# posts only shown if published
# comments only shown if approved (or logged in)
# test comment approval process?


# Test Models ---------------------------------------------------------------------------


def create_post(title="A Title", text="here is some text"):
    """
    Creates a post with the given `title` and `text` and an author with the username "test".
    The post is unpublished.
    """
    user = User.objects.create_user(username="test", password="secret")
    return Post.objects.create(author=user, title=title, text=text)


def create_comment(author = "me", text = "a comment"):
    post = create_post()
    return Comment.objects.create(post = post, author = author, text = text)


class PostModelTests(TestCase):
    """
    Test that publishing a post sets its `published_date` field to today's date.
    """
    def test_publish_post(self):
        blog_post = create_post()
        self.assertIsNone(blog_post.published_date)
        time_now = timezone.now()
        blog_post.publish(date=time_now)
        self.assertEqual(blog_post.published_date, time_now)

    def test_str(self):
        title = "This is my title"
        blog_post = create_post(title=title)
        self.assertEqual(str(blog_post), title)

    def test_get_absolute_url(self):
        blog_post = create_post()
        self.assertEqual(blog_post.get_absolute_url(), "/1/")


class CommentModelTests(TestCase):
   
    def test_str(self):
        text = "This is the comment text"
        comment = create_comment(text=text)
        self.assertEqual(str(comment), text)

    def test_comment_approval(self):
        comment = create_comment()
        self.assertFalse(comment.approved_comment)
        comment.approve()
        self.assertTrue(comment.approved_comment)


# Test Views ---------------------------------------------------------------------------

class PostListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create 3 posts for pagination tests
        user = User.objects.create_user(username="test", password="secret")

        cls.post3 = Post.objects.create(
            author=user, title="Post 3", text="post text goes here"
        )
        cls.post3.publish()

        cls.post1 = Post.objects.create(
            author=user, title="Post 1", text="post text goes here"
        )
        cls.post1.publish(date=timezone.now() - datetime.timedelta(days=1))

        cls.post2 = Post.objects.create(
            author=user, title="Post 2", text="post text goes here"
        )
        cls.post2.publish(date=timezone.now() - datetime.timedelta(hours=1))

        cls.unpublished_post = Post.objects.create(
            author=user, title="Unpublished post", text="should not appear"
        )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("blog:post_list"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("blog:post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post_list.html")

    def test_pagination_is_two(self):
        """
        Test that pagination is on and only two posts are shown on the first page.
        """
        response = self.client.get(reverse("blog:post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["post_list"]), 2)

    def test_lists_all_posts(self):
        """
        Test that one post is listed on the second page.
        """
        response = self.client.get(reverse("blog:post_list") + "?page=2")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(len(response.context["post_list"]), 1)

    def test_posts_displayed(self):
        """
        Test that the first page shows the two most recent posts.
        """
        response = self.client.get(reverse("blog:post_list"))
        post_list = response.context["post_list"]
        self.assertIn(self.post3, post_list)
        self.assertIn(self.post2, post_list)
        self.assertNotIn(self.unpublished_post, post_list)
        self.assertQuerySetEqual([self.post3, self.post2], post_list)

    def test_posts_displayed_page2(self):
        """
        Test that the second page shows the oldest post.
        """
        response = self.client.get(reverse("blog:post_list") + "?page=2")
        post_list = response.context["post_list"]
        self.assertIn(self.post1, post_list)
        self.assertNotIn(self.unpublished_post, post_list)
        self.assertQuerySetEqual([self.post1], post_list)

    def test_draft_posts__require_login(self):
        response = self.client.get(reverse("blog:post_draft_list"))
        self.assertRedirects(response, '/accounts/login/?next=/drafts/')

    def test_draft_posts_displayed(self):
        """
        Test that unpublished posts are visible to the logged-in user.
        """
        self.assertTrue(self.client.login(username = "test", password = "secret"))
        response = self.client.get(reverse("blog:post_draft_list"))
        self.assertEqual(response.status_code, 200)
        post_list = response.context["post_list"]
        self.assertNotIn(self.post1, post_list)
        self.assertIn(self.unpublished_post, post_list)
        self.assertQuerySetEqual([self.unpublished_post], post_list)


class PostDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create 3 posts for pagination tests
        user = User.objects.create_user(username="test", password="secret")

        cls.published_post = Post.objects.create(
            author=user, title="Post", text="post text goes here"
        )
        cls.published_post.publish(date=timezone.now() - datetime.timedelta(hours=1))

        cls.unpublished_post = Post.objects.create(
            author=user, title="Unpublished post", text="should not appear"
        )

    def test_post_detail_view(self):
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 1}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['post'], self.published_post)
        

    def test_post_draft_detail_view(self):
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 2}))
        self.assertEqual(response.status_code, 404)
        # test post that doesn't exist yet
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 3}))
        self.assertEqual(response.status_code, 404)
        # log in and try again
        self.assertTrue(self.client.login(username = "test", password = "secret"))
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 2}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['post'], self.unpublished_post)


class CommentViewTests(TestCase):
    def test_add_comment(self):
        post = create_post()
        response = self.client.get(reverse("blog:add_comment_to_post", kwargs={"pk": 1}))
        self.assertEqual(response.status_code, 200)
        
    