import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Comment, Post


# Test Models ---------------------------------------------------------------------------


def create_post(title="A Title", text="here is some text"):
    """
    Creates a post with the given `title` and `text` and an author with the username "test".
    The post is unpublished.
    """
    user = User.objects.create_user(username="test", password="secret")
    return Post.objects.create(author=user, title=title, text=text)


def create_comment(author="me", text="a comment"):
    """
    Creates a comment with the given `author` and `text`, that is unapproved.
    """
    post = create_post()
    return Comment.objects.create(post=post, author=author, text=text)


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

        cls.post3 = Post.objects.create(author=user, title="Post 3", text="post text goes here")
        cls.post3.publish()

        cls.post1 = Post.objects.create(author=user, title="Post 1", text="post text goes here")
        cls.post1.publish(date=timezone.now() - datetime.timedelta(days=1))

        cls.post2 = Post.objects.create(author=user, title="Post 2", text="post text goes here")
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
        self.assertRedirects(response, "/accounts/login/?next=/drafts/")

    def test_draft_posts_displayed(self):
        """
        Test that unpublished posts are visible to the logged-in user.
        """
        self.assertTrue(self.client.login(username="test", password="secret"))
        response = self.client.get(reverse("blog:post_draft_list"))
        self.assertEqual(response.status_code, 200)
        post_list = response.context["post_list"]
        self.assertNotIn(self.post1, post_list)
        self.assertIn(self.unpublished_post, post_list)
        self.assertQuerySetEqual([self.unpublished_post], post_list)

    def test_comments_displayed(self):
        """
        Test that the number of comments for a post is correctly shown in list view.
        """
        response = self.client.get(reverse("blog:post_list"))
        self.assertContains(response, "Comments: 0")
        comment = Comment.objects.create(post=self.post3, author="me", text="here is a comment")
        comment.approve()
        response = self.client.get(reverse("blog:post_list"))
        self.assertContains(response, "Comments: 1")
        # the other post on this page still has no comments
        self.assertContains(response, "Comments: 0")
        # is there a better way to do this that associates comments with the specific post?


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
        self.assertEqual(response.context["post"], self.published_post)

    def test_post_draft_detail_view(self):
        """
        Test that logged-out user can't access unpublished posts but logged-in user can.
        """
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 2}))
        self.assertEqual(response.status_code, 404)
        # test post that doesn't exist yet
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 3}))
        self.assertEqual(response.status_code, 404)
        # log in and try again
        self.assertTrue(self.client.login(username="test", password="secret"))
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 2}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["post"], self.unpublished_post)


class CommentViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username="test", password="secret")

        cls.post = Post.objects.create(author=user, title="A post", text="post text goes here")
        cls.post.publish()

    def test_add_comment_page_exists(self):
        response = self.client.get(reverse("blog:add_comment_to_post", kwargs={"pk": 1}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/add_comment_to_post.html")

    def test_no_comments_message(self):
        """
        Test that if no comments exist or no comments are approved correct message is shown.
        """
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 1}))
        self.assertContains(response, "No comments here yet :(")
        # create comment and check visibility
        comment_text = "this is my comment text"
        Comment.objects.create(post=self.post, author="me", text=comment_text)
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 1}))
        self.assertNotContains(response, comment_text)
        self.assertContains(response, "No comments here yet :(")

    def test_logged_in_user_comment_visibility(self):
        comment_text = "this is my comment text"
        comment = Comment.objects.create(post=self.post, author="me", text=comment_text)
        # log in and can see comment
        self.assertTrue(self.client.login(username="test", password="secret"))
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 1}))
        self.assertContains(response, comment_text)
        # can see approved comments too
        comment.approve()
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 1}))
        self.assertContains(response, comment_text)

    def test_logged_out_user_comment_visibility(self):
        comment_text = "this is my comment text"
        comment = Comment.objects.create(post=self.post, author="me", text=comment_text)
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 1}))
        # can't see comment
        self.assertNotContains(response, comment_text)
        # logged out user can see approved comments
        comment.approve()
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 1}))
        self.assertContains(response, comment_text)


class CommentApproveTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username="test", password="secret")

        cls.post = Post.objects.create(author=user, title="A post", text="post text goes here")
        cls.post.publish()
        cls.comment = Comment.objects.create(post=cls.post, author="me", text="A comment")

    def test_comment_approve(self):
        """
        Test that logged-in user can approve comments.
        """
        self.assertTrue(self.client.login(username="test", password="secret"))
        detail_response = self.client.get(reverse("blog:detail", kwargs={"pk": 1}))
        # is there a better way to do this?
        post_id = detail_response.context["post"].id
        comment = Comment.objects.get(post=post_id)
        response = self.client.post(reverse("blog:comment_approve", kwargs={"pk": comment.id}))
        self.assertRedirects(response, reverse("blog:detail", kwargs={"pk": post_id}))
        # check that approved comment is now visible when logged out
        self.client.logout()
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 1}))
        self.assertContains(response, comment.text)

    def test_comment_delete(self):
        """
        Test that logged-in user can delete comments.
        """
        self.assertTrue(self.client.login(username="test", password="secret"))
        detail_response = self.client.get(reverse("blog:detail", kwargs={"pk": 1}))
        # is there a better way to do this?
        post_id = detail_response.context["post"].id
        comment = Comment.objects.get(post=post_id)
        response = self.client.post(reverse("blog:comment_remove", kwargs={"pk": comment.id}))
        self.assertRedirects(response, reverse("blog:detail", kwargs={"pk": post_id}))
        # check that deleted comment is not visible
        response = self.client.get(reverse("blog:detail", kwargs={"pk": 1}))
        self.assertNotContains(response, comment.text)
        self.assertContains(response, "No comments here yet :(")


