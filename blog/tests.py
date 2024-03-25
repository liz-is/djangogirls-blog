from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

import datetime

from .models import Post

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


def create_post(title="A Title", text="here is some text"):
    """
    Creates a post with the given `title` and `text` and an author with the username "test".
    The post is unpublished.
    """
    user = User(username="test", password="")
    user.save()
    return Post.objects.create(author=user, title=title, text=text)


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


class PostIndexViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create 3 posts for pagination tests
        user = User.objects.create(username="test", password="")

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