# Test Forms ---------------------------------------------------------------------------


class PostFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test", password="secret")

        cls.post = Post.objects.create(author=cls.user, title="A post", text="post text goes here")
        cls.post.publish()

    def test_only_logged_in_users_can_create_posts(self):
        """
        Test that logged-in user can create posts but logged-out user gets redirected to login page.
        """
        response = self.client.get(reverse("blog:post_new"))
        self.assertRedirects(response, "/accounts/login/?next=/post/new/")
        self.assertTrue(self.client.login(username="test", password="secret"))
        response = self.client.get(reverse("blog:post_new"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post_edit.html")

    def test_only_logged_in_users_can_edit_posts(self):
        """
        Test that logged-in user can edit posts but logged-out user gets redirected to login page.
        """
        post_id = self.post.id
        response = self.client.get(reverse("blog:post_edit", kwargs={"pk": post_id}))
        self.assertRedirects(response, f"/accounts/login/?next=/post/{post_id}/edit/")
        self.assertTrue(self.client.login(username="test", password="secret"))
        response = self.client.get(reverse("blog:post_edit", kwargs={"pk": post_id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/post_edit.html")

    def test_post_form_invalid_if_empty_fields(self):
        # I'm not sure where the default error message is defined
        # The message that appears in the browser is actually "Please fill in this field."!
        # But at least this tests whether there's an error or not
        self.assertTrue(self.client.login(username="test", password="secret"))
        response = self.client.post(reverse("blog:post_new"), {"title": "", "text": ""})
        self.assertFormError(
            response.context["form"], field="title", errors="This field is required."
        )
        self.assertFormError(
            response.context["form"], field="text", errors="This field is required."
        )

    def test_post_author_is_current_user(self):
        self.assertTrue(self.client.login(username="test", password="secret"))
        response = self.client.post(
            reverse("blog:post_new"),
            {"title": "A title", "text": "Some text"},
            follow=True,
        )  # follow redirect
        self.assertEqual(str(response.context["post"].author), "test")
        # edit the first post
        post_id = self.post.id
        response = self.client.post(
            reverse("blog:post_edit", kwargs={"pk": post_id}),
            {"title": "A title", "text": "Some text"},
            follow=True,
        )
        self.assertEqual(str(response.context["post"].author), "test")

    def test_only_logged_in_users_can_publish(self):
        """
        Test that logged-in user can publish posts but logged-out user gets redirected to login page.
        """
        new_post = Post.objects.create(author=self.user, title="title", text="post text goes here")
        response = self.client.get(reverse("blog:post_publish", kwargs={"pk": new_post.id}))
        self.assertRedirects(response, f"/accounts/login/?next=/post/{new_post.id}/publish/")
        # log in and try again
        self.assertTrue(self.client.login(username="test", password="secret"))
        response = self.client.get(reverse("blog:post_publish", kwargs={"pk": new_post.id}))
        self.assertRedirects(response, f"/{new_post.id}/")
        response = self.client.get(
            reverse("blog:post_publish", kwargs={"pk": new_post.id}), follow=True
        )
        self.assertEqual(response.context["post"].published_date.date(), timezone.now().date())


class CommentFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(username="test", password="secret")

        cls.post = Post.objects.create(author=user, title="A post", text="post text goes here")
        cls.post.publish()

    def test_redirects_to_post_on_success(self):
        """
        Test that adding a comment redirects correctly.
        """
        response = self.client.post(
            reverse("blog:add_comment_to_post", kwargs={"pk": 1}),
            {"author": "me", "text": "comment text goes here"},
        )
        self.assertRedirects(response, reverse("blog:detail", kwargs={"pk": 1}))

    def test_comment_form_invalid_if_empty_fields(self):
        # I'm not sure where the default error message is defined
        # The message that appears in the browser is actually "Please fill in this field."!
        # But at least this tests whether there's an error or not
        response = self.client.post(
            reverse("blog:add_comment_to_post", kwargs={"pk": 1}),
            {"author": "", "text": ""},
        )
        self.assertFormError(
            response.context["form"], field="author", errors="This field is required."
        )
        self.assertFormError(
            response.context["form"], field="text", errors="This field is required."
        )
